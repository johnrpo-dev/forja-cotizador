# Proceso de construcción — Forja

Cómo se construyó este proyecto, con los hechos tomados de los transcripts de
las sesiones de Claude Code y de los archivos del proyecto. Los prompts
literales de cada sesión están en `docs/prompts-sesion.md`.

**Nota sobre las fuentes:** el repositorio git no llegó a inicializarse
(`git init` figura como primer paso en `docs/arquitectura.md`, pero no se
ejecutó), así que la evidencia primaria son los transcripts de sesión de
Claude Code, las marcas de tiempo de los archivos y el contenido del proyecto.
Nada de lo registrado aquí es reconstrucción de memoria: todo tiene respaldo
en esas fuentes.

## Metodología: dos fases

**Fase A — Arquitectura y planeación, en un chat de Claude.** Antes de
escribir código de producción se resolvió el diseño completo en conversación:
qué se construye (reto R3 de la Maratón de IA: solicitud informal de vendedor
→ cotización formal numerada), con qué restricción dominante (una persona,
~3 días), y qué se descarta y por qué. El resultado de esa fase quedó
materializado en tres artefactos:

- `docs/arquitectura.md` — las decisiones (Python sin framework, CSV, la
  carpeta `skill/` como unidad de despliegue, cálculo determinístico fuera
  del modelo), los descartes con su razón (FastAPI, SQLite, reportlab,
  aritmética en manos del LLM) y los riesgos con mitigación.
- [`docs/plan-forja.md`](plan-forja.md) — el plan de ejecución por fases,
  con prompts listos para copiar en Claude Code, cronograma, regla de
  recorte y riesgos con mitigación.
