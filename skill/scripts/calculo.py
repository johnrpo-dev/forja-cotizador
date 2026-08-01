"""Núcleo de cálculo comercial. Puro: no lee archivos, no imprime, no conoce rutas.

Recibe estructuras de datos ya cargadas y devuelve estructuras de datos.
Por eso los tests corren en milisegundos y el motor es auditable línea a línea.

Reglas de negocio: references/reglas_tributarias.md. Si este código y ese
documento divergen, es un bug.
"""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

IVA = Decimal("0.19")
RETEFUENTE_COMPRAS = Decimal("0.025")
UMBRAL_RETEFUENTE = Decimal("1000000")  # base antes de IVA estrictamente mayor

_PESO = Decimal("1")


def _pesos(valor: Decimal) -> Decimal:
    """Redondea a pesos completos, mitad hacia arriba (0,50 → 1)."""
    return valor.quantize(_PESO, rounding=ROUND_HALF_UP)


@dataclass
class LineaCotizacion:
    sku: str
    nombre: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal = Decimal("0")  # bruto: cantidad × precio de lista
    descuento_volumen_pct: Decimal = Decimal("0")
    subtotal_con_descuento: Decimal = Decimal("0")


@dataclass
class ResultadoCalculo:
    lineas: list[LineaCotizacion] = field(default_factory=list)
    subtotal: Decimal = Decimal("0")
    descuento_pct: Decimal = Decimal("0")
    descuento_valor: Decimal = Decimal("0")
    base_gravable: Decimal = Decimal("0")
    iva: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    retefuente_informativa: Decimal = Decimal("0")
    requiere_aprobacion: bool = False
    alertas: list[str] = field(default_factory=list)


class SkuNoEncontrado(Exception):
    """Un ítem solicitado no existe en el catálogo.

    Existe para que el sistema PREGUNTE en vez de inventar un precio.
    Nunca capturarla para sustituirla por un valor estimado.
    """


def _descuento_por_volumen(cantidad: int, politicas: dict) -> Decimal:
    for tramo in politicas["descuentos_volumen"]:
        if cantidad >= tramo["desde"] and (tramo["hasta"] is None or cantidad <= tramo["hasta"]):
            return tramo["descuento"]
    return Decimal("0")


def calcular(items, catalogo, cliente, politicas, descuento_manual_pct=None):
    """Calcula una cotización completa.

    Args:
        items: [{"sku": str, "cantidad": int}, ...]
        catalogo: {sku: {"nombre": str, "precio_unitario": Decimal, "stock": int}}
        cliente: {"nit": str, "agente_retenedor": bool, ...}
        politicas: {"descuentos_volumen": [...], "descuento_manual_maximo": Decimal, ...}
        descuento_manual_pct: Decimal | None — fracción global (0.15 = 15%)
            sobre la suma de líneas ya descontadas por volumen.

    Returns:
        ResultadoCalculo

    Raises:
        SkuNoEncontrado: si algún ítem no está en el catálogo.
        ValueError: si alguna cantidad no es un entero positivo.
    """
    resultado = ResultadoCalculo()

    for item in items:
        sku, cantidad = item["sku"], item["cantidad"]
        if not isinstance(cantidad, int) or cantidad < 1:
            raise ValueError(f"Cantidad inválida para {sku}: {cantidad!r}")
        if sku not in catalogo:
            raise SkuNoEncontrado(sku)
        producto = catalogo[sku]

        bruto = _pesos(cantidad * producto["precio_unitario"])
        pct = _descuento_por_volumen(cantidad, politicas)
        linea = LineaCotizacion(
            sku=sku,
            nombre=producto["nombre"],
            cantidad=cantidad,
            precio_unitario=producto["precio_unitario"],
            subtotal=bruto,
            descuento_volumen_pct=pct,
            subtotal_con_descuento=_pesos(bruto * (1 - pct)),
        )
        resultado.lineas.append(linea)

        stock = producto.get("stock")
        if stock is not None and cantidad > stock:
            resultado.alertas.append(
                f"{sku} sin stock suficiente: se piden {cantidad} y hay {stock}. "
                "Indicar tiempo de entrega desde la reposición."
            )

    resultado.subtotal = sum((l.subtotal_con_descuento for l in resultado.lineas), Decimal("0"))

    pct_manual = descuento_manual_pct if descuento_manual_pct is not None else Decimal("0")
    resultado.descuento_pct = pct_manual
    resultado.descuento_valor = _pesos(resultado.subtotal * pct_manual)
    if pct_manual > politicas["descuento_manual_maximo"]:
        resultado.requiere_aprobacion = True
        resultado.alertas.append(
            f"Descuento manual de {pct_manual:.0%} supera el tope de "
            f"{politicas['descuento_manual_maximo']:.0%}: requiere aprobación "
            "de gerencia comercial."
        )

    resultado.base_gravable = resultado.subtotal - resultado.descuento_valor
    resultado.iva = _pesos(resultado.base_gravable * IVA)
    resultado.total = resultado.base_gravable + resultado.iva

    if cliente.get("agente_retenedor") and resultado.base_gravable > UMBRAL_RETEFUENTE:
        resultado.retefuente_informativa = _pesos(resultado.base_gravable * RETEFUENTE_COMPRAS)

    return resultado
