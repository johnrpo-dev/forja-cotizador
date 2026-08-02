---
name: forja
description: >
  Genera cotizaciones, fichas técnicas, propuestas y documentos comerciales
  de Distribuciones El Cedro SAS (mobiliario y dotación de oficinas, pymes
  Colombia). ÚSALA SIEMPRE que el usuario pida cotizar o "pasar precios",
  solicite una propuesta o documento comercial, mencione clientes,
  productos, cantidades, descuentos o disponibilidad, o pegue un mensaje
  informal de WhatsApp pidiendo precios — aunque nunca aparezca la palabra
  "cotización". ÚSALA IGUAL cuando no se hable de plata: pedir una ficha
  técnica o la información de un producto, preguntar por especificaciones,
  medidas, materiales, categoría, unidad de venta o existencias, o soltar
  un "qué trae", "de qué material es" o "qué medidas tiene" sobre una
  referencia del catálogo (ARC-007, SIL-008…) es ficha técnica, y la ficha
  también es esta skill. Preguntar por un producto sin nombrar precios NO
  la desactiva. Ante la duda de si aplica, aplica.
---

# Forja — generador de documentos comerciales

Convierte una solicitud informal ("me ayudas con una coti pa...") en un
documento formal, con cálculos hechos por script determinístico. Tu papel:
entender el lenguaje, validar contra los datos, redactar. El papel del
script: TODA la aritmética.

Genera dos documentos:

| Documento | Responde a | Consume consecutivo |
|---|---|---|
| **Cotización** | cuánto vale, con cantidades y descuentos | Sí, `COT-AAAA-NNN` |
| **Ficha técnica** | qué es el producto: specs, precio de lista, disponibilidad | No |

## Datos y herramientas

| Recurso | Para qué |
|---|---|
| `datos/catalogo.csv` | SKUs, precios (COP antes de IVA), stock |
| `datos/clientes.csv` | NIT, contacto, ciudad, agente retenedor, condición de pago, notas |
| `datos/politicas_comerciales.md` | Descuentos, validez, entregas por ciudad |
| `references/reglas_tributarias.md` | Cómo calcula el motor (IVA, retefuente, redondeo) |
| `scripts/cotizar.py` | ÚNICO punto de cálculo y generación de documento (ambos modos) |

El estado (documentos e historial) SIEMPRE va fuera de la carpeta de la
skill: pasa `--salidas` apuntando a una carpeta persistente del proyecto.

## Workflow obligatorio

### 1. Decidir el tipo de documento

Antes de extraer nada, mirar **qué pregunta hace el usuario**:

| Si pide… | Documento |
|---|---|
| precios totales, cantidades, descuentos, "cuánto sale", "pásame una coti" | Cotización — pasos 2 a 7 |
| ficha técnica, especificaciones, medidas, materiales, "información del producto", "qué trae", disponibilidad de una referencia | Ficha técnica — ver sección propia abajo |

La señal es **si hay cantidades y un cliente que compra**. "¿Qué medidas tiene
el estante ARC-007?" es una ficha, no una cotización de 1 unidad: emitir una
cotización numerada por una consulta de producto ensucia el consecutivo con
documentos que nadie pidió.

Si la solicitud pide las dos cosas ("mándame la ficha y me cotizas 20"),
se generan ambos documentos: primero la ficha, después la cotización.

### 2. Extraer

De la solicitud: cliente, ítems con **cantidades**, condiciones (pago,
entrega, urgencia) y descuento pedido. Si a algún ítem le falta la cantidad
("unas lámparas", "sillas pal lobby"), **PREGUNTAR antes de continuar** —
nunca asumir una cantidad. Ejemplo real: la solicitud 5 de
`demo/solicitudes_prueba.md` no trae cantidades; la respuesta correcta es
preguntar cuántas sillas y cuántas lámparas, no cotizar "1".

Lo mismo aplica al descuento: si se pide **sin cifra** ("algún descuentico",
"mira qué se puede hacer" — solicitud 10 de `demo/solicitudes_prueba.md`),
**PREGUNTAR qué porcentaje autoriza el vendedor**, indicando que hasta 15%
no requiere aprobación y que por encima pasa por gerencia comercial. El
porcentaje es una decisión comercial del vendedor: el sistema nunca lo
elige por su cuenta.

### 3. Identificar el cliente

Contra `datos/clientes.csv`, con `datos_io.buscar_cliente(texto)`, que acepta
razón social aproximada (sin tildes) y devuelve pares `(puntaje, cliente)`
ordenados. **Solo el NIT exacto o un puntaje ≥ 0,85 identifican.** Un parecido
moderado no es una identificación: las razones sociales colombianas comparten
demasiado vocabulario, y "Constructora Sierra Alta SAS" puntúa 0,79 contra
"Constructora Altamira SAS" siendo otra empresa.

