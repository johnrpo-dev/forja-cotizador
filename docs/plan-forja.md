# Plan de ejecución — Reto Forja (Maratón de IA, Smart4AI + Ruta N) · v2

**Deadline real: domingo 2 de agosto en la noche.** Entrega oficial: lunes 3 de agosto.

> v2: alineado con el scaffolding final (`forja-scaffolding.zip`). La skill vive
> en `skill/` visible en la raíz; punto de entrada único `cotizar.py`; el
> consecutivo se deriva del historial (no existe `consecutivo.txt`).

---

## 1. Arquitectura de la solución

**Dónde se construye:** Claude Code (velocidad, scripts, tests).
**Dónde vive y se demuestra:** claude.ai — Proyecto + Skill subida + Artifact.

Razón: Smart Ranks y el jurado evalúan sobre lo que enseñó el bootcamp
(Proyectos, Skills, Artifacts). Claude Code es tu fábrica; claude.ai es tu
vitrina. La carpeta `skill/` es la unidad de despliegue: se desarrolla ahí y se
comprime desde ahí, sin ajustar rutas.

| # | Componente | Vive en | Función |
|---|-----------|---------|---------|
| 1 | Datos sintéticos (catálogo, clientes, políticas) | `skill/datos/` | Fuente única de verdad de precios |
| 2 | Skill `forja` | `skill/` → ZIP → claude.ai | Workflow + cálculo determinístico + plantilla |
| 3 | Proyecto "Forja — Cotizador" | claude.ai | Contexto permanente + instrucciones |
| 4 | Artifact dashboard | claude.ai | Capa visual: historial y totales (recortable) |

**Principio rector (tu diferencial):** el LLM nunca calcula ni inventa precios.
Extrae, valida contra catálogo, delega la aritmética a `calculo.py` y redacta
solo el texto comercial. Ítem fuera de catálogo → pregunta, jamás inventa.

---

## 2. Estructura (la del scaffolding que ya tienes)

```
forja/
├── skill/                     ← LA UNIDAD DE DESPLIEGUE (esto se zipea)
│   ├── SKILL.md               ← placeholder; se redacta completo en Fase 4
│   ├── scripts/
│   │   ├── calculo.py         ← NÚCLEO puro (Fase 2)
│   │   ├── datos_io.py        ← borde: carga CSVs (Fase 1-2)
│   │   ├── documento.py       ← borde: .docx → PDF (Fase 3)
│   │   ├── historial.py       ← borde: consecutivo derivado + registro (Fase 3)
│   │   └── cotizar.py         ← punto de entrada ÚNICO, ya ejecuta
│   ├── datos/                 ← Fase 1
│   ├── assets/                ← plantilla.docx (Fase 3)
│   └── references/            ← reglas_tributarias.md (Fase 2)
├── tests/test_calculo.py      ← 4 guardas de scaffolding en verde; crecen en Fase 2
├── salidas/                   ← documentos generados + historial.csv (ESTADO)
├── demo/                      ← solicitudes de prueba + guion
└── docs/arquitectura.md       ← decisiones y sus porqués
```

---

## 3. Flujo end-to-end

```
Solicitud informal ("hazme cotización pa' don Jorge: 40 sillas, 10% dcto")
   → [LLM] extrae JSON {cliente, items[], condiciones}
   → [LLM] valida contra skill/datos/catalogo.csv
        no existe → PREGUNTA (nunca inventa)
   → [cotizar.py] orquesta: calculo.py → historial.py → documento.py
        subtotal, descuento, IVA 19%, retefuente · COT-2026-NNN · .docx/.pdf
   → [LLM] redacta alcance y condiciones personalizadas
   → registro en salidas/historial.csv → alimenta el Artifact
```

---

## 4. Reglas de cálculo (definirlas ANTES de codear)

Datos sintéticos = tú defines las reglas, pero deben ser realistas y estar
**documentadas** en `skill/references/reglas_tributarias.md`. El jurado evalúa
correctitud *dentro de reglas declaradas*:

- Precios de catálogo **antes de IVA**, en COP. Redondeo a pesos completos.
- Descuento por volumen (≥20 und: 5%, ≥50: 10%). Descuento manual máx. 15%;
  por encima → cotización marcada "requiere aprobación".
- IVA 19% sobre subtotal con descuento.
- Retefuente compras 2.5% — solo si el cliente es agente retenedor y la base
  supera $1.000.000 COP. Se **informa** en el documento, no se resta del total.

---

## 5. Fases con prompts para Claude Code (copy-paste)

### Fase 0 — Puesta en marcha (hoy, 15 min, manual)

1. Descomprime `forja-scaffolding.zip` donde trabajas.
2. `pip install python-docx pytest`
3. `python -m pytest -q` → 4 tests en verde.
4. Auto-descubrimiento de la skill en Claude Code (Windows, sin admin):
   `mkdir .claude\skills` y `mklink /J .claude\skills\forja skill`
5. Abre Claude Code en la carpeta `forja/`.

### Fase 1 — Datos sintéticos (viernes, ~45 min)

