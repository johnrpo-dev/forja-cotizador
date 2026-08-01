# Resumen de pruebas — las 14 solicitudes de demo

Corrida real del flujo completo (1 de agosto de 2026, la fecha que llevan las
filas de `salidas/historial.csv`) sobre `demo/solicitudes_prueba.md`, una
solicitud por vez, contra un `salidas/` reiniciado desde cero para que la
numeración quede trazable. Cada documento se generó ejecutando
`skill/scripts/cotizar.py`; ningún valor de esta tabla fue calculado a mano.
Las solicitudes que terminan en pregunta **no** ejecutaron el script ni
consumieron consecutivo: la regla de la skill es preguntar en la extracción o
el mapeo, antes de calcular.

Las solicitudes 13 y 14 se ejecutaron en **modo ficha** (`--modo ficha`):
producen documento pero no consumen consecutivo ni escriben en el historial.

## Tabla de resultados

| # | Cliente | Qué se extrajo | Resultado | Alertas |
|---|---|---|---|---|
| 1 | Café y Punto SAS (Medellín) | 30 × silla rimax apilable (SIL-006), contado, urgente | **COT-2026-001** — total $2.306.220 | ninguna |
| 2 | Estudio Jurídico Vargas y Asociados SAS (Medellín) | 1 × silla gerencial Monserrate (SIL-003), 1 × escritorio Macondo wengué (ESC-003), entrega prioritaria | **COT-2026-002** — total $3.659.250 | stock ×2: SIL-003 y ESC-003 agotados (0 unidades); nota de reposición en el documento |
| 3 | Ferretería La Frontera SAS (Cúcuta) | 60 × organizador (ACC-003), 40 × papelera (ACC-004), 25 × cartelera corcho (ACC-006), 20 % prometido, contado | **COT-2026-003** — total $6.671.616, **borrador** | aprobación: 20 % > tope del 15 %, requiere gerencia comercial |
| 4 | Fiduciaria Andina SA (Bogotá) | 25 × escritorio Cedro (ESC-001), 25 × silla Cedro Pro (SIL-001), 10 × archivador rodante (ARC-009), 4 × gabinete alto (ARC-003), 1 × mesa de juntas (ESC-006), 30 días | **COT-2026-004** — total $43.702.155 | retención informativa: $918.113 (agente retenedor, base > $1.000.000) |
| 5 | Hotel Bahía Serena SAS (Cartagena) | sillas de espera y lámparas para recepción — **sin cantidades** | **Consulta, sin documento**: ¿cuántas sillas de espera y cuántas lámparas? ¿Lámpara de piso (ILU-003), colgante (ILU-004) o aplique (ILU-009)? | — |
| 6 | Universidad Corporación del Sur (Pasto) | 60 × silla plegable acolchada (SIL-010), 4 × tablero acrílico 120×80 (ACC-005), 30 días, para pliegos | **COT-2026-005** — total $6.921.040 | retención informativa: $145.400 |
| 7 | Corabastos Mayorista del Centro SAS (Bogotá) | 10 × silla rimax (SIL-006), 1 × caja fuerte digital (ARC-008), 2 × mesa auxiliar rodante (ESC-010), entrega antes de las 6:00 a. m. | **COT-2026-006** — total $1.870.680 | stock: ARC-008 agotado; retención informativa: $39.300 |
| 8 | Droguería Nororiente SAS (Cúcuta) | 4 × estante metálico (ARC-007), 2 × papelera (ACC-004), contado | **COT-2026-007** — total $1.742.160 | ninguna |
| 9 | Logística del Oriente SAS (Bucaramanga) | 3 × locker 9 puestos (ARC-004), 1 × mesa de juntas (ESC-006), 6 × silla interlocutora Guadua (SIL-004), recibo nocturno, 30 días con OC | **COT-2026-008** — total $8.047.970 | retención informativa: $169.075 |
| 10 | Software Eje Cafetero SAS (Pereira) | 8 × ESC-001, 8 × silla Nogal (SIL-008), 8 × base refrigerante (ACC-001), 8 × soporte monitor (ACC-007), contado — descuento pedido **sin cifra** ("algún descuentico") | **Consulta, sin documento**: ¿qué porcentaje de descuento autorizas? Hasta 15 % no requiere aprobación; superior pasa por gerencia comercial | — |
| 11 | Droguería Nororiente SAS (Cúcuta) | greca industrial 60 tazas y ventilador de techo | **Consulta, sin documento**: no manejamos esos productos (verificado: 0 coincidencias en catálogo). ¿Se excluyen o se consulta al cliente? | — |
| 12 | Hotel Bahía Serena SAS (Cartagena) | 2 × aire acondicionado mini split 12000 BTU | **Consulta, sin documento**: no manejamos aires acondicionados (verificado: 0 coincidencias). Responder al cliente que no está en el portafolio | — |
| 13 | Droguería Nororiente SAS (Cúcuta) | medidas y material del estante metálico de carga liviana (ARC-007) — **sin cantidades ni precios**, pide explícitamente no cotizar todavía | **Ficha técnica** — `salidas/FICHA-ARC-007.docx`, precio de lista $345.000, entrega 5 días hábiles (Cúcuta). **Sin consecutivo** | el catálogo no registra características |
| 14 | Universidad Corporación del Sur (Pasto) | ficha de la silla ergonómica Nogal con soporte lumbar (SIL-008) para anexar al expediente de compra, sin orden ni cantidades definidas | **Ficha técnica** — `salidas/FICHA-SIL-008.docx`, precio de lista $915.000, entrega 6 días hábiles (Pasto). **Sin consecutivo** | el catálogo no registra dimensiones ni materiales: la ficha los **declara**, no los completa |

