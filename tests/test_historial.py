"""Tests del historial: usan tmp_path — jamás tocan salidas/ real."""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skill" / "scripts"))

import historial  # noqa: E402


def test_sin_historial_arranca_en_001(tmp_path):
    assert historial.siguiente_numero(tmp_path / "historial.csv", 2026) == "COT-2026-001"


def test_consecutivo_es_maximo_mas_uno(tmp_path):
    ruta = tmp_path / "historial.csv"
    # Desordenado a propósito: debe derivar del máximo, no de la última fila.
    for numero in ("COT-2026-002", "COT-2026-007", "COT-2026-001"):
        historial.registrar(ruta, {"numero": numero, "fecha": "2026-07-30"})
    assert historial.siguiente_numero(ruta, 2026) == "COT-2026-008"


def test_consecutivo_reinicia_por_anio(tmp_path):
    ruta = tmp_path / "historial.csv"
    historial.registrar(ruta, {"numero": "COT-2025-041"})
    assert historial.siguiente_numero(ruta, 2026) == "COT-2026-001"


def test_registrar_crea_encabezados_y_acumula(tmp_path):
    ruta = tmp_path / "historial.csv"
    historial.registrar(ruta, {"numero": "COT-2026-001", "total": "809200",
                               "campo_extra": "se ignora"})
    historial.registrar(ruta, {"numero": "COT-2026-002"})
    with open(ruta, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    assert [f_["numero"] for f_ in filas] == ["COT-2026-001", "COT-2026-002"]
    assert list(filas[0].keys()) == historial.COLUMNAS
    assert filas[0]["total"] == "809200"
    assert filas[1]["total"] == ""  # columnas ausentes quedan vacías, no rompen


def test_fila_con_numero_ajeno_no_rompe(tmp_path):
    ruta = tmp_path / "historial.csv"
    historial.registrar(ruta, {"numero": "BORRADOR"})
    historial.registrar(ruta, {"numero": "COT-2026-003"})
    assert historial.siguiente_numero(ruta, 2026) == "COT-2026-004"