```
Lee docs/arquitectura.md para entender el proyecto. Luego genera datos 100%
sintéticos para la pyme ficticia "Distribuciones El Cedro SAS" (mobiliario y
dotación para oficinas):

1. skill/datos/catalogo.csv — 50 productos: sku, nombre, categoria, unidad,
   precio_unitario_cop (antes de IVA, entre 15.000 y 2.500.000), stock.
   Categorías: sillas, escritorios, archivadores, iluminación, accesorios.

2. skill/datos/clientes.csv — 12 clientes: nit, razon_social, contacto,
   ciudad, agente_retenedor (si/no), condicion_pago (contado/30 dias), notas.
   Ciudades colombianas variadas.

3. skill/datos/politicas_comerciales.md — descuentos por volumen (>=20 und:
   5%, >=50: 10%), descuento manual máximo 15% (encima requiere aprobación),
   validez 15 días, tiempos de entrega por ciudad.

4. demo/solicitudes_prueba.md — 10 solicitudes de cotización escritas como
   mensajes informales de WhatsApp de un vendedor colombiano. Incluye
   deliberadamente: 2 con productos que NO existen en el catálogo, 1 con
   descuento del 20% (excede el máximo), 1 para cliente agente retenedor con
   monto alto, 1 ambigua (sin cantidades).

5. Implementa skill/scripts/datos_io.py (las tres funciones que hoy lanzan
   NotImplementedError) para cargar esos archivos, con precios y umbrales
   como Decimal. Agrega en tests/ pruebas de carga y déjalas en verde.

No toques todavía calculo.py.
```

### Fase 2 — Motor de cálculo + tests (viernes, ~1 h)

```
Implementa la función calcular() de skill/scripts/calculo.py respetando su
contrato actual (recibe estructuras ya cargadas, devuelve ResultadoCalculo,
lanza SkuNoEncontrado si un ítem no está en catálogo — NUNCA estimes precios).
El núcleo debe seguir puro: sin leer archivos, sin imprimir, sin rutas.

Reglas (documéntalas primero en skill/references/reglas_tributarias.md):
- Subtotal por línea y global desde precios del catálogo.
- Descuento por volumen según políticas; descuento manual: si >15%,
  requiere_aprobacion=True y alerta.
- IVA 19% sobre la base con descuento.
- Retefuente compras 2.5% solo si cliente agente_retenedor y base >
  1.000.000 COP; va en retefuente_informativa, no se resta del total.
- Redondeo a pesos completos con Decimal.

En tests/test_calculo.py: elimina la guarda test_calcular_existe_y_esta_pendiente
y agrega casos: cotización simple, descuento por volumen, descuento manual
excedido, retefuente aplicada, retefuente NO aplicada por base insuficiente,
SKU inexistente, redondeo. Ejecuta pytest y no termines hasta verde total.
```

### Fase 3 — Documento, historial y orquestación (sábado AM, ~2 h)

```
Implementa en este orden:

1. skill/scripts/historial.py — siguiente_numero() deriva COT-2026-NNN del
   máximo en salidas/historial.csv (si no existe, arranca en 001) y
   registrar() agrega la fila creando encabezados si hace falta. El estado
   SIEMPRE va en la carpeta que se pase por --salidas, nunca dentro de skill/.

2. skill/assets/plantilla.docx — genera con python-docx una plantilla sobria:
   encabezado de "Distribuciones El Cedro SAS" (NIT ficticio), espacio para
   número y fecha, datos del cliente, tabla de ítems, bloque de totales,
   alcance, condiciones, validez 15 días, línea de firma.

3. skill/scripts/documento.py — generar_docx() rellena la plantilla con el
   ResultadoCalculo y los textos que pase Claude; si requiere_aprobacion,
   inserta banda visible "BORRADOR — REQUIERE APROBACIÓN". a_pdf() convierte
   con LibreOffice si está disponible; si no, devuelve el .docx sin fallar.

4. skill/scripts/cotizar.py — conecta todo: entrada JSON (archivo o stdin) →
   datos_io → calculo → historial → documento → JSON por stdout con totales,
   alertas y ruta del documento. --solo-calculo omite el documento.

Genera 2 cotizaciones reales desde demo/solicitudes_prueba.md, muéstrame las
rutas, y agrega un test de integración del consecutivo (dos cotizaciones
seguidas → 001 y 002).
```

### Fase 4 — SKILL.md definitivo (sábado PM, ~1.5 h)