Notas de la corrida:

- Las notas de cliente relevantes viajaron en las observaciones del documento:
  ascensor de carga (2), entrega antes de las 6:00 a. m. (7), recibo nocturno (9).
- Las fichas (13 y 14) resolvieron la ciudad desde el cliente de la solicitud,
  que es lo que define el tiempo de entrega impreso en el documento.

## Casos especiales y la ruta que ejercita cada uno

### Solicitud sin cantidades (5)

Ejercita la regla del paso 2 del workflow: **si falta una cantidad, se
pregunta antes de continuar** — nunca se asume "1". La extracción encontró los
productos candidatos (silla de espera tándem SIL-007; tres lámparas posibles)
pero el mensaje no dice cuántos, así que el flujo se detiene en la pregunta y
`cotizar.py` nunca se ejecuta: no se consume consecutivo ni queda rastro en el
historial. Una cotización con cantidades inventadas sería peor que una
pregunta de más.

### Descuento solicitado sin cifra (10)

Ejercita la extensión del mismo principio al descuento: "algún descuentico
dentro de lo permitido" no trae porcentaje, y el porcentaje es una decisión
comercial del vendedor — el sistema no la toma por su cuenta. La respuesta
correcta es preguntar qué descuento autoriza, indicando el marco: hasta 15 %
no requiere aprobación, por encima pasa por gerencia comercial (y no hay
descuento por volumen que aplicar de oficio: las 8 unidades por línea no
alcanzan el tramo de 20). `cotizar.py` no se ejecuta y el consecutivo no se
mueve. Este caso quedó cubierto explícitamente en `SKILL.md` (paso 2 y
"Casos especiales") por consistencia con la solicitud 5.

### Stock agotado (2 y 7)

Ejercita la alerta de inventario de `calculo.calcular` y la política §6: un
producto agotado **se cotiza igual, a precio pleno, con alerta** y nota de
reposición en las observaciones del documento. La 2 es el caso de bloqueo
total (sus dos ítems, SIL-003 y ESC-003, tienen stock 0 — dos alertas) y la 7
el de disponibilidad parcial (solo ARC-008 agotado entre tres ítems). El
sistema avanza e informa; no bloquea, porque la venta puede esperar la
reposición.

### Descuento sobre el máximo (3)

Ejercita `requiere_aprobacion`: el 20 % prometido por el vendedor supera el
tope autónomo del 15 %, así que el motor **calcula igual** (descuento de
$1.401.600 sobre el subtotal ya afectado por volumen) pero marca la cotización
y el documento sale con la banda "BORRADOR — REQUIERE APROBACIÓN DE GERENCIA
COMERCIAL"; en el historial queda como `borrador_requiere_aprobacion`. De paso
prueba el descuento por volumen **por línea**: 10 % para los 60 organizadores,
5 % para las 40 papeleras y 5 % para las 25 carteleras — cada línea su tramo.

