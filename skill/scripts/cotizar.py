#!/usr/bin/env python3
"""Punto de entrada ÚNICO de la skill. Delgado: solo orquesta.

Uso:
    python cotizar.py --entrada peticion.json --salidas ../salidas
    echo '{...}' | python cotizar.py --salidas ./salidas

Petición (JSON):
    {
      "cliente": "nit o razón social aproximada",
      "items": [{"sku": "SIL-006", "cantidad": 30}, ...],
      "descuento_manual_pct": "0.10",          // opcional, fracción
      "alcance": "...", "observaciones": "...",// opcionales
      "asesor": "...", "fecha": "2026-07-30"   // opcionales
    }

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
    parser = argparse.ArgumentParser(description="Genera una cotización comercial.")
    parser.add_argument("--entrada", help="Ruta a JSON de petición. Si se omite, lee stdin.")
    parser.add_argument("--salidas", default="salidas", help="Carpeta de documentos e historial.")
    parser.add_argument("--solo-calculo", action="store_true",
                        help="Calcula y devuelve JSON sin generar documento ni consumir consecutivo.")
    args = parser.parse_args(argv)

    try:
        crudo = Path(args.entrada).read_text(encoding="utf-8") if args.entrada else sys.stdin.read()
        peticion = json.loads(crudo)
    except (OSError, json.JSONDecodeError) as exc:
        return _error("peticion_invalida", f"No se pudo leer la petición: {exc}")

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
    salidas = Path(args.salidas)
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

    if args.solo_calculo:
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
