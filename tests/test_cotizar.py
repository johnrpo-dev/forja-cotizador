"""Tests del orquestador de punta a punta: datos reales, salidas en tmp_path."""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skill" / "scripts"))

import cotizar  # noqa: E402


def _correr(tmp_path, capsys, peticion, extra_args=()):
    entrada = tmp_path / "peticion.json"
    entrada.write_text(json.dumps(peticion, ensure_ascii=False), encoding="utf-8")
    codigo = cotizar.main(["--entrada", str(entrada), "--salidas", str(tmp_path / "salidas"),
                           *extra_args])
    return codigo, json.loads(capsys.readouterr().out)


PETICION_BASE = {
    "cliente": "café y punto",
    "items": [{"sku": "SIL-006", "cantidad": 30}],
    "fecha": "2026-07-30",
}


def test_flujo_completo_genera_documento_e_historial(tmp_path, capsys):
    codigo, salida = _correr(tmp_path, capsys, PETICION_BASE)
    assert codigo == 0
    assert salida["estado"] == "ok"
    assert salida["numero"] == "COT-2026-001"
    assert salida["cliente"]["nit"] == "901238450-6"
    # 30 × 68.000 × 0,95 = 1.938.000; IVA 368.220; total 2.306.220
    assert salida["totales"]["subtotal"] == "1938000"
    assert salida["totales"]["total"] == "2306220"
    assert Path(salida["documento"]).exists()
    with open(tmp_path / "salidas" / "historial.csv", newline="", encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))
    assert filas[0]["numero"] == "COT-2026-001"
    assert filas[0]["total"] == "2306220"


def test_consecutivo_avanza_entre_corridas(tmp_path, capsys):
    _correr(tmp_path, capsys, PETICION_BASE)
    _, segunda = _correr(tmp_path, capsys, PETICION_BASE)
    assert segunda["numero"] == "COT-2026-002"


def test_solo_calculo_no_toca_estado(tmp_path, capsys):
    codigo, salida = _correr(tmp_path, capsys, PETICION_BASE, ["--solo-calculo"])
    assert codigo == 0
    assert salida["estado"] == "ok"
    assert salida["numero"] is None
    assert salida["documento"] is None
    assert not (tmp_path / "salidas").exists()  # ni documento ni historial


def test_sku_no_encontrado_es_error_json(tmp_path, capsys):
    peticion = dict(PETICION_BASE, items=[{"sku": "VEN-999", "cantidad": 1}])
    codigo, salida = _correr(tmp_path, capsys, peticion)
    assert codigo == 1
    assert salida["estado"] == "error"
    assert salida["tipo"] == "sku_no_encontrado"
    assert salida["sku"] == "VEN-999"
    assert not (tmp_path / "salidas").exists()  # no consumió consecutivo


def test_cliente_ambiguo_devuelve_candidatos(tmp_path, capsys):
    # "clínica" coincide con la odontológica y la veterinaria.
    codigo, salida = _correr(tmp_path, capsys, dict(PETICION_BASE, cliente="clínica"))
    assert codigo == 1
    assert salida["tipo"] == "cliente_ambiguo"
    assert len(salida["candidatos"]) >= 2


def test_cliente_no_encontrado(tmp_path, capsys):
    codigo, salida = _correr(tmp_path, capsys,
                             dict(PETICION_BASE, cliente="Astilleros del Pacífico Sur"))
    assert codigo == 1
    assert salida["tipo"] == "cliente_no_encontrado"


def test_stock_insuficiente_alerta_sin_alterar_precios(tmp_path, capsys):
    # SIL-003 (stock 0 en catalogo.csv): 2 × 1.185.000 = 2.370.000 se cotiza pleno.
    peticion = dict(PETICION_BASE, items=[{"sku": "SIL-003", "cantidad": 2}])
    codigo, salida = _correr(tmp_path, capsys, peticion, ["--solo-calculo"])
    assert codigo == 0
    assert salida["totales"]["subtotal"] == "2370000"
    assert any("SIL-003" in a and "reposición" in a for a in salida["alertas"])


def test_descuento_excedido_marca_borrador_en_historial(tmp_path, capsys):
    peticion = dict(PETICION_BASE, descuento_manual_pct="0.20")
    _, salida = _correr(tmp_path, capsys, peticion)
    assert salida["requiere_aprobacion"] is True
    with open(tmp_path / "salidas" / "historial.csv", newline="", encoding="utf-8-sig") as f:
        assert list(csv.DictReader(f))[0]["estado"] == "borrador_requiere_aprobacion"