El script resuelve lo mismo y devuelve tres respuestas posibles:

| Respuesta | Qué significa | Qué hacer |
|---|---|---|
| cliente resuelto | NIT exacto o parecido fuerte y único | seguir |
| `cliente_ambiguo` | hay parecidos, ninguno concluyente (banda 0,60–0,85) | mostrar los candidatos **con su puntaje** y preguntar cuál es; si ninguno lo es, es cliente nuevo |
| `cliente_no_encontrado` | nada se le parece | preguntar; casi siempre es cliente nuevo |

`cliente_ambiguo` **no** significa "elegir el mejor". Ni el script ni el modelo
eligen: una cotización lleva NIT, ciudad, condición de pago y régimen
tributario del cliente, y equivocarse de empresa los falsea todos a la vez.

Lee las **notas** del cliente: casi siempre contienen una restricción de
entrega o facturación que va en la cotización.

**Cliente nuevo (no está en `clientes.csv`).** Pedir razón social, NIT, ciudad
y contacto, y **preguntar si es agente retenedor** — ese dato no se supone.
Después, mandar `cliente` como objeto en vez de texto:

```json
"cliente": {
  "nit": "901999888-1", "razon_social": "Inversiones La Floresta SAS",
  "contacto": "Ana Ruiz", "ciudad": "Bogotá",
  "agente_retenedor": false, "notas": "opcional"
}
```

El script **no lo da de alta** en `clientes.csv`: el cliente vale para esa
cotización y el registro formal lo tramita cartera. Fuerza además condición de
pago **contado** (políticas §5, primera compra), ignorando cualquier crédito
que traiga la petición, y devuelve una alerta que hay que transmitir. Si falta
un dato responde `cliente_nuevo_incompleto` (con la lista de campos), y si no
se declaró la retención, `retencion_no_declarada` — en ambos casos se pregunta,
no se completa de memoria. Si el NIT ya existe, responde `cliente_ya_registrado`:
no era un cliente nuevo, y usar los datos dictados habría pisado la condición
de pago y las notas del real.

### 4. Mapear ítems a SKUs

Cada ítem de la solicitud debe corresponder a un SKU exacto de
`datos/catalogo.csv`.

**REGLA INQUEBRANTABLE:** si un producto no tiene SKU correspondiente
(ej.: greca, ventilador, aire acondicionado — solicitudes 11 y 12 de
`demo/solicitudes_prueba.md`), se **informa al usuario y se pregunta** si lo
reemplaza por algo del catálogo o lo excluye de la cotización. PROHIBIDO
inventar precios, asumir equivalencias o elegir "el más parecido" sin
confirmar. El script refuerza esto lanzando `sku_no_encontrado`, pero la
pregunta debe hacerse ANTES de ejecutar, al mapear. Sí es válido proponer:
"no manejamos greca; ¿la excluyo o preguntas al cliente?" — proponer
opciones no es asumirlas.

### 5. Calcular con el script — nunca a mano

Armar el JSON y ejecutar:

```bash
python scripts/cotizar.py --entrada peticion.json --salidas <carpeta_estado>
```

```json
{
  "cliente": "nit o razón social aproximada",
  "items": [{"sku": "SIL-006", "cantidad": 30}],
  "descuento_manual_pct": "0.20",
  "alcance": "opcional", "observaciones": "opcional",
  "asesor": "opcional", "fecha": "AAAA-MM-DD opcional"
}
```

`cliente` admite texto (se resuelve contra `clientes.csv`) u objeto, que es la
forma de cotizarle a un cliente nuevo — ver paso 3.

`--solo-calculo` da un borrador sin consumir consecutivo ni generar
documento — útil para previsualizar antes de confirmar con el usuario.

**PROHIBIDO** hacer aritmética manual, "verificar" recalculando o corregir
un número del script: es la única fuente de cálculo (Decimal, redondeo a
pesos, reglas de `references/reglas_tributarias.md`). Si un total parece
raro, se revisa la ENTRADA, no se ajusta la salida.

**Las alertas del JSON de salida se transmiten al usuario SIEMPRE** — stock
insuficiente, requiere aprobación, retención informativa. Nunca se omiten ni
se suavizan.

### 6. Redactar alcance y condiciones

Personalizar con: las **notas del cliente** (restricciones de recibo,
horarios, requisitos de facturación), el **tiempo de entrega según ciudad**
(tabla de `politicas_comerciales.md` §6 — el script ya lo pone en el
documento) y la condición de pago. El descuento manual siempre con su
justificación en observaciones.

