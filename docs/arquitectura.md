# Arquitectura: Forja — generador de documentos comerciales

## Qué entendí

Reto R3 de la Maratón de IA (Smart4AI + Ruta N). Un vendedor de pyme escribe una
solicitud informal — estilo WhatsApp — y el sistema devuelve una cotización
formal con cálculos correctos, personalizada por cliente y con numeración
consecutiva. Datos 100% sintéticos. Lo construye una persona en ~3 días
(31 jul – 2 ago), lo evalúa Smart Ranks de forma verificable y se presenta ante
las empresas madrinas el 6 de agosto. La restricción dominante es el calendario.

## Decisión

- **Lenguaje:** Python 3.10+ — runtime del contenedor de Claude y tu lenguaje. No hay razón para salir de ahí en 3 días.
- **Framework:** ninguno. Librería estándar + `python-docx`. Flujo lineal de cinco pasos; un framework solo agrega piezas que se pueden caer.
- **Persistencia:** archivos planos (CSV). Sin motor de base de datos: no hay concurrencia ni consultas, y un CSV se muestra en la demo abriéndolo.
- **Interfaz:** Claude — Proyecto + Skill en claude.ai. Sin GUI propia: la interfaz *es* el chat.
- **Empaquetado:** la carpeta `skill/` es la unidad de despliegue → ZIP → Customize → Skills en claude.ai.
- **Costo mensual de operación:** USD 0 adicionales (plan Pro ya pagado + equipo local).

## Por qué, y qué descarté

**Descartado FastAPI + SQLite + frontend propio.** Sería la respuesta en el mundo
real y es la equivocada aquí: el reto se evalúa sobre lo que enseñó el bootcamp
(Proyectos, Skills, Artifacts). Una API que el jurado debe levantar es fricción,
no mérito, y consumiría el sábado entero.

**Descartado SQLite.** Un usuario, sin escrituras concurrentes, catálogo de
decenas de filas. No aporta nada sobre CSV y sí quita: un `.db` binario no se
enseña en pantalla; un CSV sí.

**Descartado dejar el cálculo en manos del modelo.** La decisión central del
proyecto. Un LLM haciendo aritmética de IVA y retención falla de forma
silenciosa, y falla justo cuando hay público. El cálculo es Python
determinístico y testeado; el modelo entiende lenguaje informal, valida contra
catálogo y redacta.

**Descartado reportlab para el PDF.** Maquetar a mano cuesta horas.
`python-docx` sobre plantilla itera rápido, y LibreOffice (verificado presente
en el contenedor de Claude) convierte a PDF en una línea. Si faltara, el `.docx`
ya es entregable.

**Descartada la estructura anterior (`.claude/skills/forja/`).** Ponía la fuente
de verdad dentro de una carpeta oculta a cuatro niveles: una carpeta con punto
comunica "configuración", no "código". La skill ahora es `skill/`, visible y de
primer nivel. Para que Claude Code la auto-descubra durante el desarrollo, un
junction de Windows (no requiere admin): `mklink /J .claude\skills\forja skill`
— una sola fuente de verdad, dos consumidores.

## Estructura del proyecto

```
forja/
├── skill/                     ← LA UNIDAD DE DESPLIEGUE. Esto es lo que se zipea.
│   ├── SKILL.md               ← workflow + reglas inquebrantables (Fase 4)
│   ├── scripts/
│   │   ├── calculo.py         ← NÚCLEO. Puro: sin I/O, sin rutas, sin prints.
│   │   ├── datos_io.py        ← borde: carga catálogo/clientes/políticas
│   │   ├── documento.py       ← borde: renderiza .docx / convierte a PDF
│   │   ├── historial.py       ← borde: consecutivo derivado + registro
│   │   └── cotizar.py         ← punto de entrada ÚNICO y delgado
│   ├── datos/                 ← catálogo, clientes, políticas (sintéticos, Fase 1)
│   ├── assets/                ← plantilla.docx (Fase 3)
│   └── references/            ← reglas_tributarias.md (Fase 2)
├── tests/                     ← corre contra el núcleo: milisegundos, sin archivos
├── salidas/                   ← ESTADO: cotizaciones generadas + historial.csv
├── demo/                      ← solicitudes de prueba + guion del Demo Day
├── docs/                      ← este documento
├── pyproject.toml
└── README.md
```

Ocho entradas en la raíz, cada una con un rol que se lee sin explicación:
*lo que se despliega* (skill/), *lo que lo verifica* (tests/), *lo que produce*
(salidas/), *lo que se presenta* (demo/), *por qué es así* (docs/).

Tres separaciones y su razón:

1. **Núcleo (`calculo.py`) contra bordes.** El núcleo recibe diccionarios y
   devuelve diccionarios; no sabe qué es un CSV ni qué es Word. Por eso los
   tests corren sin montar nada y el motor es auditable ante un evaluador.
2. **Un solo punto de entrada (`cotizar.py`).** El SKILL.md invoca un comando,
   no encadena scripts pasándose JSON: menos superficie donde el modelo pueda
   dañar el intercambio en vivo.
3. **El estado vive fuera de la skill (`salidas/`).** El contenedor de claude.ai
   se reinicia entre sesiones; la carpeta de la skill es efímera. Además el
   consecutivo se deriva del historial (máximo + 1): no existe un contador
   aparte que se pueda desincronizar.

## Riesgos y cuándo esta decisión deja de servir

- **Aguanta:** un vendedor, cientos de SKUs, decenas de cotizaciones.
- **Caduca cuando:** dos vendedores coticen al tiempo — la numeración sobre CSV
  se rompe (dos procesos leen el mismo máximo) y toca servidor con
  transacciones. También cuando el catálogo cambie a diario y alguien deba
  administrarlo sin editar CSV a mano.
- **Riesgo #1:** `python-docx` ausente en el contenedor de tu cuenta claude.ai.
  Verificado presente en el entorno de Claude (1.2.0); confírmalo el viernes.
- **Riesgo #2:** la skill no dispara sola en claude.ai. Doble mitigación:
  description "pushy" + instrucciones del Proyecto que la invocan explícito.
- **Riesgo #3:** el brief oficial entrega sus datos o exige otro formato.
  Mitigado por la separación datos/lógica: se reemplaza `skill/datos/`, se
  corren los tests, la arquitectura no se toca.

## Primeros pasos

```bash
cd forja
python -m pytest -q                          # 4 tests en verde
python skill/scripts/cotizar.py --salidas salidas
pip install python-docx pytest
mklink /J .claude\skills\forja skill         # (Windows) auto-descubrimiento en Claude Code
git init && git add -A && git commit -m "scaffolding"
```

Luego la Fase 1 del plan (datos sintéticos). Nunca arrancar por el documento.
