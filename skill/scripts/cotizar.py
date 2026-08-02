#!/usr/bin/env python3
"""Punto de entrada ÚNICO de la skill. Delgado: solo orquesta.

Dos modos de operación:

    cotizacion (por defecto)  precios y totales -> documento numerado
    ficha                     especificaciones de producto -> ficha técnica

Uso:
    python cotizar.py --entrada peticion.json --salidas ../salidas
    python cotizar.py --modo ficha --entrada peticion.json --salidas ../salidas
    echo '{...}' | python cotizar.py --salidas ./salidas

Petición de cotización (JSON):
    {
      "cliente": "nit o razón social aproximada",
      "items": [{"sku": "SIL-006", "cantidad": 30}, ...],
      "descuento_manual_pct": "0.10",          // opcional, fracción
      "alcance": "...", "observaciones": "...",// opcionales
      "asesor": "...", "fecha": "2026-07-30"   // opcionales
    }

Cliente nuevo (todavía no está en clientes.csv): "cliente" va como objeto en
vez de texto, y no se da de alta en el CSV — vale solo para esta cotización.

    "cliente": {
      "nit": "901999888-1", "razon_social": "...",
      "contacto": "...", "ciudad": "Bogotá",
      "agente_retenedor": false,               // OBLIGATORIO declararlo
      "notas": "..."                           // opcional
    }

La condición de pago se fuerza a contado (políticas §5, primera compra) y
agente_retenedor no tiene valor por defecto: sin declarar, el script lo
reclama en vez de suponer que el cliente no retiene.

Petición de ficha técnica (JSON):
    {
      "modo": "ficha",                         // o pasar --modo ficha
      "skus": ["ARC-007", "SIL-008"],          // uno o varios; "sku" también sirve
      "ciudad": "Medellín",                    // opcional, para el tiempo de entrega
      "cliente": "...",                        // opcional, aporta la ciudad
      "observaciones": "...", "asesor": "...", "fecha": "..."  // opcionales
    }

La ficha NO consume consecutivo ni escribe en el historial: es informativa y
se identifica por SKU. Solo la cotización mueve el estado del negocio.

Salida: JSON por stdout con totales, alertas y ruta del documento.
Errores de negocio (SKU o cliente no resueltos) también salen como JSON,
con estado "error" y código de salida 1: el modelo debe PREGUNTAR con esa
información, nunca inventar.

Aritmética: calculo.py. Renderizado: documento.py. Estado: historial.py.
"""

import argparse
import datetime as dt
import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import calculo
import datos_io
import documento
import historial


