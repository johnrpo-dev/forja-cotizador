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


def _resolver_cliente(referencia: str, clientes: dict):
    """NIT exacto o razón social aproximada. Devuelve (cliente, candidatos)."""
    referencia = referencia.strip()
    if referencia in clientes:
        return clientes[referencia], []
    candidatos = datos_io.buscar_cliente(referencia, clientes)
    if len(candidatos) == 1:
        return candidatos[0], []
    return None, candidatos


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
    if not ciudad and peticion.get("cliente"):
        cliente, _ = _resolver_cliente(str(peticion["cliente"]), datos_io.cargar_clientes())
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

    cliente, candidatos = _resolver_cliente(str(peticion["cliente"]), clientes)
    if cliente is None:
        if candidatos:
            return _error(
                "cliente_ambiguo",
                "Varios clientes coinciden: preguntar cuál es antes de cotizar.",
                candidatos=[{"nit": c["nit"], "razon_social": c["razon_social"]} for c in candidatos],
            )
        return _error("cliente_no_encontrado",
                      f"Ningún cliente coincide con {peticion['cliente']!r}: preguntar, no adivinar.")

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

    fecha = peticion.get("fecha") or dt.date.today().isoformat()
    salida = {
        "estado": "ok",
        "numero": None,
        "cliente": {"nit": cliente["nit"], "razon_social": cliente["razon_social"]},
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
        "alertas": resultado.alertas,
        "documento": None,
    }

    if solo_calculo:
        _emitir(salida)
        return 0

    numero = historial.siguiente_numero(salidas / "historial.csv", int(fecha[:4]))
    # Las políticas exigen indicar en la cotización las novedades de stock y
    # aprobación: las alertas van también al documento, no solo al JSON.
    observaciones = " ".join(
        parte for parte in [peticion.get("observaciones", "").strip(), *resultado.alertas] if parte
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