### Retención en la fuente informativa (4, 6, 7 y 9)

Ejercita la regla de retefuente: cliente **agente retenedor** y base gravable
antes de IVA **estrictamente mayor** a $1.000.000. Se disparó en cuatro
cotizaciones (Fiduciaria $918.113, Universidad $145.400, Corabastos $39.300,
Logística del Oriente $169.075) y en las cuatro es **informativa**: el total
cotizado es base + IVA completo, y el documento explica que ese valor lo
retendrá el cliente al pagar la factura. La 4 es además el caso de monto alto
pedido por el reto ($43.702.155 con descuento de volumen del 5 % en dos de
sus cinco líneas).

### Producto inexistente (11 y 12)

Ejercita la **regla inquebrantable** del paso 4 del workflow y la excepción
`SkuNoEncontrado` del motor: un producto sin SKU en el catálogo **detiene el
flujo y produce una pregunta**, nunca un precio estimado ni una equivalencia
asumida. La verificación fue real: búsqueda en `catalogo.csv` de greca,
ventilador, aire, split, BTU y acondicionado — cero coincidencias. A
diferencia del stock agotado (que cotiza con alerta), aquí no hay nada que
cotizar: la respuesta correcta es informar que no se manejan y preguntar si se
excluyen o se reemplazan por algo del catálogo. Ningún documento se generó y
el consecutivo no se movió.

### Consulta de producto sin precios (13 y 14)

Ejercita el paso 1 del workflow —decidir el tipo de documento— y el modo
`--modo ficha`: una pregunta sobre el producto **no** es una cotización de una
unidad. A diferencia de las consultas 5, 10, 11 y 12, estas dos **sí** producen
documento, pero ninguna toca el estado del negocio: tras correrlas,
`salidas/historial.csv` quedó byte por byte idéntico —mismo SHA-256, las mismas
8 filas, COT-2026-008 sigue siendo la última—. Emitir una cotización numerada
para responder "¿qué medidas tiene?" ensuciaría el consecutivo con documentos
que nadie pidió.

La 13 se resuelve completa porque el catálogo sí trae el dato dentro del nombre
del producto: dimensiones 200 × 90 × 40 cm y material Metal, que es justo lo que
doña Miriam preguntó.

La 14 es el caso que importa. `SIL-008` es "Silla ergonómica Nogal con soporte
lumbar", donde **"Nogal" es nombre de línea comercial, no un material** (como
Cedro Pro, Tayrona o Macondo). La ficha imprime "No registradas en catálogo" en
dimensiones y materiales, con el aviso de confirmarlo con el proveedor, en vez
de deducir madera de nogal o estimar unas medidas plausibles; el JSON devuelve
además la alerta correspondiente. Se verificó sobre el `.docx` generado que no
aparece ningún material ni medida inventada. Un dato falso en una ficha que se
anexa a un proceso de compra es exactamente el daño que esta skill existe para
evitar.

## Cierre de la corrida

- **8 solicitudes produjeron cotización** (1, 2, 3, 4, 6, 7, 8, 9) →
  COT-2026-001 a COT-2026-008.
- **2 produjeron ficha técnica** (13 y 14) → `FICHA-ARC-007.docx` y
  `FICHA-SIL-008.docx`, ambas **sin consumir consecutivo**.
- **4 quedaron en consulta al usuario, sin documento** (5, 10, 11, 12), como
  exige el workflow: cantidades faltantes (5), descuento sin cifra (10) y
  productos fuera de catálogo (11 y 12).
- **Historial consistente y consecutivo**: `salidas/historial.csv` tiene
  exactamente 8 filas, numeradas COT-2026-001 a COT-2026-008 sin huecos ni
  duplicados, cada una con su `.docx` presente en `salidas/`, totales
  idénticos a la salida JSON del script, y estados correctos: 7 `emitida` y
  1 `borrador_requiere_aprobacion` (la COT-2026-003). Las dos fichas **no lo
  alteraron**: el archivo quedó con el mismo SHA-256 antes y después de
  generarlas.
