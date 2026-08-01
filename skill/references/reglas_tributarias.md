# Reglas tributarias y de cálculo — Forja

Especificación del motor de cálculo (`skill/scripts/calculo.py`). Todo lo que
el motor hace con números está definido aquí; si este documento y el código
divergen, es un bug. Los porcentajes comerciales provienen de
`skill/datos/politicas_comerciales.md`; este documento fija cómo se aplican.

## Supuestos generales

- **Moneda:** pesos colombianos (COP). Los precios del catálogo
  (`catalogo.csv`) están **antes de IVA**.
- **Redondeo:** a pesos completos (0 decimales), método *half-up* (mitad hacia
  arriba: 0,50 → 1). Se redondea cada valor derivado en el momento de
  calcularlo — subtotal de línea, descuento manual, IVA, retefuente — de modo
  que todo valor que aparece en el documento es un entero y las sumas mostradas
  cuadran entre sí.
- **Aritmética:** `Decimal`, nunca `float`. Es dinero.
- **Datos sintéticos:** cifras y clientes son ficticios; las reglas simplifican
  el régimen tributario real de forma declarada (ver §5).

## Orden de cálculo

Los pasos se aplican estrictamente en este orden; cada uno opera sobre el
resultado del anterior:

1. Bruto por línea: `cantidad × precio_unitario` de catálogo.
2. Descuento por volumen **por línea** (§1) → subtotal de línea.
3. Suma de subtotales de línea → subtotal de la cotización.
4. Descuento manual **global** sobre ese subtotal (§2) → base gravable.
5. IVA 19% sobre la base gravable (§3) → total a pagar = base + IVA.
6. Retefuente informativa (§4), calculada sobre la base gravable **antes de
   IVA**. No altera el total.

## 1. Descuento por volumen (por línea)

Según la cantidad cotizada de **cada ítem**, sobre su precio unitario de lista:

| Cantidad por ítem | Descuento |
|---|---|
| 1 a 19 unidades | 0% |
| 20 a 49 unidades | 5% |
| 50 unidades o más | 10% |

- Se evalúa **línea por línea**: 30 sillas y 30 escritorios reciben cada uno
  su 5%; las cantidades **no se suman entre líneas** para alcanzar un tramo
  mayor.
- Subtotal de línea = `redondear(cantidad × precio_unitario × (1 − descuento))`.

## 2. Descuento manual (global)

- Se aplica **una sola vez**, sobre la suma de las líneas ya afectadas por el
  descuento de volumen (paso 3 del orden de cálculo). No se aplica línea por
  línea.
- Tope autónomo del asesor: **15%**. Un descuento manual **superior al 15% no
  se rechaza**: el motor lo calcula igual y marca la cotización con
  `requiere_aprobacion = True`, porque la política exige visto bueno de la
  gerencia comercial antes de emitirla.
- Base gravable = `redondear(subtotal × (1 − descuento_manual))`.

## 3. IVA

- **19%** sobre la base gravable, es decir, después de **todos** los
  descuentos (volumen y manual): `IVA = redondear(base_gravable × 0.19)`.
- Total de la cotización = `base_gravable + IVA`.

## 4. Retención en la fuente (informativa)

- **Tarifa:** 2,5% por compras: `retefuente = redondear(base_gravable × 0.025)`.
- **Aplica solo si se cumplen ambas condiciones:**
  1. El cliente es **agente retenedor** (`agente_retenedor = si` en
     `clientes.csv`).
  2. La base gravable **antes de IVA** supera **1.000.000 COP** (estrictamente
     mayor; exactamente 1.000.000 no causa retención).
- **Es informativa, no se resta del total.** La cotización muestra el total
  pleno (base + IVA) y, en nota aparte, el valor que el cliente retendrá al
  momento del pago y el neto que recibiría la empresa. Quien retiene y
  certifica es el cliente al pagar la factura — una cotización no liquida
  retenciones.

## 5. Simplificaciones declaradas frente al régimen real

Asumidas a sabiendas para el alcance de la demo:

- El umbral real de retefuente por compras se expresa en **UVT** (27 UVT para
  obligados a declarar) y cambia cada año; aquí se fija en 1.000.000 COP.
- No se modelan **ReteIVA ni ReteICA**, ni tarifas diferenciales por régimen
  del vendedor (la nota al agente retenedor de `politicas_comerciales.md` las
  cubre genéricamente como "retenciones de ley").
- Todos los productos se tratan como **gravados a la tarifa general del 19%**;
  no hay bienes exentos ni excluidos en el catálogo.
- La condición de agente retenedor viene dada por `clientes.csv`, sin validar
  calidades tributarias reales (gran contribuyente, autorretenedor, etc.).
