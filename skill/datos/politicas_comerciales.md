# Políticas comerciales — Distribuciones El Cedro SAS

Documento de referencia para la elaboración de cotizaciones.
Aplica sobre los precios del catálogo (`catalogo.csv`), expresados en COP antes de IVA.

## 1. Descuentos por volumen

Se aplican automáticamente por línea de producto, según la cantidad cotizada
de cada ítem:

| Cantidad por ítem | Descuento |
|---|---|
| 1 a 19 unidades | 0% |
| 20 a 49 unidades | 5% |
| 50 unidades o más | 10% |

- El descuento por volumen se calcula sobre el precio unitario de lista.
- No es acumulable entre ítems distintos: cada línea se evalúa por separado.

## 2. Descuento manual (comercial)

- El asesor comercial puede otorgar un descuento adicional de hasta **15%**
  sobre el subtotal ya afectado por el descuento de volumen.
- Todo descuento manual **superior al 15% requiere aprobación de la gerencia
  comercial** antes de emitir la cotización. Debe quedar registro escrito de
  la aprobación (correo o firma en la orden interna).
- El descuento manual debe justificarse en las notas de la cotización
  (ej.: cliente frecuente, negociación por proyecto, igualación de oferta).

## 3. Validez de la cotización

- Toda cotización tiene una validez de **15 días calendario** contados desde
  su fecha de emisión.
- Vencido el plazo, los precios y la disponibilidad de stock deben
  confirmarse nuevamente antes de facturar.

## 4. Impuestos y retenciones

- Los precios del catálogo **no incluyen IVA**. Se liquida IVA del 19% sobre
  el subtotal después de descuentos.
- Si el cliente es **agente retenedor** (ver `clientes.csv`), la cotización
  debe incluir la nota: "Cliente agente retenedor: aplicar retenciones de ley
  al momento del pago".

## 5. Condiciones de pago

- **Contado**: pago contra entrega o anticipado según acuerdo.
- **30 días**: crédito sujeto a cupo aprobado por cartera; primera compra de
  clientes nuevos siempre de contado.

## 6. Tiempos de entrega por ciudad

Contados en días hábiles desde la confirmación del pedido (o del pago, para
ventas de contado), sujetos a disponibilidad de stock:

| Ciudad | Tiempo de entrega |
|---|---|
| Bogotá | 2 días hábiles |
| Medellín | 3 días hábiles |
| Cali | 3 días hábiles |
| Barranquilla | 4 días hábiles |
| Bucaramanga | 4 días hábiles |
| Cartagena | 4 días hábiles |
| Pereira | 3 días hábiles |
| Manizales | 3 días hábiles |
| Armenia | 3 días hábiles |
| Ibagué | 3 días hábiles |
| Cúcuta | 5 días hábiles |
| Villavicencio | 4 días hábiles |
| Santa Marta | 5 días hábiles |
| Neiva | 4 días hábiles |
| Pasto | 6 días hábiles |
| Montería | 5 días hábiles |
| Tunja | 3 días hábiles |
| Popayán | 5 días hábiles |
| Valledupar | 5 días hábiles |
| Sincelejo | 5 días hábiles |
| Otras ciudades | 7 días hábiles (confirmar con logística) |

- Pedidos con ítems sin stock suficiente: el tiempo de entrega se cuenta
  desde la reposición estimada y debe indicarse en la cotización.
- Entregas en obra, zona franca o con restricción horaria (ver notas del
  cliente) pueden requerir 1 a 2 días hábiles adicionales de coordinación.
