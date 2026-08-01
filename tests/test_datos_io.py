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


# --- especificaciones derivadas del nombre del producto ---------------------


def test_especificaciones_dimensiones_materiales_y_caracteristicas():
    e = datos_io.especificaciones_de("Estante metálico carga liviana 200x90x40")
    assert e["dimensiones"] == "200 × 90 × 40 cm"
    assert e["materiales"] == ["Metal"]
    assert e["caracteristicas"] == []


def test_especificaciones_lee_clausula_con_como_caracteristica():
    e = datos_io.especificaciones_de("Silla ergonómica Nogal con soporte lumbar")
    assert e["caracteristicas"] == ["Soporte lumbar"]
    # "Nogal" es nombre de línea, no material: deducir madera sería inventar.
    assert e["materiales"] == []
    assert e["dimensiones"] == ""


def test_especificaciones_vacias_cuando_el_nombre_no_dice_nada():
    e = datos_io.especificaciones_de("Silla rimax apilable para eventos")
    assert e == {"dimensiones": "", "materiales": [], "caracteristicas": []}
    assert datos_io.especificaciones_de("") == {
        "dimensiones": "", "materiales": [], "caracteristicas": []}


def test_especificaciones_no_confunden_configuracion_con_medidas():
    # "2x1" son cuerpos del archivador, no centímetros: por eso se exigen
    # dos dígitos por componente.
    e = datos_io.especificaciones_de("Archivador 2x1 con cajón de seguridad")
    assert e["dimensiones"] == ""
    assert e["caracteristicas"] == ["Cajón de seguridad"]


def test_material_no_se_infiere_de_subcadenas():
    # "entrepaños" contiene "paño": sin límites de palabra, un gabinete
    # metálico salía con "Paño" entre sus materiales.
    assert datos_io.especificaciones_de("Gabinete alto 2 puertas con entrepaños")[
        "materiales"] == []
    assert datos_io.especificaciones_de("Folderama abierto 5 entrepaños")[
        "materiales"] == []
    assert datos_io.especificaciones_de("Divisor de escritorio en paño 120x40")[
        "materiales"] == ["Paño"]


def test_especificaciones_potencia_capacidad_y_conteos():
    assert datos_io.especificaciones_de("Panel LED 60x60 40W luz blanca") == {
        "dimensiones": "60 × 60 cm", "materiales": [], "caracteristicas": ["40 W"]}
    assert datos_io.especificaciones_de("Papelera metálica perforada 12 litros") == {
        "dimensiones": "", "materiales": ["Metal"], "caracteristicas": ["12 litros"]}
    assert datos_io.especificaciones_de("Locker metálico 9 puestos")[
        "caracteristicas"] == ["9 puestos"]
    assert datos_io.especificaciones_de("Tubo LED T8 18W 120cm")[
        "dimensiones"] == "120 cm"


def test_especificaciones_de_todo_el_catalogo_no_revientan():
    catalogo = datos_io.cargar_catalogo()
    for sku, producto in catalogo.items():
        e = datos_io.especificaciones_de(producto["nombre"])
        assert isinstance(e["dimensiones"], str), sku
        assert isinstance(e["materiales"], list), sku
        assert isinstance(e["caracteristicas"], list), sku


def test_campos_sin_registro_etiqueta_lo_ausente():
    completo = {"dimensiones": "200 × 90 cm", "materiales": ["Metal"],
                "caracteristicas": ["4 gavetas"]}
    assert datos_io.campos_sin_registro(completo) == []
    vacio = {"dimensiones": "", "materiales": [], "caracteristicas": []}
    assert datos_io.campos_sin_registro(vacio) == [
        "dimensiones", "materiales", "características"]
