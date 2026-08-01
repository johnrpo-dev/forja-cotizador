# Forja — generador de cotizaciones para pymes

Convierte una solicitud informal de WhatsApp ("me ayudas con una coti pa...")
en una cotización formal, correcta y trazable: documento `.docx` numerado,
cálculos verificables e historial consecutivo.

## El problema

En una pyme comercial, armar cada cotización a mano — buscar precios, aplicar
descuentos, liquidar IVA y retenciones, maquetar el documento, llevar el
consecutivo — consume horas y se presta a errores; mientras tanto el cliente
que "está afanado" se enfría y la oportunidad se pierde. Forja es la respuesta
al reto R3 de la Maratón de IA (Smart4AI + Ruta N): automatizar ese flujo para
una pyme colombiana ficticia, Distribuciones El Cedro SAS (mobiliario y
dotación de oficinas).

## Cómo funciona

El flujo tiene cinco pasos. (1) **Extracción**: del mensaje informal se
obtienen cliente, ítems con cantidades y condiciones; si falta una cantidad,
se pregunta — nunca se asume. (2) **Validación**: el cliente se resuelve
contra `clientes.csv` (acepta razón social aproximada) y cada ítem debe
corresponder a un SKU exacto de `catalogo.csv`. (3) **Cálculo**: un script
determinístico aplica descuentos por volumen por línea, descuento manual
global, IVA 19 % y retención en la fuente informativa, con aritmética
`Decimal` y redondeo a pesos. (4) **Documento**: se genera el `.docx` desde
una plantilla, con alertas visibles (banda de borrador si el descuento excede
el tope, nota de reposición si no hay stock). (5) **Registro**: la cotización
queda numerada (`COT-2026-NNN`, derivada del máximo del historial) y asentada
en `historial.csv`.

## Decisión de diseño central

**El modelo entiende y redacta; la aritmética la hace código Python
determinístico y testeado.** Un LLM haciendo cálculos de IVA y retención falla
de forma silenciosa, y falla justo cuando hay público: por eso toda cifra sale
de `calculo.py`, un núcleo puro (sin I/O) especificado en
`skill/references/reglas_tributarias.md` y cubierto por tests cuyos valores
esperados están calculados a mano en comentarios, auditables sin ejecutar
nada. La misma lógica aplica a los datos: un producto que no está en el
catálogo se pregunta, nunca se inventa — el motor lanza `SkuNoEncontrado` en
vez de estimar un precio, y la skill tiene prohibido asumir equivalencias.

## Ejemplo real

Entrada (solicitud 1 de `demo/solicitudes_prueba.md`):

> [8:02 a.m.] Buenas! qué más pues. Me ayudas con una coti pa Café y Punto
> de Medellín, el señor Andrés Mora. Necesita 30 sillas rimax apilables pa
> un evento que tienen en agosto. Es de contado como siempre. Me la mandas
> hoy porfa que el man está afanado 🙏

Resultado: **COT-2026-001** para Café y Punto SAS — 30 × silla rimax apilable
(SIL-006) a $68.000, con 5 % de descuento por volumen en la línea: subtotal
$1.938.000, IVA $368.220, **total $2.306.220**, entrega en Medellín en 3 días
hábiles, documento en `salidas/COT-2026-001.docx` y fila en
`salidas/historial.csv`.

El set de prueba (12 solicitudes) cubre además los casos especiales: producto
con **stock agotado** (se cotiza a precio pleno con alerta y nota de
reposición), **descuento sobre el máximo** (se calcula igual pero el documento
sale como borrador que requiere aprobación de gerencia), **retención
informativa** para clientes agentes retenedores (se muestra lo que el cliente
retendrá al pagar, sin restarse del total) y **producto inexistente** (el
sistema pregunta si se reemplaza o se excluye).

![Interacción de Forja ante productos inexistentes](docs/img/COT_Greca.png)

## Estructura del proyecto

```
forja/
├── skill/          ← la unidad de despliegue: esto es lo que se sube a claude.ai
│   ├── SKILL.md    ← workflow obligatorio y reglas de la skill
│   ├── scripts/    ← calculo.py (núcleo), datos_io, documento, historial, cotizar (CLI)
│   ├── datos/      ← catálogo, clientes y políticas comerciales (sintéticos)
│   ├── assets/     ← plantilla.docx
│   └── references/ ← reglas_tributarias.md (especificación del motor)
├── tests/          ← 49 tests sobre el núcleo y los bordes; nunca tocan salidas/
├── salidas/        ← estado: cotizaciones generadas + historial.csv
├── demo/           ← 12 solicitudes de prueba estilo WhatsApp
└── docs/           ← arquitectura, plan y registro del proceso
```

## Cómo ejecutarlo

Requiere Python 3.10+.

```bash
pip install python-docx pytest
python -m pytest -q        # 49 passed
```

Corrida de ejemplo (la solicitud 1, sin consumir consecutivo ni generar
documento gracias a `--solo-calculo`):

```bash
echo '{"cliente": "Cafe y Punto", "items": [{"sku": "SIL-006", "cantidad": 30}]}' \
  | python skill/scripts/cotizar.py --solo-calculo --salidas salidas
```

Sin `--solo-calculo`, la misma entrada genera el `.docx` en `salidas/` y
registra la cotización en el historial.

## Uso como skill en claude.ai

Comprimir la carpeta `skill/` renombrada a `forja` (la carpeta como raíz del
ZIP, no los archivos sueltos) y subir el ZIP en Customize → Skills → + →
Create skill. Requiere "Code execution and file creation" activo en Settings →
Capabilities. Una vez instalada, pegar el mensaje de WhatsApp en el chat
basta: la skill extrae, valida, ejecuta `cotizar.py` y entrega el documento.

### Desarrollo (Windows)

Para que Claude Code auto-descubra la skill durante el desarrollo sin duplicar
la carpeta, crear un junction (no requiere permisos de administrador):

```bat
mkdir .claude\skills
mklink /J .claude\skills\forja skill
```

## Documentación

- [`docs/arquitectura.md`](docs/arquitectura.md) — las decisiones y descartes:
  por qué está construido así y cuándo esta arquitectura deja de servir.
- [`docs/proceso.md`](docs/proceso.md) — cómo se construyó: metodología de dos
  fases, las siete fases de ejecución y las decisiones y correcciones del
  camino.
- [`docs/plan-forja.md`](docs/plan-forja.md) — el plan por fases producido en
  la etapa de arquitectura y planeación.
- [`docs/prompts-sesion.md`](docs/prompts-sesion.md) — registro cronológico de
  los prompts de construcción, verbatim, con lo que se hizo en cada uno.

## Nota

Todos los datos son 100 % sintéticos: la empresa, los clientes, los NITs, los
precios y las solicitudes son ficticios. Las reglas tributarias simplifican el
régimen colombiano real de forma declarada (ver
`skill/references/reglas_tributarias.md` §5).