def _emitir(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _error(tipo: str, mensaje: str, **extra) -> int:
    _emitir({"estado": "error", "tipo": tipo, "mensaje": mensaje, **extra})
    return 1


def _enumerar(terminos: list[str]) -> str:
    """['a', 'b', 'c'] -> 'a, b y c'."""
    if len(terminos) <= 1:
        return "".join(terminos)
    return f"{', '.join(terminos[:-1])} y {terminos[-1]}"


# Datos mínimos para cotizarle a un cliente que aún no está en clientes.csv.
CAMPOS_CLIENTE_NUEVO = ("nit", "razon_social", "contacto", "ciudad")


def _resolver_cliente(referencia: str, clientes: dict):
    """NIT exacto o razón social aproximada. Devuelve (cliente, candidatos).

    Identifica solo con un parecido fuerte y único (datos_io.UMBRAL_CERTEZA) o
    con el NIT exacto. Un puntaje en la banda intermedia devuelve
    (None, candidatos) para que el flujo pregunte: quedarse con el mejor de
    varios parecidos tibios es cómo se termina facturando a otra empresa.
    """
    referencia = referencia.strip()
    if referencia in clientes:
        return clientes[referencia], []
    candidatos = datos_io.buscar_cliente(referencia, clientes)
    ciertos = [c for puntaje, c in candidatos if puntaje >= datos_io.UMBRAL_CERTEZA]
    if len(ciertos) == 1:
        return ciertos[0], []
    return None, candidatos


def _leer_retenedor(valor):
    """True/False si la petición lo declara inequívocamente; None si no.

    Cuidado con bool("no"), que es True: un 'no' leído como sí le inventaría
    una retención al cliente. Todo lo que no sea un sí o un no claro es un
    dato ausente, y un dato ausente se pregunta.
    """
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        texto = valor.strip().lower()
        if texto in ("si", "sí", "true", "1"):
            return True
        if texto in ("no", "false", "0"):
            return False
    return None


def _cliente_nuevo(datos: dict, clientes: dict):
    """Cliente declarado en la propia petición. Devuelve (cliente, fallo).

    'fallo' son los kwargs de _error() cuando la declaración no alcanza.

    NO escribe en clientes.csv: el alta formal la hace cartera, y una skill
    que edita su propia fuente de datos deja de ser auditable. El cliente
    vale para esta cotización y nada más.

    Dos reglas que no se negocian:

      - condición de pago de CONTADO, traiga lo que traiga la petición:
        políticas §5, primera compra de cliente nuevo;
      - agente_retenedor tiene que venir declarado. Suponerlo en falso es
        inventar una condición tributaria — justo lo que la skill prohíbe.
    """
    faltantes = [c for c in CAMPOS_CLIENTE_NUEVO if not str(datos.get(c, "")).strip()]
    if faltantes:
        return None, {
            "tipo": "cliente_nuevo_incompleto",
            "mensaje": f"Faltan datos del cliente nuevo: {_enumerar(faltantes)}. "
                       "Pedírselos al vendedor antes de cotizar.",
            "campos_faltantes": faltantes,
        }

    nit = str(datos["nit"]).strip()
    if nit in clientes:
        registrado = clientes[nit]
        return None, {
            "tipo": "cliente_ya_registrado",
            "mensaje": f"El NIT {nit} ya está en clientes.csv como "
                       f"{registrado['razon_social']}: no es un cliente nuevo. "
                       "Cotizar con el registro existente (que trae su condición de "
                       "pago y sus notas) o confirmar cuál de los dos es el correcto.",
            "cliente_registrado": {"nit": nit, "razon_social": registrado["razon_social"],
                                   "ciudad": registrado["ciudad"],
                                   "condicion_pago": registrado["condicion_pago"]},
        }

    retenedor = _leer_retenedor(datos.get("agente_retenedor"))
    if retenedor is None:
        return None, {
            "tipo": "retencion_no_declarada",
            "mensaje": "Falta declarar si el cliente nuevo es agente retenedor "
                       "(agente_retenedor: true/false). PREGUNTAR: suponer que no "
                       "retiene inventa una condición tributaria del cliente.",
        }

    return {
        "nit": nit,
        "razon_social": str(datos["razon_social"]).strip(),
        "contacto": str(datos["contacto"]).strip(),
        "ciudad": str(datos["ciudad"]).strip(),
        "agente_retenedor": retenedor,
        "condicion_pago": "contado",  # políticas §5: primera compra
        "notas": str(datos.get("notas", "")).strip(),
    }, None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Genera una cotización comercial o una ficha técnica de producto.")
    parser.add_argument("--entrada", help="Ruta a JSON de petición. Si se omite, lee stdin.")
    parser.add_argument("--salidas", default="salidas", help="Carpeta de documentos e historial.")
    parser.add_argument("--modo", choices=("cotizacion", "ficha"),
                        help="Tipo de documento. Por defecto: cotizacion (o 'modo' de la petición).")
    parser.add_argument("--solo-calculo", action="store_true",
                        help="Calcula y devuelve JSON sin generar documento ni consumir consecutivo.")
    args = parser.parse_args(argv)

    try:
        crudo = Path(args.entrada).read_text(encoding="utf-8") if args.entrada else sys.stdin.read()
        peticion = json.loads(crudo)
    except (OSError, json.JSONDecodeError) as exc:
        return _error("peticion_invalida", f"No se pudo leer la petición: {exc}")

    modo = args.modo or peticion.get("modo") or "cotizacion"
    if modo not in ("cotizacion", "ficha"):
        return _error("peticion_invalida",
                      f"Modo {modo!r} desconocido: usar 'cotizacion' o 'ficha'.")
    if modo == "ficha":
        if args.solo_calculo:
            return _error("peticion_invalida",
                          "--solo-calculo no aplica al modo ficha: la ficha nunca "
                          "consume consecutivo ni modifica el historial.")
        return _flujo_ficha(peticion, Path(args.salidas))
    return _flujo_cotizacion(peticion, Path(args.salidas), args.solo_calculo)


def _flujo_ficha(peticion: dict, salidas: Path) -> int:
    """Una ficha técnica por SKU. No toca el historial ni el consecutivo."""
    skus = peticion.get("skus") or ([peticion["sku"]] if peticion.get("sku") else [])
    if not skus:
        return _error("peticion_invalida", "La petición de ficha necesita 'skus' (o 'sku').")

    catalogo = datos_io.cargar_catalogo()
    politicas = datos_io.cargar_politicas()

    desconocidos = [s for s in skus if s not in catalogo]
    if desconocidos:
        return _error("sku_no_encontrado",
                      f"Estos códigos no están en el catálogo: {', '.join(desconocidos)}. "
                      "Preguntar por el producto, NUNCA inventar especificaciones.",
                      sku=desconocidos[0], skus=desconocidos)

    # La ciudad solo afecta el tiempo de entrega. Sin destino la ficha no lo
    # supone: enuncia la sede y remite a logística.
    ciudad = peticion.get("ciudad")
    referencia = peticion.get("cliente")
    if not ciudad and referencia:
        # La ficha no exige cliente registrado. Si viene declarado como objeto
        # (cliente nuevo), su ciudad sirve igual; si es una referencia que no
        # se resuelve con certeza, se queda sin ciudad y remite a logística
        # antes que heredar el destino de un cliente parecido.
        if isinstance(referencia, dict):
            ciudad = str(referencia.get("ciudad", "")).strip()
        else:
            cliente, _ = _resolver_cliente(str(referencia), datos_io.cargar_clientes())
            if cliente:
                ciudad = cliente["ciudad"]
    if ciudad:
        entrega = f"{datos_io.tiempo_entrega(ciudad)} ({ciudad})"
    else:
        entrega = (f"Según ciudad de destino — {datos_io.tiempo_entrega('Bogotá')} "
                   "en Bogotá D.C.; otras ciudades, confirmar con logística")

    fecha = peticion.get("fecha") or dt.date.today().isoformat()
    textos = {
        "fecha": fecha,
        "tiempo_entrega": entrega,
        "observaciones": peticion.get("observaciones", "").strip() or "Ninguna.",
        "asesor": peticion.get("asesor", "Equipo comercial"),
        "validez_dias": politicas["validez_dias"],
    }

    fichas, alertas = [], []
    for sku in skus:
        producto = catalogo[sku]
        especificaciones = datos_io.especificaciones_de(producto["nombre"])
        # Un campo vacío en la ficha se leería como descuido. Dejar dicho que el
        # catálogo no lo registra evita que alguien lo "complete" de memoria.
        ausentes = datos_io.campos_sin_registro(especificaciones)
        nota = (
            f"El catálogo no registra {_enumerar(ausentes)} para este producto. "
            "No se incluyen datos estimados: confirmar con el proveedor antes de "
            "comprometerlos con el cliente."
        ) if ausentes else "Especificaciones tomadas del catálogo vigente."
        ruta = documento.generar_ficha_docx(
            sku, producto, especificaciones,
            dict(textos, nota_especificaciones=nota), salidas,
        )
        fichas.append({
            "sku": sku,
            "nombre": producto["nombre"],
            "categoria": producto["categoria"],
            "unidad": producto["unidad"],
            "precio_lista": str(producto["precio_unitario"]),
            "stock": producto["stock"],
            "especificaciones": especificaciones,
            "documento": str(documento.a_pdf(ruta)),
        })
        if producto["stock"] == 0:
            alertas.append(f"{sku}: sin existencias, sujeto a reposición.")
        if ausentes:
            alertas.append(
                f"{sku}: el catálogo no registra {_enumerar(ausentes)}. La ficha lo "
                "declara como no registrado — NO estimar esos datos.")

    _emitir({
        "estado": "ok",
        "modo": "ficha",
        "consecutivo_consumido": False,
        "fichas": fichas,
        "alertas": alertas,
    })
    return 0


def _flujo_cotizacion(peticion: dict, salidas: Path, solo_calculo: bool) -> int:
    items = peticion.get("items") or []
    if not items or not peticion.get("cliente"):
        return _error("peticion_invalida", "La petición necesita 'cliente' e 'items'.")

    catalogo = datos_io.cargar_catalogo()
    clientes = datos_io.cargar_clientes()
    politicas = datos_io.cargar_politicas()

    # Un cliente puede llegar como referencia (texto a resolver contra el CSV) o
    # como objeto: eso último es un cliente nuevo que el vendedor acaba de dictar.
    referencia = peticion["cliente"]
    es_nuevo = isinstance(referencia, dict)
    if es_nuevo:
        cliente, fallo = _cliente_nuevo(referencia, clientes)
        if fallo:
            return _error(**fallo)
    else:
        cliente, candidatos = _resolver_cliente(str(referencia), clientes)
        if cliente is None:
            if candidatos:
                return _error(
                    "cliente_ambiguo",
                    f"Ningún cliente coincide con certeza con {referencia!r}, pero estos "
                    "se le parecen: preguntar cuál es. Si ninguno lo es, declararlo como "
                    "cliente nuevo enviando 'cliente' como objeto.",
                    candidatos=[{"nit": c["nit"], "razon_social": c["razon_social"],
                                 "puntaje": round(puntaje, 2)}
                                for puntaje, c in candidatos],
                )
            return _error(
                "cliente_no_encontrado",
                f"Ningún cliente coincide con {referencia!r}: preguntar, no adivinar. "
                "Si es cliente nuevo, enviar 'cliente' como objeto con nit, "
                "razon_social, contacto, ciudad y agente_retenedor.")

    descuento = peticion.get("descuento_manual_pct")
    try:
        descuento = Decimal(str(descuento)) if descuento is not None else None
        resultado = calculo.calcular(items, catalogo, cliente, politicas,
                                     descuento_manual_pct=descuento)
    except calculo.SkuNoEncontrado as exc:
        return _error("sku_no_encontrado",
                      f"El ítem {exc} no está en el catálogo: preguntar por el producto, "
                      "NUNCA estimar un precio.", sku=str(exc))
    except (ValueError, ArithmeticError) as exc:
        return _error("peticion_invalida", str(exc))

    alertas = list(resultado.alertas)
    if es_nuevo:
        alertas.append(
            "Cliente nuevo, no registrado en clientes.csv: se cotiza de contado "
            "(políticas §5, primera compra) y no queda dado de alta. Tramitar el "
            "registro con cartera antes de facturar."
        )

    fecha = peticion.get("fecha") or dt.date.today().isoformat()
    salida = {
        "estado": "ok",
        "numero": None,
        "cliente": {"nit": cliente["nit"], "razon_social": cliente["razon_social"],
                    "nuevo": es_nuevo},
        "totales": {
            "subtotal": str(resultado.subtotal),
            "descuento_manual_pct": str(resultado.descuento_pct),
            "descuento_manual": str(resultado.descuento_valor),
            "base_gravable": str(resultado.base_gravable),
            "iva": str(resultado.iva),
            "total": str(resultado.total),
            "retefuente_informativa": str(resultado.retefuente_informativa),
        },
        "lineas": [
            {"sku": l.sku, "cantidad": l.cantidad,
             "descuento_volumen_pct": str(l.descuento_volumen_pct),
             "subtotal_con_descuento": str(l.subtotal_con_descuento)}
            for l in resultado.lineas
        ],
        "requiere_aprobacion": resultado.requiere_aprobacion,
        "alertas": alertas,
        "documento": None,
    }

    if solo_calculo:
        _emitir(salida)
        return 0

    numero = historial.siguiente_numero(salidas / "historial.csv", int(fecha[:4]))
    # Las políticas exigen indicar en la cotización las novedades de stock y
    # aprobación: las alertas van también al documento, no solo al JSON.
    observaciones = " ".join(
        parte for parte in [peticion.get("observaciones", "").strip(), *alertas] if parte
    ) or "Ninguna."
    textos = {
        "fecha": fecha,
        "alcance": peticion.get("alcance",
                                "Suministro de mobiliario y dotación según el detalle."),
        "tiempo_entrega": datos_io.tiempo_entrega(cliente["ciudad"]),
        "observaciones": observaciones,
        "asesor": peticion.get("asesor", "Equipo comercial"),
        "validez_dias": politicas["validez_dias"],
    }
    ruta_docx = documento.generar_docx(resultado, cliente, numero, textos, salidas)
    ruta_final = documento.a_pdf(ruta_docx)

    historial.registrar(salidas / "historial.csv", {
        "numero": numero,
        "fecha": fecha,
        "cliente_nit": cliente["nit"],
        "cliente_nombre": cliente["razon_social"],
        "subtotal": str(resultado.subtotal),
        "descuento": str(resultado.descuento_valor),
        "iva": str(resultado.iva),
        "total": str(resultado.total),
        "estado": "borrador_requiere_aprobacion" if resultado.requiere_aprobacion else "emitida",
    })

    salida["numero"] = numero
    salida["documento"] = str(ruta_final)
    _emitir(salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
