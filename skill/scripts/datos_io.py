"""Borde de datos: carga catálogo, clientes y políticas desde skill/datos/.

Aislado del núcleo a propósito: si mañana los datos vienen de una API o de un
Excel, cambia este archivo y calculo.py no se entera.
"""

import csv
import unicodedata
from decimal import Decimal
from difflib import SequenceMatcher
from pathlib import Path

DATOS = Path(__file__).resolve().parent.parent / "datos"

# Políticas comerciales. Fuente de verdad: skill/datos/politicas_comerciales.md
# (secciones 1, 2 y 3). Si ese documento cambia, estas constantes deben
# actualizarse a mano — los tests de datos_io verifican los valores actuales.
DESCUENTOS_VOLUMEN = (
    {"desde": 1, "hasta": 19, "descuento": Decimal("0.00")},
    {"desde": 20, "hasta": 49, "descuento": Decimal("0.05")},
    {"desde": 50, "hasta": None, "descuento": Decimal("0.10")},
)
DESCUENTO_MANUAL_MAXIMO = Decimal("0.15")
VALIDEZ_DIAS = 15

# Días hábiles por ciudad — politicas_comerciales.md, sección 6.
TIEMPOS_ENTREGA_DIAS = {
    "bogota": 2, "medellin": 3, "cali": 3, "barranquilla": 4,
    "bucaramanga": 4, "cartagena": 4, "pereira": 3, "manizales": 3,
    "armenia": 3, "ibague": 3, "cucuta": 5, "villavicencio": 4,
    "santa marta": 5, "neiva": 4, "pasto": 6, "monteria": 5,
    "tunja": 3, "popayan": 5, "valledupar": 5, "sincelejo": 5,
}
ENTREGA_OTRAS_CIUDADES = "7 días hábiles (confirmar con logística)"


def cargar_catalogo(ruta: Path | None = None) -> dict:
    """Devuelve {sku: {"nombre", "categoria", "unidad", "precio_unitario", "stock"}}.

    precio_unitario es Decimal (nunca float: es dinero) y stock es int.
    """
    ruta = ruta or DATOS / "catalogo.csv"
    catalogo = {}
    with open(ruta, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            catalogo[fila["sku"]] = {
                "nombre": fila["nombre"],
                "categoria": fila["categoria"],
                "unidad": fila["unidad"],
                "precio_unitario": Decimal(fila["precio_unitario_cop"]),
                "stock": int(fila["stock"]),
            }
    return catalogo


def cargar_clientes(ruta: Path | None = None) -> dict:
    """Devuelve {nit: {...}} con agente_retenedor convertido a bool.

    Cada registro incluye también el nit, para que un cliente sacado del
    diccionario (p. ej. por buscar_cliente) siga identificable.
    """
    ruta = ruta or DATOS / "clientes.csv"
    clientes = {}
    with open(ruta, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            clientes[fila["nit"]] = {
                "nit": fila["nit"],
                "razon_social": fila["razon_social"],
                "contacto": fila["contacto"],
                "ciudad": fila["ciudad"],
                "agente_retenedor": fila["agente_retenedor"].strip().lower() == "si",
                "condicion_pago": fila["condicion_pago"],
                "notas": fila["notas"],
            }
    return clientes


def _normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar 'Bahía' con 'bahia'."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return " ".join(sin_tildes.lower().split())


def buscar_cliente(texto: str, clientes: dict | None = None) -> list[dict]:
    """Busca clientes por razón social aproximada.

    El vendedor escribe 'hotel bahia serena', no '901092837-5': la búsqueda
    ignora tildes y mayúsculas, acepta coincidencias parciales y devuelve los
    candidatos ordenados del más al menos parecido. Lista vacía si nada
    supera el umbral — en ese caso hay que preguntar, no adivinar.
    """
    clientes = clientes if clientes is not None else cargar_clientes()
    consulta = _normalizar(texto)
    if not consulta:
        return []

    candidatos = []
    for cliente in clientes.values():
        razon = _normalizar(cliente["razon_social"])
        if consulta in razon:
            puntaje = 1.0
        else:
            tokens = consulta.split()
            contenidos = sum(1 for t in tokens if t in razon)
            puntaje = max(
                contenidos / len(tokens) * 0.9,
                SequenceMatcher(None, consulta, razon).ratio(),
            )
        if puntaje >= 0.6:
            candidatos.append((puntaje, cliente))

    candidatos.sort(key=lambda par: par[0], reverse=True)
    return [cliente for _, cliente in candidatos]


def tiempo_entrega(ciudad: str) -> str:
    """Tiempo de entrega según la tabla de politicas_comerciales.md §6.

    Ignora tildes y mayúsculas; ciudad desconocida cae en 'otras ciudades'.
    """
    dias = TIEMPOS_ENTREGA_DIAS.get(_normalizar(ciudad))
    if dias is None:
        return ENTREGA_OTRAS_CIUDADES
    return f"{dias} días hábiles"


def cargar_politicas(ruta: Path | None = None) -> dict:
    """Devuelve las políticas comerciales con los porcentajes como Decimal.

    Los valores salen de las constantes del módulo, que reflejan
    skill/datos/politicas_comerciales.md (la fuente humana de verdad).
    El parámetro ruta se acepta por simetría con las otras cargas y se
    ignora: las políticas no se parsean del markdown.
    """
    return {
        "descuentos_volumen": [dict(tramo) for tramo in DESCUENTOS_VOLUMEN],
        "descuento_manual_maximo": DESCUENTO_MANUAL_MAXIMO,
        "validez_dias": VALIDEZ_DIAS,
    }