```
Reemplaza el placeholder skill/SKILL.md por la versión definitiva.

Frontmatter:
- name: forja
- description: redáctala "pushy": debe activarse cuando el usuario pida
  cotizar, hacer una propuesta o ficha técnica, mencione clientes/productos/
  precios, o pegue un mensaje informal pidiendo precios — aunque no use la
  palabra "cotización".

Cuerpo (máx ~200 líneas), workflow obligatorio:
1. Extraer cliente, ítems con cantidades y condiciones. Si falta una
   cantidad, PREGUNTAR antes de continuar.
2. Validar cliente e ítems contra skill/datos/. Regla inquebrantable: producto
   fuera de catálogo → informar y preguntar (reemplazo o cotización aparte).
   PROHIBIDO inventar precios o asumir equivalencias.
3. Ejecutar scripts/cotizar.py con el JSON extraído. PROHIBIDO hacer
   aritmética manual o "verificar" recalculando: el script es la única
   fuente de cálculo.
4. Redactar alcance y condiciones personalizadas usando las notas del
   cliente y las políticas.
5. Presentar: totales + ruta del documento + alertas (aprobación requerida,
   retención informada, ítems excluidos).

Sección "Casos especiales": descuento excedido, cliente no registrado (pedir
datos mínimos), solicitud ambigua.

Luego pruébala tú mismo con 4 solicitudes de demo/solicitudes_prueba.md: la
simple, las 2 de productos inexistentes y la del 20% de descuento. Muéstrame
los resultados.
```

### Fase 5 — Empaquetar y subir a claude.ai (sábado PM, ~30 min)

```
Empaqueta la skill: copia skill/ a un temporal renombrada como "forja" (debe
coincidir con el name del frontmatter) y comprímela como forja.zip con esa
carpeta como raíz del ZIP — ni archivos sueltos ni carpeta contenedora extra.
Verifica listando el contenido del ZIP.
```

Manual en claude.ai:
1. Settings → Capabilities: activa **Code execution and file creation**.
2. Customize → Skills → **+** → **Create skill** → sube `forja.zip` → toggle ON.
3. Proyecto "Forja — Cotizador El Cedro" con instrucciones: *"Eres el asistente
   comercial de Distribuciones El Cedro SAS. Para toda solicitud de cotización
   o propuesta usa la skill forja y sigue su workflow sin excepciones. Los
   documentos e historial se guardan en la carpeta de salidas de la sesión."*
4. Prueba las mismas 4 solicitudes de la Fase 4. El comportamiento debe ser
   idéntico al de Claude Code. **Verifica ahí mismo que python-docx esté
   disponible en el contenedor** (riesgo #1 de docs/arquitectura.md).

### Fase 6 — Artifact dashboard (sábado noche / domingo AM, ~1 h) — RECORTABLE

En el chat del Proyecto en claude.ai:

```
Con el contenido de historial.csv que te pego, crea un Artifact (React)
"Panel Comercial — El Cedro": tarjetas con total cotizado del mes, número de
cotizaciones y ticket promedio; tabla del historial con badge de color por
estado; gráfico de barras de cotizaciones por semana. Estilo sobrio, apto
para gerencia. Debe permitir pegar un CSV actualizado para refrescar.
```

### Fase 7 — Pruebas finales y demo (domingo, ~3 h)

```
Corre el flujo completo con las 10 solicitudes de demo/solicitudes_prueba.md.
Por cada una registra: qué se extrajo, qué se validó, resultado del cálculo,
documento generado o pregunta hecha. Genera demo/resumen_pruebas.md con la
tabla de resultados y toda inconsistencia encontrada.
```

Guion de demo (3 casos, en este orden):
1. **La feliz**: mensaje informal → cotización en segundos, totales que
   cuadran centavo a centavo.
2. **El control**: producto inexistente → el sistema pregunta en vez de
   inventar. *El momento diferenciador: dilo explícito.*
3. **La trazabilidad**: descuento del 20% → "BORRADOR — REQUIERE APROBACIÓN"
   + historial consecutivo en el dashboard.

Cierre del pitch: "La IA redacta y entiende; la aritmética es código
determinístico y testeado. Por eso esta cotización se puede firmar."

---

## 6. Cronograma

| Cuándo | Qué | Horas |
|--------|-----|-------|
| **Jue 30, 9 p.m.** | Lanzamiento oficial. Verificar: ¿entregan ellos los datos sintéticos? ¿formato de entrega en Smart Ranks? Ajustar plan | 1 |
| **Vie 31 (noche)** | Fases 0, 1 y 2 | 2.5–3.5 |
| **Sáb 1** | Fases 3, 4 y 5 | 5–6 |
| **Sáb noche / Dom AM** | Fase 6 (recortable) | 1 |
| **Dom 2** | Fase 7 + video de respaldo (2 min) + entrega | 3–4 |

**Regla de recorte:** si el sábado te atrasas, cae primero la Fase 6. Jamás se
recortan: tests del cálculo y los casos de control de la demo.

---

## 7. Riesgos y mitigaciones

- **El brief contradice el plan** → ajustar el jueves mismo, antes de codear.
- **El bootcamp entrega sus datos sintéticos** → reemplazas `skill/datos/` y
  corres los tests; la arquitectura no cambia.
- **La skill no dispara en claude.ai** → description más "pushy" + las
  instrucciones del Proyecto ya la invocan explícitamente.
- **python-docx ausente en tu contenedor de claude.ai** → verificar en Fase 5,
  no el domingo. Plan B: la plantilla se rellena vía plantillas de texto y
  LibreOffice.
- **Demo en vivo falla** → video de 2 minutos grabado el domingo como respaldo.
