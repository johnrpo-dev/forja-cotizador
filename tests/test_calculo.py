"""Tests del núcleo. Importan calculo.py directo: sin CSV, sin docx, sin contenedor.

Cada valor esperado va acompañado del cálculo a mano que lo produce, para que
un evaluador pueda auditar la aritmética sin ejecutar nada.
"""

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skill" / "scripts"))

import calculo  # noqa: E402

# Fixtures en memoria: el núcleo no debe necesitar archivos para probarse.
# Precios tomados de catalogo.csv para que los cálculos a mano sean familiares.
CATALOGO = {
    "SIL-006": {"nombre": "Silla rimax apilable", "precio_unitario": Decimal("68000"), "stock": 240},
    "ESC-001": {"nombre": "Escritorio Cedro 120x60", "precio_unitario": Decimal("489000"), "stock": 40},
    "SIL-003": {"nombre": "Silla gerencial Monserrate", "precio_unitario": Decimal("1185000"), "stock": 0},
}
POLITICAS = {
    "descuentos_volumen": [
        {"desde": 1, "hasta": 19, "descuento": Decimal("0.00")},
        {"desde": 20, "hasta": 49, "descuento": Decimal("0.05")},
        {"desde": 50, "hasta": None, "descuento": Decimal("0.10")},
    ],
    "descuento_manual_maximo": Decimal("0.15"),
    "validez_dias": 15,
}
CONTADO = {"nit": "901238450-6", "agente_retenedor": False}
RETENEDOR = {"nit": "830214569-7", "agente_retenedor": True}


def test_iva_configurado_al_19_por_ciento():
    assert calculo.IVA == Decimal("0.19")


def test_sku_no_encontrado_es_excepcion_propia():
    # Distinguir "no existe en catálogo" de cualquier otro error permite
    # preguntarle al usuario en vez de inventar un precio.
    assert issubclass(calculo.SkuNoEncontrado, Exception)


def test_resultado_arranca_en_ceros():
    r = calculo.ResultadoCalculo()
    assert r.total == Decimal("0")
    assert r.requiere_aprobacion is False
    assert r.alertas == []


def test_cotizacion_simple_sin_descuentos():
    # 10 × 68.000 = 680.000 (10 uds < 20 → 0% volumen)
    # IVA   = 680.000 × 0,19 = 129.200
    # Total = 680.000 + 129.200 = 809.200
    r = calculo.calcular([{"sku": "SIL-006", "cantidad": 10}], CATALOGO, CONTADO, POLITICAS)
    linea = r.lineas[0]
    assert linea.subtotal == Decimal("680000")
    assert linea.descuento_volumen_pct == Decimal("0")
    assert linea.subtotal_con_descuento == Decimal("680000")
    assert r.base_gravable == Decimal("680000")
    assert r.iva == Decimal("129200")
    assert r.total == Decimal("809200")
    assert r.requiere_aprobacion is False
    assert r.retefuente_informativa == Decimal("0")


def test_volumen_una_linea_si_y_otra_no():
    # Línea 1: 30 × 68.000 = 2.040.000; 30 uds → 5% → 2.040.000 × 0,95 = 1.938.000
    # Línea 2:  5 × 489.000 = 2.445.000;  5 uds → 0% → 2.445.000
    # Subtotal = 1.938.000 + 2.445.000 = 4.383.000
    # (las cantidades 30 + 5 = 35 NO se suman para subir de tramo)
    r = calculo.calcular(
        [{"sku": "SIL-006", "cantidad": 30}, {"sku": "ESC-001", "cantidad": 5}],
        CATALOGO, CONTADO, POLITICAS,
    )
    con, sin = r.lineas
    assert con.descuento_volumen_pct == Decimal("0.05")
    assert con.subtotal_con_descuento == Decimal("1938000")
    assert sin.descuento_volumen_pct == Decimal("0")
    assert sin.subtotal_con_descuento == Decimal("2445000")
    assert r.subtotal == Decimal("4383000")


def test_volumen_50_o_mas_da_10_por_ciento():
    # 50 × 68.000 = 3.400.000 × 0,90 = 3.060.000
    r = calculo.calcular([{"sku": "SIL-006", "cantidad": 50}], CATALOGO, CONTADO, POLITICAS)
    assert r.lineas[0].descuento_volumen_pct == Decimal("0.10")
    assert r.lineas[0].subtotal_con_descuento == Decimal("3060000")


def test_descuento_manual_valido():
    # Subtotal con volumen: 30 × 68.000 × 0,95 = 1.938.000
    # Manual 10% (≤ 15%, no requiere aprobación): 1.938.000 × 0,10 = 193.800
    # Base  = 1.938.000 − 193.800 = 1.744.200
    # IVA   = 1.744.200 × 0,19 = 331.398
    # Total = 1.744.200 + 331.398 = 2.075.598
    r = calculo.calcular(
        [{"sku": "SIL-006", "cantidad": 30}], CATALOGO, CONTADO, POLITICAS,
        descuento_manual_pct=Decimal("0.10"),
    )
    assert r.subtotal == Decimal("1938000")
    assert r.descuento_valor == Decimal("193800")
    assert r.base_gravable == Decimal("1744200")
    assert r.iva == Decimal("331398")
    assert r.total == Decimal("2075598")
    assert r.requiere_aprobacion is False
    assert r.alertas == []