- El **scaffolding con contratos vacíos**: los scripts de `skill/scripts/`
  nacieron con docstrings de contrato y `raise NotImplementedError`
  etiquetado por fase (p. ej. `NotImplementedError("Fase 1-2")` en
  `datos_io.py`), tests guarda que indicaban en qué fase eliminarse, y
  placeholders que anunciaban su versión definitiva ("Workflow definitivo en
  la Fase 4" en `SKILL.md`).

**Fase B — Ejecución por fases, en Claude Code.** Cada fase se ejecutó con
uno o pocos prompts, en orden estricto ("vamos paso por paso" fue literal:
los pasos se enviaron uno a uno), con dos reglas operativas visibles en todos
los prompts: validar los datos o leer los contratos **antes** de tocar
código, y no cerrar ninguna fase sin `pytest` completo en verde. La
progresión de tests lo documenta: 16 → 29 → 34 → 40 → 49.

## Las siete fases

La numeración de esta sección corresponde a los bloques **como se
ejecutaron**. El plan original ([`plan-forja.md`](plan-forja.md)) numeraba
distinto — Fases 0 a 7, con una Fase 0 de puesta en marcha manual y una
Fase 6 de dashboard Artifact marcada como recortable, que no se ejecutó
(la regla de recorte del propio plan la señalaba como lo primero en caer).

### Fase 1 — Datos sintéticos (30 jul, 22:01–22:22)

Sesión propia, cinco pasos enviados uno a uno:

- `catalogo.csv`: 50 productos en 5 categorías (SIL/ESC/ARC/ILU/ACC),
  precios COP antes de IVA entre 15.000 y 2.450.000.
- `clientes.csv`: 50 clientes, NITs con formato colombiano, 20 ciudades,
  mezcla de agentes retenedores y condiciones de pago, notas operativas.
- `politicas_comerciales.md`: descuentos por volumen **por línea**
  (20–49: 5 %, 50+: 10 %), manual máximo 15 %, validez 15 días, tabla de
  entregas por ciudad.
- `solicitudes_prueba.md`: 10 mensajes estilo WhatsApp con casos deliberados
  (descuento del 20 %, retenedor con monto alto, solicitud sin cantidades,
  productos problemáticos — ver "Decisiones y correcciones" #4).
- Registro inicial: `registro/consecutivo.txt` y `registro/historial.csv`
  (estructura luego reemplazada — ver #1).

### Fase 2 — Set de pruebas completo y capa de datos

Ya sobre la estructura definitiva (`skill/datos/`, `demo/`): se agregaron las
solicitudes 11 y 12 (greca, ventilador, aire acondicionado — verificando que
nada parecido existiera en el catálogo) para probar la ruta `SkuNoEncontrado`.
Luego, validación de los tres archivos de datos (50 filas cada CSV, tipos
correctos, sin duplicados — cero inconsistencias) y la implementación de
`datos_io.py`: `cargar_catalogo()`, `cargar_clientes()`, `buscar_cliente()`
(búsqueda aproximada por razón social, sin tildes, con candidatos ordenados) y
`cargar_politicas()`. Resultado: 16 tests en verde.

### Fase 3 — Motor de cálculo

En tres pasos deliberados: **primero la especificación**
(`references/reglas_tributarias.md`: orden de cálculo en 6 pasos, redondeo
*half-up* a pesos, retefuente 2,5 % informativa con umbral estrictamente mayor
a 1.000.000, simplificaciones declaradas frente al régimen real), **luego el
código** (`calcular()` en `calculo.py`: núcleo puro sin I/O, todo `Decimal`,
`SkuNoEncontrado` en vez de estimar precios), **luego los tests**
(`test_calculo.py` con la aritmética esperada calculada a mano en comentarios,
para que un evaluador la audite sin ejecutar nada). Aquí se aplicó la
corrección del modelo de descuentos (ver #2). Resultado: 29 tests en verde.

### Fase 4 — Estado, documento y orquestador

Cuatro puntos en orden: `historial.py` (numeración `COT-2026-NNN` derivada del
máximo del historial, reinicio por año, estado siempre fuera de `skill/`);
`assets/plantilla.docx` (plantilla sobria con 18 marcadores, columna de
descuento por línea, bloque de retefuente condicional); `documento.py` (banda
"BORRADOR — REQUIERE APROBACIÓN" cuando aplica, `a_pdf()` que degrada al
`.docx` si LibreOffice no está); y `cotizar.py` como punto de entrada único:
JSON → datos → cálculo → historial → documento → JSON, con errores de negocio
tipados (`sku_no_encontrado`, `cliente_ambiguo`, `cliente_no_encontrado`) que
no consumen consecutivo, y `--solo-calculo` para previsualizar. Resultado: 49
tests en verde y prueba de humo del CLI.

### Fase 5 — SKILL.md y prueba de punta a punta

`SKILL.md` definitivo, escrito **después** de releer `cotizar.py`, las reglas
tributarias y las solicitudes de demo, para que el workflow documentara lo que
el código ya hace (no al revés). Description "pushy" para que la skill dispare
siempre, workflow obligatorio de 6 pasos, regla inquebrantable de SKUs y casos
especiales anclados a solicitudes concretas. Se probó el workflow completo con
las solicitudes 1, 3, 5, 11 y 2: la 1 y la 3 produjeron documento (la 3 como
borrador con aprobación pendiente), la 5 terminó correctamente en pregunta por
cantidades, la 11 en pregunta por productos que no se manejan, y la 2 cotizó
con sus alertas de stock.

### Fase 6 — Empaquetado

`forja.zip` con la carpeta `forja/` como raíz única (verificada con assert),
13 archivos, sin `__pycache__`. Detalle técnico registrado: se empaquetó con
`zipfile` de Python y no con `Compress-Archive`, que en Windows escribe
separadores `\` en las rutas internas y rompe al descomprimir en el contenedor
Linux de claude.ai.

### Fase 7 — Auditoría de salidas/ y cierre

Auditoría en 5 pasos del estado generado: mapeo del historial contra las
solicitudes, identificación de una cotización faltante (ver #3), verificación
de que los tests no tocaran `salidas/` real (ya usaban `tmp_path`; nada que
corregir), regeneración desde cero de las 4 cotizaciones (COT-2026-001 a 004,
1:1 con las solicitudes 1–4) y verificación del contenido real de cada
`.docx` — no de su existencia. Cierre: `forja.zip` regenerado, confirmando por
fechas que la auditoría solo tocó `salidas/` y el contenido de la skill quedó
idéntico.

## Decisiones y correcciones

Registro honesto de lo que cambió sobre la marcha y por qué.

### 1. Cambio de la estructura inicial

La sesión de datos creó `datos/` y `registro/` en la raíz del proyecto, con un
contador explícito `registro/consecutivo.txt` inicializado en "0". La fase de
arquitectura descartó esa organización dos veces:

- **`.claude/skills/forja/` → `skill/`.** La primera estructura de skill puso
  la fuente de verdad dentro de una carpeta oculta a cuatro niveles; una
  carpeta con punto comunica "configuración", no "código". Quedó `skill/`
  visible y de primer nivel como unidad de despliegue, con un junction de
  Windows (`mklink /J .claude\skills\forja skill`) para que Claude Code la
  auto-descubra: una sola fuente de verdad, dos consumidores.
- **`registro/consecutivo.txt` → numeración derivada.** El contador aparte se
  eliminó: el consecutivo se deriva del máximo en `historial.csv` (máximo +1),
  de modo que no existe un segundo estado que se pueda desincronizar. El
  estado vive en `salidas/`, fuera de la skill, porque el contenedor de
  claude.ai es efímero.

Además `solicitudes_prueba.md` salió de `datos/` hacia `demo/`: es material de
prueba y demo, no un dato que la skill necesite en despliegue.

### 2. Descuentos: de global a por línea

El contrato inicial de `calculo.py` (scaffolding) modelaba un único descuento
global en `ResultadoCalculo` (`descuento_pct`, `descuento_valor`);
`LineaCotizacion` no tenía campos de descuento. Pero las políticas escritas en
la Fase 1 ya definían el descuento por volumen "por línea de producto, no
acumulable entre ítems". Al implementar el motor se corrigió el modelo: el
prompt de la Fase 3 lo pide explícitamente ("Las políticas definen el
descuento por volumen POR LÍNEA") — `LineaCotizacion` se extendió con
`descuento_volumen_pct` y `subtotal_con_descuento`, cada línea evalúa su
propio tramo (30 sillas + 5 escritorios **no** suman 35 para subir de tramo),
y el descuento **manual** quedó como el único global, aplicado una sola vez
sobre la suma de líneas ya descontadas. La distinción quedó codificada en
`reglas_tributarias.md` (§1 y §2) y cubierta por tests
(`test_volumen_una_linea_si_y_otra_no`).

### 3. Auditoría de salidas/: la cotización faltante

La fase de punta a punta debía dejar generadas las cotizaciones de las
solicitudes 1 a 4. La auditoría encontró el historial con solo tres —
COT-2026-001 (solicitud 1), COT-2026-002 (solicitud 3) y COT-2026-003
(solicitud 2), con la numeración fuera del orden de las solicitudes — y
**faltaba la solicitud 4** (Fiduciaria Andina). El diagnóstico importó tanto
como el hallazgo: no falló ninguna ejecución de `cotizar.py` (el stock 0 de la
solicitud 2 no rompe — cotiza pleno con alertas — y la ruta de retefuente ya
había pasado el smoke test); la 4 sencillamente **no estaba en el conjunto que
se corrió** (1, 3, 5, 11 y 2 — de las cuales la 5 y la 11 terminan en pregunta,
no en documento). Fue una omisión, no un bug. Se verificó de paso que los
tests no contaminaran el estado real (ya usaban `tmp_path`), se borró el
historial y los `.docx`, y se regeneraron las cuatro cotizaciones limpias
(COT-2026-001 a 004, 1:1 con las solicitudes 1–4), verificando el contenido
real de cada documento: las dos alertas de stock en la 002, la banda
"REQUIERE APROBACIÓN" visible en la 003 y la retefuente informativa en la 004.

### 4. Casos de prueba: productos inexistentes vs. agotados

El pedido original de la Fase 1 incluía "2 solicitudes con productos que NO
existen en el catálogo", y así se generaron (sofá en L y mesa de centro;
greca y ventiladores). Vino entonces una redefinición del usuario: "los
productos inexistentes serían los que ya no tienen stock". Se acató: tres
productos del catálogo quedaron agotados (SIL-003 silla Monserrate, ESC-003
escritorio Macondo, ARC-008 caja fuerte digital) y las solicitudes 2 y 7 se
reescribieron para pedir productos reales sin inventario.

Eso dejó sin cubrir el caso original — y son **modos de fallo distintos con
comportamientos opuestos**:

- **Agotado** (existe en catálogo, stock 0): se cotiza a precio pleno con
  alerta y nota de reposición en el documento (política §6; test
  `test_sin_stock_alerta_pero_cotiza`). El sistema avanza e informa.
- **Inexistente** (no hay SKU): el sistema se detiene y pregunta si se
  reemplaza o se excluye — `SkuNoEncontrado`, la regla inquebrantable de
  `SKILL.md`: prohibido inventar precios o asumir equivalencias. El sistema
  bloquea y pregunta.

Por eso, al arrancar la implementación, el caso inexistente se **recuperó**
agregando las solicitudes 11 y 12 (greca, ventilador de techo, aire
acondicionado — verificando que nada parecido existiera en el catálogo).
Conservar ambos tipos no fue redundancia: si se hubieran fusionado, una de las
dos rutas del sistema habría quedado sin ejercitar. El set final prueba las
dos — solicitudes 2 y 7 (agotados), 11 y 12 (inexistentes).