### 7. Presentar

Al usuario: resumen de totales (subtotal, descuentos, IVA, total), número de
cotización, **ruta del documento generado** y **todas las alertas**. Si hubo
retención informativa, explicar que es el valor que el cliente retendrá al
pagar y que NO se resta del total cotizado.

## Ficha técnica de producto

Para consultas de producto, no de precio. Una ficha por SKU, **sin consumir
consecutivo y sin escribir en el historial**: es informativa y no compromete
valores en firme.

```bash
python scripts/cotizar.py --modo ficha --entrada peticion.json --salidas <carpeta_estado>
```

```json
{
  "skus": ["ARC-007", "SIL-008"],
  "ciudad": "Medellín",
  "cliente": "opcional, aporta la ciudad",
  "observaciones": "opcional", "asesor": "opcional", "fecha": "AAAA-MM-DD opcional"
}
```

No hace falta cliente: una ficha se puede pedir sin destinatario. Si se pasa
`ciudad` (o un `cliente` que la aporte, ya sea texto u objeto), el tiempo de
entrega se calcula para esa ciudad; sin ella la ficha remite a logística en vez
de suponer un destino. Un `cliente` en texto que no se resuelva con certeza
tampoco aporta ciudad: mejor remitir a logística que heredar el destino —
y el flete — de una empresa parecida.

**Misma REGLA INQUEBRANTABLE del paso 4:** un SKU que no está en el catálogo
se pregunta, nunca se inventa. El script devuelve `sku_no_encontrado` con la
lista de códigos desconocidos y **no genera ninguna ficha**, ni siquiera las
de los SKUs válidos, para que la respuesta salga completa o no salga.

**Las especificaciones se leen del catálogo, jamás se completan de memoria.**
Dimensiones, materiales y características se extraen del nombre del producto;
lo que el nombre no dice sale como "No registrada en catálogo" y el JSON
devuelve una alerta. Ese hueco es información válida y se transmite tal cual:
si el usuario necesita el dato, se confirma con el proveedor. Inventar el
material de una silla es tan grave como inventar su precio.

Al presentar: nombre y SKU, especificaciones encontradas, **precio de lista
antes de IVA** (aclarando que no incluye descuentos por volumen ni IVA),
disponibilidad, ruta del documento y todas las alertas. Si el usuario después
quiere valores en firme, ofrecer emitir la cotización.

## Casos especiales

- **Descuento manual > 15%:** el script cotiza igual pero marca
  `requiere_aprobacion` y el documento sale con banda "BORRADOR — REQUIERE
  APROBACIÓN". Decirle al usuario que necesita visto bueno de gerencia
  comercial antes de enviarla al cliente (solicitud 3 es este caso).
- **Ítem con stock 0 o insuficiente:** se cotiza a precio pleno con alerta;
  la nota de reposición queda en observaciones del documento (política §6).
  Transmitir la alerta y sugerir confirmar fecha de reposición.
- **Cliente nuevo (no está en clientes.csv):** pedir razón social, NIT,
  ciudad, contacto y **si es agente retenedor**; mandarlo como objeto en
  `cliente` (paso 3). La condición de pago no se pregunta: la primera compra
  de un cliente nuevo es de contado y el script la fuerza. Avisar que el
  cliente queda sin registrar y que el alta la tramita cartera.
- **Cliente parecido pero no idéntico:** `cliente_ambiguo` se resuelve
  preguntando, jamás quedándose con el de mayor puntaje. Que haya sobrado un
  solo candidato no lo confirma: puede ser un cliente nuevo que se parece a
  uno viejo.
- **Solicitud ambigua sin cantidades:** preguntar. Una cotización con
  cantidades inventadas es peor que una pregunta de más.
- **Descuento pedido sin cifra:** preguntar al vendedor qué porcentaje
  autoriza (hasta 15% sin aprobación; superior requiere gerencia). Mismo
  principio que las cantidades: el sistema no decide descuentos por su
  cuenta (solicitud 10 es este caso).
- **Producto que no manejamos:** ver regla inquebrantable del paso 4 —
  informar, preguntar, jamás inventar.
- **Consulta de producto sin intención de compra** ("¿qué medidas tiene…?",
  "¿de qué material es…?"): es una ficha técnica, no una cotización. No gastar
  consecutivo en resolver una duda.
- **Ficha de un producto con specs incompletas:** se entrega igual, con los
  campos ausentes marcados como no registrados. Nunca rellenarlos con datos
  plausibles: un dato inventado en una ficha termina en un pliego de licitación.
