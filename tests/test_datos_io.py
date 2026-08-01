"""Tests del borde de datos: cargan los CSV sintéticos reales de skill/datos/."""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skill" / "scripts"))

import datos_io  # noqa: E402


# --- catálogo ---------------------------------------------------------------


def test_catalogo_tiene_50_skus():
    assert len(datos_io.cargar_catalogo()) == 50


def test_catalogo_precios_decimal_y_stock_int():
    for sku, item in datos_io.cargar_catalogo().items():
        assert isinstance(item["precio_unitario"], Decimal), sku
        assert isinstance(item["stock"], int), sku
        assert item["precio_unitario"] > 0, sku
        assert item["stock"] >= 0, sku


def test_catalogo_item_conocido():
    silla = datos_io.cargar_catalogo()["SIL-006"]
    assert silla["nombre"] == "Silla rimax apilable para eventos"
    assert silla["categoria"] == "sillas"
    assert silla["unidad"] == "unidad"
    assert silla["precio_unitario"] == Decimal("68000")


# --- clientes ---------------------------------------------------------------


def test_clientes_tiene_50_registros():
    assert len(datos_io.cargar_clientes()) == 50


def test_agente_retenedor_es_bool():
    clientes = datos_io.cargar_clientes()
    assert all(isinstance(c["agente_retenedor"], bool) for c in clientes.values())
    # Un retenedor y un no retenedor conocidos, para atrapar un si/no invertido.
    assert clientes["830214569-7"]["agente_retenedor"] is True  # Fiduciaria Andina
    assert clientes["901238450-6"]["agente_retenedor"] is False  # Café y Punto


def test_cliente_incluye_su_nit():
    clientes = datos_io.cargar_clientes()
    assert all(c["nit"] == nit for nit, c in clientes.items())


def test_buscar_cliente_sin_tildes_ni_mayusculas():
    candidatos = datos_io.buscar_cliente("hotel bahia serena")
    assert candidatos and candidatos[0]["nit"] == "901092837-5"


def test_buscar_cliente_parcial():
    candidatos = datos_io.buscar_cliente("Droguería Nororiente")
    assert candidatos and candidatos[0]["nit"] == "900786153-4"


def test_buscar_cliente_inexistente_devuelve_vacio():
    assert datos_io.buscar_cliente("Petroquímica Zeta del Pacífico") == []
    assert datos_io.buscar_cliente("") == []


def test_tiempo_entrega_segun_ciudad():
    # Valores de politicas_comerciales.md, sección 6.
    assert datos_io.tiempo_entrega("Bogotá") == "2 días hábiles"
    assert datos_io.tiempo_entrega("cucuta") == "5 días hábiles"  # sin tilde
    assert datos_io.tiempo_entrega("Leticia") == "7 días hábiles (confirmar con logística)"


# --- políticas --------------------------------------------------------------


def test_politicas_reflejan_el_documento():
    # Valores de skill/datos/politicas_comerciales.md, secciones 1 a 3.
    p = datos_io.cargar_politicas()
    assert p["descuento_manual_maximo"] == Decimal("0.15")
    assert p["validez_dias"] == 15
    assert p["descuentos_volumen"] == [
        {"desde": 1, "hasta": 19, "descuento": Decimal("0.00")},
        {"desde": 20, "hasta": 49, "descuento": Decimal("0.05")},
        {"desde": 50, "hasta": None, "descuento": Decimal("0.10")},
    ]


def test_politicas_porcentajes_son_decimal():
    p = datos_io.cargar_politicas()
    assert isinstance(p["descuento_manual_maximo"], Decimal)
    assert all(isinstance(t["descuento"], Decimal) for t in p["descuentos_volumen"])


def test_politicas_devuelve_copia_mutable_sin_tocar_constantes():
    p = datos_io.cargar_politicas()
    p["descuentos_volumen"][0]["descuento"] = Decimal("0.99")
    assert datos_io.DESCUENTOS_VOLUMEN[0]["descuento"] == Decimal("0.00")
