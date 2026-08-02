# Registro cronológico de prompts — Forja

Evidencia del proceso de construcción, junto a `docs/proceso.md`. Cada prompt
se reproduce **tal cual se envió** (sin editar: se conservan erratas y hasta un
párrafo duplicado por un pegado doble), tomado de los transcripts de sesión de
Claude Code. Debajo de cada uno, un resumen breve de lo que se hizo en
respuesta. Horas en hora local de Colombia (UTC−5).

**Alcance temporal:** registro de las sesiones 1 a 3, hasta el **31 de julio de
2026**. Los prompts y sus resúmenes quedan tal como ocurrieron y no se
actualizan después: el trabajo posterior no está aquí. Para el estado actual
del sistema, ver `README.md` y `demo/resumen_pruebas.md`.

---

## Sesión 1 — Datos sintéticos (30 de julio, 22:01–22:22)

### P1 · 22:01

```text
Crea la estructura de un proyecto llamado "forja" para el reto de generación
de cotizaciones de una pyme colombiana ficticia: "Distribuciones El Cedro SAS",
que vende mobiliario y dotación para oficinas y negocios.

Genera estos datos 100% sintéticos:

1. datos/catalogo.csv — 50 productos con columnas: sku, nombre, categoria,
   unidad, precio_unitario_cop (antes de IVA, valores realistas entre 15.000
   y 2.500.000 COP), stock. Categorías: sillas, escritorios, archivadores,
   iluminación, accesorios.
```

**Respuesta:** se creó la estructura base y `datos/catalogo.csv` con 50
productos sintéticos (10 por categoría, SKUs por prefijo SIL/ESC/ARC/ILU/ACC,
precios de 15.000 a 2.450.000 COP antes de IVA). El asistente notó que el
mensaje parecía cortado tras el punto 1 y pidió el resto de la lista.

### P2 · 22:03

```text
vamos paso por paso.
```

**Respuesta:** se confirmó el paso 1 como completo y quedó acordado el flujo:
un paso por prompt.

### P3 · 22:04

```text
2. datos/clientes.csv — 50 clientes con: nit, razon_social, contacto, ciudad,
   agente_retenedor (si/no), condicion_pago (contado/30 dias), notas.
   Ciudades colombianas variadas.
```

**Respuesta:** `datos/clientes.csv` con 50 clientes sintéticos: NITs con
formato colombiano, 20 ciudades, sectores variados, 24 agentes retenedores
correlacionados de forma verosímil con el tamaño del cliente, y notas
operativas (horarios de entrega, órdenes de compra, facturación).

### P4 · 22:09

```text
3. datos/politicas_comerciales.md — descuentos por volumen (>=20 und: 5%,
   >=50 und: 10%), descuento manual máximo 15% (por encima requiere
   aprobación), validez de cotización 15 días, tiempos de entrega por ciudad.
```

**Respuesta:** `datos/politicas_comerciales.md` con los descuentos por volumen
evaluados **por línea de producto**, descuento manual hasta 15 % (más requiere
aprobación de gerencia), validez de 15 días, tabla de entrega para las 20
ciudades de `clientes.csv`, y apartados complementarios (IVA 19 %, nota para
agentes retenedores, primera compra de clientes nuevos de contado).

### P5 · 22:14

```text
4. datos/solicitudes_prueba.md — 10 solicitudes de cotización escritas como
   mensajes informales de WhatsApp de un vendedor colombiano, con lenguaje
   coloquial. Incluye deliberadamente: 2 con productos que NO existen en el
   catálogo, 1 con descuento del 20% (excede el máximo), 1 para cliente
   agente retenedor con monto alto, 1 ambigua (no dice cantidades).
```

**Respuesta:** 10 mensajes estilo WhatsApp referenciando clientes y productos
reales de los CSV. Casos deliberados en esta primera versión: solicitudes 2 y
7 con productos inexistentes (sofá en L y mesa de centro; greca y
ventiladores), solicitud 3 con el 20 % prometido, solicitud 4 con la
Fiduciaria Andina (retenedor, monto alto), solicitud 5 ambigua sin cantidades.

### P6 · 22:20