def test_manual_de_15_exacto_no_requiere_aprobacion():
    # 15% es el tope autónomo del asesor: en el límite no hay aprobación.
    r = calculo.calcular(
        [{"sku": "SIL-006", "cantidad": 10}], CATALOGO, CONTADO, POLITICAS,
        descuento_manual_pct=Decimal("0.15"),
    )
    assert r.requiere_aprobacion is False


def test_manual_excedido_calcula_pero_requiere_aprobacion():
    # Subtotal con volumen: 1.938.000 (ver test anterior)
    # Manual 20% > 15%: se calcula igual y se marca para aprobación.
    # Descuento = 1.938.000 × 0,20 = 387.600 → base = 1.550.400
    r = calculo.calcular(
        [{"sku": "SIL-006", "cantidad": 30}], CATALOGO, CONTADO, POLITICAS,
        descuento_manual_pct=Decimal("0.20"),
    )
    assert r.requiere_aprobacion is True
    assert r.base_gravable == Decimal("1550400")
    assert any("aprobación" in a for a in r.alertas)


def test_retefuente_aplicada():
    # 25 × 489.000 = 12.225.000; 25 uds → 5% → base = 12.225.000 × 0,95 = 11.613.750
    # Base 11.613.750 > 1.000.000 y cliente retenedor → aplica.
    # Retefuente = 11.613.750 × 0,025 = 290.343,75 → 290.344 (half-up)
    # IVA        = 11.613.750 × 0,19  = 2.206.612,50 → 2.206.613 (half-up)
    # Informativa: total = base + IVA, SIN restar la retención.
    r = calculo.calcular([{"sku": "ESC-001", "cantidad": 25}], CATALOGO, RETENEDOR, POLITICAS)
    assert r.retefuente_informativa == Decimal("290344")
    assert r.total == r.base_gravable + r.iva == Decimal("13820363")


def test_retefuente_no_aplicada_por_base_insuficiente():
    # 2 × 489.000 = 978.000 < 1.000.000 → no aplica aunque el cliente retenga.
    r = calculo.calcular([{"sku": "ESC-001", "cantidad": 2}], CATALOGO, RETENEDOR, POLITICAS)
    assert r.base_gravable == Decimal("978000")
    assert r.retefuente_informativa == Decimal("0")


def test_retefuente_umbral_es_estrictamente_mayor():
    # Base exactamente 1.000.000 no supera el umbral → no aplica.
    catalogo = {"X": {"nombre": "x", "precio_unitario": Decimal("1000000"), "stock": 9}}
    r = calculo.calcular([{"sku": "X", "cantidad": 1}], catalogo, RETENEDOR, POLITICAS)
    assert r.retefuente_informativa == Decimal("0")


def test_retefuente_no_aplicada_por_cliente_no_retenedor():
    # Misma compra del caso aplicado (base 11.613.750 > 1.000.000), pero el
    # cliente no es agente retenedor → no aplica y el total no cambia.
    r = calculo.calcular([{"sku": "ESC-001", "cantidad": 25}], CATALOGO, CONTADO, POLITICAS)
    assert r.retefuente_informativa == Decimal("0")
    assert r.total == Decimal("13820363")


def test_sku_inexistente_lanza_y_no_estima():
    with pytest.raises(calculo.SkuNoEncontrado):
        calculo.calcular([{"sku": "VEN-999", "cantidad": 1}], CATALOGO, CONTADO, POLITICAS)


def test_redondeo_half_up_a_pesos():
    # IVA:  11.613.750 × 0,19  = 2.206.612,50 → 2.206.613 (la mitad sube)
    # Rete: 11.613.750 × 0,025 =   290.343,75 →   290.344
    r = calculo.calcular([{"sku": "ESC-001", "cantidad": 25}], CATALOGO, RETENEDOR, POLITICAS)
    assert r.iva == Decimal("2206613")
    assert r.retefuente_informativa == Decimal("290344")
    # Todo valor expuesto queda en pesos completos (sin decimales).
    for valor in (r.subtotal, r.descuento_valor, r.base_gravable, r.iva, r.total):
        assert valor == valor.to_integral_value()


def test_sin_stock_alerta_pero_cotiza():
    # SIL-003 tiene stock 0: se cotiza igual y se alerta para indicar reposición.
    r = calculo.calcular([{"sku": "SIL-003", "cantidad": 2}], CATALOGO, CONTADO, POLITICAS)
    assert r.total > 0
    assert any("SIL-003" in a for a in r.alertas)


def test_cantidad_invalida_lanza_valueerror():
    for cantidad in (0, -3):
        with pytest.raises(ValueError):
            calculo.calcular([{"sku": "SIL-006", "cantidad": cantidad}], CATALOGO, CONTADO, POLITICAS)
