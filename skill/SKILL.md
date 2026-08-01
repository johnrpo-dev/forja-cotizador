---
name: forja
description: >
  Genera cotizaciones, propuestas y documentos comerciales de Distribuciones
  El Cedro SAS (mobiliario y dotación de oficinas, pymes Colombia). ÚSALA
  SIEMPRE que el usuario pida cotizar o "pasar precios", solicite una
  propuesta, ficha técnica o documento comercial, mencione clientes,
  productos, cantidades, descuentos o disponibilidad, o pegue un mensaje
  informal de WhatsApp pidiendo precios — aunque nunca aparezca la palabra
  "cotización". Ante la duda de si aplica, aplica.
---

# Forja — generador de cotizaciones

Convierte una solicitud informal ("me ayudas con una coti pa...") en una
cotización formal numerada, con cálculos hechos por script determinístico.
Tu papel: entender el lenguaje, validar contra los datos, redactar. El papel
del script: TODA la aritmética.

## Datos y herramientas

| Recurso | Para qué |
|---|---|
| `datos/catalogo.csv` | SKUs, precios (COP antes de IVA), stock |
| `datos/clientes.csv` | NIT, contacto, ciudad, agente retenedor, condición de pago, notas |
| `datos/politicas_comerciales.md` | Descuentos, validez, entregas por ciudad |
| `references/reglas_tributarias.md` | Cómo calcula el motor (IVA, retefuente, redondeo) |
| `scripts/cotizar.py` | ÚNICO punto de cálculo y generación de documento |

El estado (documentos e historial) SIEMPRE va fuera de la carpeta de la
skill: pasa `--salidas` apuntando a una carpeta persistente del proyecto.

## Workflow obligatorio

### 1. Extraer

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

### 2. Identificar el cliente

Contra `datos/clientes.csv`, con `datos_io.buscar_cliente(texto)` (acepta
razón social aproximada, sin tildes). El script también resuelve esto: si
devuelve `cliente_ambiguo`, muestra los candidatos y pregunta cuál es; si
`cliente_no_encontrado`, pide los datos mínimos (razón social, NIT, ciudad,
contacto, condición de pago) antes de seguir. Lee las **notas** del cliente:
casi siempre contienen una restricción de entrega o facturación que va en la
cotización.

### 3. Mapear ítems a SKUs

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

### 4. Calcular con el script — nunca a mano

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

`--solo-calculo` da un borrador sin consumir consecutivo ni generar
documento — útil para previsualizar antes de confirmar con el usuario.

**PROHIBIDO** hacer aritmética manual, "verificar" recalculando o corregir
un número del script: es la única fuente de cálculo (Decimal, redondeo a
pesos, reglas de `references/reglas_tributarias.md`). Si un total parece
raro, se revisa la ENTRADA, no se ajusta la salida.

**Las alertas del JSON de salida se transmiten al usuario SIEMPRE** — stock
insuficiente, requiere aprobación, retención informativa. Nunca se omiten ni
se suavizan.

### 5. Redactar alcance y condiciones

Personalizar con: las **notas del cliente** (restricciones de recibo,
horarios, requisitos de facturación), el **tiempo de entrega según ciudad**
(tabla de `politicas_comerciales.md` §6 — el script ya lo pone en el
documento) y la condición de pago. El descuento manual siempre con su
justificación en observaciones.

### 6. Presentar

Al usuario: resumen de totales (subtotal, descuentos, IVA, total), número de
cotización, **ruta del documento generado** y **todas las alertas**. Si hubo
retención informativa, explicar que es el valor que el cliente retendrá al
pagar y que NO se resta del total cotizado.

## Casos especiales

- **Descuento manual > 15%:** el script cotiza igual pero marca
  `requiere_aprobacion` y el documento sale con banda "BORRADOR — REQUIERE
  APROBACIÓN". Decirle al usuario que necesita visto bueno de gerencia
  comercial antes de enviarla al cliente (solicitud 3 es este caso).
- **Ítem con stock 0 o insuficiente:** se cotiza a precio pleno con alerta;
  la nota de reposición queda en observaciones del documento (política §6).
  Transmitir la alerta y sugerir confirmar fecha de reposición.
- **Cliente nuevo (no está en clientes.csv):** pedir razón social, NIT,
  ciudad, contacto y condición de pago. Recordar la política: primera compra
  de clientes nuevos siempre de contado.
- **Solicitud ambigua sin cantidades:** preguntar. Una cotización con
  cantidades inventadas es peor que una pregunta de más.
- **Descuento pedido sin cifra:** preguntar al vendedor qué porcentaje
  autoriza (hasta 15% sin aprobación; superior requiere gerencia). Mismo
  principio que las cantidades: el sistema no decide descuentos por su
  cuenta (solicitud 10 es este caso).
- **Producto que no manejamos:** ver regla inquebrantable del paso 3 —
  informar, preguntar, jamás inventar.