```text
En este caso los productos inexistentes, serian los que ya no tienen stock o ya no hay inventario de estos
```

**Respuesta:** redefinición acatada — en `catalogo.csv` quedaron agotados
SIL-003 (silla Monserrate), ESC-003 (escritorio Macondo) y ARC-008 (caja
fuerte digital), y las solicitudes 2 y 7 se reescribieron para pedir productos
reales del catálogo con stock 0 (caso de bloqueo total y de disponibilidad
parcial, respectivamente). El caso "producto inexistente" se recuperaría
después con las solicitudes 11 y 12 (ver sesión 2, P1, y
`docs/proceso.md` §"Decisiones y correcciones" #4).

### P7 · 22:22

```text
5. registro/consecutivo.txt con valor inicial "0" y registro/historial.csv
   con encabezados: numero, fecha, cliente_nit, cliente_nombre, subtotal,
   descuento, iva, total, estado.
```

**Respuesta:** carpeta `registro/` con `consecutivo.txt` en "0" y
`historial.csv` solo con encabezados. (Esta estructura fue luego descartada
por la fase de arquitectura: el contador aparte se eliminó a favor de la
numeración derivada del historial, y el estado pasó a `salidas/`.)

---

**Entre sesiones:** la fase de arquitectura y planeación (chat de Claude)
produjo `docs/arquitectura.md`, la reestructuración a la forma definitiva
(`datos/` → `skill/datos/`, solicitudes a `demo/`, estado a `salidas/`,
descarte de `.claude/skills/forja/` y de `consecutivo.txt`) y el scaffolding
con contratos `NotImplementedError` etiquetados por fase.

---

## Sesión 2 — Implementación por fases (30–31 de julio, 23:15–00:18)

### P1 · 23:15

```text
Agrega al final de demo/solicitudes_prueba.md dos solicitudes nuevas con el
mismo formato y tono informal de las existentes:

- Solicitud 11: doña Miriam de la Droguería Nororiente (Cúcuta) pregunta si
  además de los estantes manejamos una greca industrial de 60 tazas y un
  ventilador de techo para la bodega.
- Solicitud 12: Marcela del Hotel Bahía Serena (Cartagena) pide, aparte de lo
  del lobby, 2 aires acondicionados mini split de 12000 BTU, y el vendedor
  duda de que eso se maneje.

IMPORTANTE: greca, ventilador de techo y aire acondicionado NO deben existir
en skill/datos/catalogo.csv — verifica que no haya nada parecido y NO los
agregues al catálogo. Estas solicitudes existen para probar la ruta
SkuNoEncontrado: el sistema debe preguntar, nunca inventar. Actualiza el
encabezado del archivo si menciona cuántas solicitudes hay.
```

**Respuesta:** solicitudes 11 y 12 agregadas con el mismo tono y timestamps
que continúan la secuencia del día. Se verificó el catálogo completo: no
existe greca, ventilador, aire acondicionado, "split" ni "BTU" ni nada
semejante — no se agregó ningún producto, así que ambas ejercitan la ruta
`SkuNoEncontrado`.

### P2 · 23:18

```text
Lee docs/arquitectura.md. Los datos sintéticos ya existen en skill/datos/ y
demo/solicitudes_prueba.md. Primero valídalos: catalogo.csv (50 filas, precios
numéricos, columnas sku/nombre/categoria/unidad/precio_unitario_cop/stock),
clientes.csv (columna agente_retenedor con valores si/no), y
politicas_comerciales.md (umbrales de descuento por volumen y máximo manual).
Reporta cualquier inconsistencia antes de tocar código.

Luego implementa las tres funciones de skill/scripts/datos_io.py (hoy lanzan
NotImplementedError):
- cargar_catalogo(): {sku: {nombre, categoria, unidad, precio_unitario, stock}}
  con precio_unitario como Decimal y stock como int.
- cargar_clientes(): {nit: {...}} con agente_retenedor como bool. Debe
  permitir también buscar cliente por razón social aproximada (función
  auxiliar buscar_cliente(texto) que retorne candidatos).
- cargar_politicas(): umbrales de descuento por volumen, descuento manual
  máximo (15%) y validez, como Decimal. Los umbrales pueden ir definidos como
  constantes que reflejen politicas_comerciales.md, documentando que ese
  archivo es la fuente.

Agrega tests de carga en tests/ (archivo nuevo test_datos_io.py) y no
termines hasta que TODO pytest esté en verde.
```

**Respuesta:** validación sin inconsistencias (50 filas por CSV, tipos
correctos, sin duplicados; stock 0 de SIL-003/ESC-003/ARC-008 coherente con
las solicitudes). `datos_io.py` implementado: `cargar_catalogo()`,
`cargar_clientes()`, `buscar_cliente()` (normaliza tildes, subcadenas y
tokens con respaldo de `difflib`, devuelve candidatos ordenados) y
`cargar_politicas()`. 16 tests en verde.

### P3 · 23:22

```text
lo siguiente lo vamos a dividir en 3 pasos:
```

**Respuesta:** el mensaje llegó sin la lista; el asistente pidió los 3 pasos.

### P4 · 23:23

```text
Primero escribe skill/references/reglas_tributarias.md documentando TODAS las
reglas de cálculo con sus supuestos:
- Precios de catálogo antes de IVA, en COP. Redondeo a pesos completos.
- Descuento por volumen POR LÍNEA según politicas_comerciales.md
  (1-19: 0%, 20-49: 5%, >=50: 10%), no acumulable entre líneas.
- Descuento manual global sobre la suma de líneas ya descontadas; si supera
  15%, requiere_aprobacion=True.
- IVA 19% sobre la base con todos los descuentos.
- Retefuente por compras 2.5%, solo si el cliente es agente_retenedor y la
  base gravable antes de IVA supera 1.000.000 COP. Es INFORMATIVA: se muestra
  en el documento como valor que el cliente retendrá al pagar, no se resta
  del total de la cotización. (Simplificación declarada del régimen real.)
```

**Respuesta:** `skill/references/reglas_tributarias.md` escrito como
especificación del motor: supuestos generales (Decimal, redondeo *half-up* a
pesos en cada valor derivado), orden de cálculo explícito en 6 pasos,
descuento por volumen por línea, manual global, IVA 19 %, retefuente
informativa y simplificaciones declaradas. Caso límite definido: el umbral es
estrictamente mayor (exactamente 1.000.000 no causa retención).

### P5 · 23:24

```text
Luego implementa calcular() en skill/scripts/calculo.py respetando su
contrato: núcleo puro (sin archivos, sin prints, sin rutas), lanza
SkuNoEncontrado si un ítem no está en catálogo — NUNCA estimar precios.
Las políticas definen el descuento por volumen POR LÍNEA: extiende
LineaCotizacion con descuento_volumen_pct y subtotal_con_descuento, y deja
el descuento manual como campo global sobre la suma de líneas ya
descontadas. Todo con Decimal, redondeo a pesos.implementa calcular() en skill/scripts/calculo.py respetando su
contrato: núcleo puro (sin archivos, sin prints, sin rutas), lanza
SkuNoEncontrado si un ítem no está en catálogo — NUNCA estimar precios.
Las políticas definen el descuento por volumen POR LÍNEA: extiende
LineaCotizacion con descuento_volumen_pct y subtotal_con_descuento, y deja
el descuento manual como campo global sobre la suma de líneas ya
descontadas. Todo con Decimal, redondeo a pesos.
```

*(El texto duplicado viene así en el original — pegado doble.)*

**Respuesta:** `calcular()` implementado según `reglas_tributarias.md`:
núcleo puro, `SkuNoEncontrado` sin rutas que estimen precios, `ValueError`
para cantidades no positivas, `LineaCotizacion` extendida con
`descuento_volumen_pct` y `subtotal_con_descuento` (esta es la corrección del
modelo de descuentos: de global a por línea), descuento manual global con
`requiere_aprobacion` si supera 15 %, alerta de stock insuficiente que cotiza
igual. 28 tests en verde.

### P6 · 23:31

```text
En tests/test_calculo.py: elimina la guarda
test_calcular_existe_y_esta_pendiente y agrega casos: cotización simple;
descuento por volumen en una línea sí y otra no; descuento manual válido;
descuento manual excedido (requiere_aprobacion + alerta); retefuente
aplicada; retefuente NO aplicada por base insuficiente; retefuente NO
aplicada por cliente no retenedor; SkuNoEncontrado; redondeo. Los valores
esperados de los tests calcúlalos a mano en los comentarios para que sean
auditables. Pytest en verde total antes de terminar.
```

**Respuesta:** `test_calculo.py` reescrito para cubrir exactamente la lista,
con la aritmética esperada calculada a mano en comentarios (p. ej. volumen
mixto: 30 sillas al 5 % junto a 5 escritorios al 0 %, verificando que 30+5 no
suben de tramo; redondeos *half-up* que caen justo en fracción). 29 tests en
verde.

### P7 · 23:34

```text
Implementa en este orden:

1. skill/scripts/historial.py — siguiente_numero() deriva COT-2026-NNN del
   máximo en el historial.csv de la carpeta --salidas (si no existe: 001);
   registrar() agrega la fila creando encabezados si hace falta. El estado
   SIEMPRE fuera de skill/.
```

**Respuesta:** `historial.py` implementado: `siguiente_numero()` deriva del
máximo (no de la última fila), reinicia por año e ignora filas con numeración
ajena al patrón; `registrar()` crea archivo y carpeta si faltan. La ruta
siempre llega por parámetro — sin referencias a `skill/`. Tests sobre
`tmp_path`. 34 tests en verde.

### P8 · 23:35

```text
2. skill/assets/plantilla.docx — plantilla sobria con python-docx:
   encabezado de "Distribuciones El Cedro SAS" (NIT ficticio), número y
   fecha, datos del cliente, tabla de ítems (con columna de descuento por
   línea), bloque de totales (subtotal, descuento manual, IVA, total;
   retefuente informativa cuando aplique), alcance, condiciones, validez
   15 días, tiempo de entrega según ciudad (politicas_comerciales.md),
   línea de firma.
```

**Respuesta:** `plantilla.docx` generada con python-docx y verificada:
encabezado a dos columnas, bloque de cliente, tabla de ítems de 6 columnas
(incluida "Desc. línea"), bloque de totales con `{{RETEFUENTE_BLOQUE}}`
condicional, condiciones comerciales, observaciones y línea de firma —
18 marcadores por run como contrato para `documento.py`.

### P9 · 23:40

```text
3. skill/scripts/documento.py — generar_docx() rellena la plantilla; si
   requiere_aprobacion, banda visible "BORRADOR — REQUIERE APROBACIÓN".
   a_pdf() usa LibreOffice si existe; si no, devuelve el .docx sin fallar.
```

**Respuesta:** `documento.py` implementado: reemplazo de los 18 marcadores,
filas de ítems desde el resultado del cálculo, banda roja "BORRADOR — REQUIERE
APROBACIÓN DE GERENCIA COMERCIAL" cuando aplica, bloque de retefuente con el
neto estimado (o eliminado cuando no aplica), y `a_pdf()` con degradación
controlada al `.docx` si LibreOffice falta o falla. 40 tests en verde.

### P10 · 23:42

```text
4. skill/scripts/cotizar.py — conecta todo: JSON de entrada (archivo o
   stdin) → datos_io → calculo → historial → documento → JSON por stdout
   con totales, alertas y ruta del documento. Además: compara la cantidad
   pedida contra el stock del catálogo y agrega alerta de stock
   insuficiente con la nota de reposición que exigen las políticas — sin
   alterar el cálculo de precios. --solo-calculo omite el documento.
```

**Respuesta:** `cotizar.py` como orquestador delgado con errores de negocio
como JSON (`sku_no_encontrado`, `cliente_ambiguo`, `cliente_no_encontrado`,
`peticion_invalida`) que no consumen consecutivo; la comparación de stock se
mantuvo en `calculo.calcular` (un solo lugar testeado) y se expone en las
alertas y en las observaciones del documento. 49 tests en verde y prueba de
humo por stdin (retefuente informativa sin restarse del total).

### P11 · 23:52

```text
Reemplaza el placeholder skill/SKILL.md por la versión definitiva de la
skill "forja". Antes de escribirlo, lee skill/scripts/cotizar.py,
skill/references/reglas_tributarias.md y demo/solicitudes_prueba.md para
que el workflow documente exactamente lo que el código ya hace.

Frontmatter:
- name: forja
- description: redáctala "pushy" para que dispare siempre: generación de
  cotizaciones, propuestas y documentos comerciales para pymes; debe
  activarse cuando el usuario pida cotizar, hacer una propuesta o ficha
  técnica, mencione clientes/productos/precios/descuentos, o pegue un
  mensaje informal de WhatsApp pidiendo precios — aunque nunca use la
  palabra "cotización".

Cuerpo (máximo ~200 líneas), workflow obligatorio:
1. Extraer de la solicitud: cliente, ítems con cantidades, condiciones y
   descuento pedido. Si falta la cantidad de algún ítem, PREGUNTAR antes
   de continuar (ver solicitud 5 como ejemplo del caso).
2. Identificar el cliente contra skill/datos/clientes.csv (usar
   buscar_cliente de datos_io). Cliente no registrado → pedir datos mínimos.
3. Mapear cada ítem a un SKU de skill/datos/catalogo.csv. REGLA
   INQUEBRANTABLE: producto sin SKU correspondiente → informar y preguntar
   si se reemplaza o se excluye (las solicitudes 11 y 12 son este caso).
   PROHIBIDO inventar precios, asumir equivalencias o elegir "el más
   parecido" sin confirmar.
4. Ejecutar scripts/cotizar.py con el JSON armado. PROHIBIDO hacer
   aritmética manual o "verificar" recalculando: el script es la única
   fuente de cálculo. Las alertas que devuelva (stock insuficiente,
   requiere aprobación, retención informativa) se transmiten al usuario
   SIEMPRE, nunca se omiten.
5. Redactar alcance y condiciones personalizadas con las notas del cliente
   y politicas_comerciales.md (tiempo de entrega según ciudad, restricciones
   de recibo).
6. Presentar: resumen de totales + ruta del documento + todas las alertas.

Sección "Casos especiales": descuento >15% (borrador de aprobación),
ítems con stock 0 (cotiza con nota de reposición), cliente nuevo,
solicitud ambigua sin cantidades.

Cuando termines, pruébala tú mismo ejecutando el workflow completo con las
solicitudes 1, 3, 5, 11 y 2 de demo/solicitudes_prueba.md — una por una,
mostrándome por cada una: qué extrajiste, qué validaste, qué preguntarías
si aplica, y el resultado. La 11 debe terminar en pregunta, no en documento.
```

**Respuesta:** `SKILL.md` definitivo (~140 líneas) escrito tras releer el
código, y prueba de punta a punta: solicitud 1 → COT-2026-001 emitida;
solicitud 3 → COT-2026-002 como borrador con aprobación pendiente; solicitud
5 → terminó en pregunta por cantidades; solicitud 11 → terminó en pregunta por
productos que no se manejan (sin documento, como se exigía); solicitud 2 →
COT-2026-003 con las alertas de stock. 49 tests en verde. (La solicitud 4
quedó fuera de este conjunto — la auditoría de P13 lo detectaría.)

### P12 · 23:55

```text
Empaqueta la skill para claude.ai: copia skill/ a un directorio temporal
renombrada como "forja" (debe coincidir con el name del frontmatter) y
comprímela como forja.zip con esa carpeta como raíz del ZIP — ni archivos
sueltos en la raíz, ni carpeta contenedora extra. Lista el contenido del
ZIP para verificar, y déjalo en la raíz del proyecto.
```

**Respuesta:** `forja.zip` en la raíz del proyecto: carpeta raíz única
`forja/` verificada con assert, 13 archivos, sin `__pycache__`, empaquetado
con `zipfile` de Python (no `Compress-Archive`, que en Windows escribe
separadores `\` y rompe al descomprimir en el contenedor Linux de claude.ai).

### P13 · 00:09

```text
Auditoría de salidas/. Haz esto en orden y muéstrame cada resultado:

1. Lee salidas/historial.csv y dime a qué solicitud de
   demo/solicitudes_prueba.md corresponde cada número (COT-2026-001 a 003),
   por cliente y totales.
2. La Fase anterior pedía generar las cotizaciones de las solicitudes 1, 2,
   3 y 4. Identifica cuál falta y por qué: revisa si alguna ejecución de
   cotizar.py falló (stock 0 en la solicitud 2, retefuente en la 4) y
   muéstrame el error si lo hubo.
3. Revisa el test de integración del consecutivo: si escribe en salidas/
   real, corrígelo para que use tmp_path de pytest — los tests NUNCA tocan
   el estado real. Corre pytest completo en verde.
4. Si el historial quedó contaminado por tests, límpialo: borra
   salidas/historial.csv y los .docx, y regenera desde cero las 4
   cotizaciones (solicitudes 1, 2, 3, 4) para que queden COT-2026-001 a
   004 limpias y consistentes con el historial.
5. Confírmame: la de la solicitud 2 debe traer las 2 alertas de stock, la
   de la 3 debe ser borrador con "REQUIERE APROBACIÓN" visible, y la de la
   4 debe mostrar la retefuente informativa. Abre cada docx y verifícalo
   en el contenido, no lo asumas.
```

**Respuesta:** auditoría completa en 5 pasos. Mapeo: COT-001 = solicitud 1,
COT-002 = solicitud 3, COT-003 = solicitud 2 (numeración fuera de orden). La
faltante era la **solicitud 4** (Fiduciaria Andina), por **omisión, no por
fallo**: ninguna ejecución de `cotizar.py` falló; la 4 no estaba en el
conjunto corrido en la fase anterior. Los tests ya usaban `tmp_path` — nada
que corregir, 49 en verde. Se borró el estado y se regeneraron las 4
cotizaciones (COT-2026-001 a 004, 1:1 con las solicitudes 1–4), verificando
el contenido real de cada `.docx`: alertas de stock en la 002 (silla
Monserrate y escritorio Macondo agotados), banda "REQUIERE APROBACIÓN" visible
en la 003, retefuente informativa en la 004.

### P14 · 00:18

```text
Regenera forja.zip desde el estado actual de skill/ (carpeta raíz 'forja') y muéstrame el listado del ZIP con fechas
```

**Respuesta:** `forja.zip` regenerado con listado y fechas: 13 archivos, raíz
única `forja/`. Las fechas confirmaron que nada de `skill/` cambió después de
`SKILL.md` (23:53) — la auditoría solo tocó `salidas/`, que no viaja en la
skill, así que el contenido del ZIP quedó idéntico al anterior.

---

## Sesión 3 — Documentación del proceso (31 de julio, 20:34–20:56)

### P1 · 20:34

```text
Crea docs/proceso.md documentando cómo se construyó este proyecto:
metodología de dos fases (arquitectura y planeación en un chat de Claude,
ejecución por fases en Claude Code), las 7 fases con lo que se hizo en cada
una, y una sección "Decisiones y correcciones" que registre honestamente:
el cambio de estructura inicial, la corrección del modelo de descuentos de
global a por línea, la auditoría de salidas/ que encontró una cotización
faltante, el debate sobre casos de prueba con productos inexistentes vs.
agotados y por qué se conservaron ambos. Toma los hechos del historial de
git y de los archivos del proyecto — no inventes nada que no haya ocurrido.
```

**Respuesta:** al no existir repositorio git (nunca se ejecutó `git init`),
los hechos se reconstruyeron desde los transcripts de las sesiones de Claude
Code y los archivos del proyecto, y se escribió `docs/proceso.md` con la
metodología, las siete fases y las cuatro decisiones/correcciones con su
evidencia. El usuario interrumpió a mitad de investigación para encargar
también este registro.

### P2 · 20:56

```text
Guarda en docs/prompts-sesion.md el registro cronológico de la sesión: cada
prompt tal cual se envió y un resumen breve de lo que se hizo en respuesta.
Sin editar los prompts. Sirve como evidencia del proceso junto a
docs/proceso.md.
```

**Respuesta:** este archivo, con los prompts extraídos verbatim de los
transcripts de las tres sesiones.
