# Guion de demo — Forja

**Demo Day: jueves 6 de agosto, Ruta N, ante las empresas madrinas.**
Duración objetivo: 5 minutos en vivo · 2 minutos para el video de respaldo.

---

## Antes de empezar (checklist de 5 minutos)

- [ ] Sesión de claude.ai **fresca**, límites verificados (el sábado llegaste al 90% a mitad de la corrida)
- [ ] Modelo fijado en Opus 5 desde el inicio — no dejarlo cambiar a mitad de demo
- [ ] Proyecto "Forja — Cotizador El Cedro" abierto, skill `forja` activa (una sola en la lista)
- [ ] Chat **nuevo y vacío** — el consecutivo arranca en COT-2026-001
- [ ] Los 5 mensajes copiados en un bloc de notas, listos para pegar
- [ ] Repositorio abierto en otra pestaña: github.com/johnrpo-dev/forja-cotizador
- [ ] Video de respaldo accesible en 10 segundos
- [ ] **Todo en un solo chat**: cada chat nuevo reinicia la numeración

---

## Apertura (20 segundos)

> "En una pyme comercial, armar una cotización a mano se lleva media hora:
> buscar precios, aplicar descuentos, liquidar IVA, maquetar el documento,
> llevar el consecutivo. Mientras tanto el cliente que está afanado se enfría.
>
> Forja recibe el WhatsApp tal como llega y devuelve el documento formal.
> Pero lo que quiero mostrarles no es que lo genera rápido — es **dónde decide
> no hacerlo**."

*(No abrir con arquitectura. La frase de "dónde decide no hacerlo" es el gancho:
promete algo distinto a lo que todos los demás van a mostrar.)*

---

## Caso 1 · Genera (45 segundos)

**Pegar:**
```
Buenas! qué más pues. Me ayudas con una coti pa Café y Punto de Medellín,
el señor Andrés Mora. Necesita 30 sillas rimax apilables pa un evento que
tienen en agosto. Es de contado como siempre. Me la mandas hoy porfa que
el man está afanado 🙏
```

**Mientras corre:**
> "Español coloquial, sin estructura, con emoji. De ahí salen cliente, producto,
> cantidad y condición de pago."

**Al aparecer el PDF — abrirlo y señalar:**
> "COT-2026-001. El 5% de descuento por volumen se aplicó solo, porque la
> política dice que a partir de 20 unidades aplica. Total $2.306.220.
>
> Y miren las observaciones del documento: *'Evento en agosto, cliente con
> afán'*. Eso venía en el WhatsApp y llegó al PDF."

**Rematar con la decisión de diseño:**
> "Un detalle que importa: **el modelo no calculó nada de esto**. Entiende el
> mensaje y redacta, pero la aritmética la hace un script de Python con 86
> tests. Un modelo sumando IVA falla en silencio, y falla justo cuando hay
> público."

---

## Caso 2 · No inventa (60 segundos) — **el caso central**

**Pegar:**
```
Oiga, doña Miriam de la Droguería Nororiente volvió a escribir. Que además
de los estantes metálicos quiere saber si manejamos una greca industrial de
60 tazas pa los tintos y un ventilador de techo pa la bodega que allá en
Cúcuta hace un calor bravo 🥵 Yo ni idea si vendemos eso, me confirmas?
```

**Antes de que responda, decirlo en voz alta:**
> "Un asistente genérico aquí les inventa un precio para la greca. Suena
> razonable, sale bien formateado, y nadie se da cuenta hasta que el cliente
> lo acepta."

**Al responder:**
> "No los tiene, lo dice, y no inventa. Además ofrece una alternativa del
> catálogo — convierte el 'no' en una oportunidad.
>
> Y noten la segunda cosa: por los estantes **sí** pregunta la cantidad, porque
> el mensaje no la trae. No asume que es uno."

---

## Caso 3 · Devuelve la decisión (45 segundos)

**Pegar:**
```
Última del día 😅 Los muchachos de Software Eje Cafetero en Pereira van
creciendo, ahora quieren 8 escritorios operativos, 8 sillas ergonómicas
Nogal, 8 bases refrigerantes y 8 soportes de monitor doble brazo. De
contado. Cristian pregunta si por llevar el combo le sale algún descuentico,
mira qué se puede hacer dentro de lo permitido
```

**Al aparecer la pregunta con opciones:**
> "'Algún descuentico' no es un número. El sistema no lo elige por su cuenta:
> pregunta, y de paso le recuerda al vendedor que 15% es su tope sin aprobación.
>
> Esa es una **decisión comercial**, y es del humano. El sistema conoce la
> política y la aplica; no la sustituye."

**Responder "10%" y mostrar el PDF:** COT-2026-002, total $14.822.640.

---

## Caso 4 · Bloquea (45 segundos)

**Pegar:**
```
Hágame un favor. El señor Óscar de la Ferretería La Frontera en Cúcuta
quiere: 60 organizadores de escritorio, 40 papeleras metálicas y 25
carteleras de corcho. PERO dice que si le damos el 20% de descuento cierra
ya mismo y paga de contado. Yo le dije que de una... me arma la coti con
ese 20%? El cliente compra harto, no lo dejemos ir
```

**Al aparecer el PDF con la banda roja:**
> "Aquí el vendedor ya le prometió el 20% al cliente. El sistema lo cotiza
> igual — no le dice que no — pero el documento sale marcado **'BORRADOR —
> REQUIERE APROBACIÓN DE GERENCIA COMERCIAL'** en rojo, arriba de todo.
>
> Y en el chat dice algo que no le pedimos: *'No se la puedes mandar a Óscar
> todavía'*. Eso ya no es generar documentos, es hacer cumplir la política
> comercial de la empresa."

---

## Caso 5 · Declara lo que no sabe (60 segundos) — **el remate**

**Pegar:**
```
Necesito las fichas técnicas del estante ARC-007 y de la silla ergonómica
Nogal SIL-008 para anexar a un proceso de compra.
```

**Abrir la ficha de ARC-007:**
> "200 × 90 × 40 centímetros, material metal. Salió del catálogo."

**Antes de abrir la de SIL-008 — preguntarle al público:**
> "El producto se llama 'Silla ergonómica **Nogal**'. ¿De qué creen que está
> hecha?"

*(Esperar. Alguien va a decir madera.)*

**Abrir la ficha:**
> "Dimensiones: no registradas. Materiales: no registrados.
>
> Nogal es la línea comercial, como Cedro Pro o Macondo. **No es una madera.**
> Cualquier sistema que le pida esto a un modelo sin control escribe 'madera de
> nogal' — suena perfecto y es falso.
>
> Esta ficha se anexa a un proceso de compra. Un dato inventado ahí termina en
> un pliego de licitación."

---

## Cierre (30 segundos)

> "Cinco casos: generó uno, y en tres decidió **no** completar solo.
>
> Fíjense en la numeración: 001, 002, 003. Las dos fichas se generaron en medio
> y no consumieron consecutivo, porque responder '¿qué medidas tiene?' con una
> cotización numerada ensucia el historial con documentos que nadie pidió.
>
> El principio es uno solo: **prefiere un campo vacío y declarado a un dato
> plausible inventado**.
>
> La IA entiende y redacta. La aritmética es código determinístico y testeado.
> Por eso esta cotización se puede firmar."

**Mostrar el repositorio:** motor con 86 tests, reglas documentadas, 16
solicitudes de prueba con evidencia, y el proceso completo de construcción.

---

## Versión de 2 minutos (para el video de respaldo)

Grabar en pantalla, sin cámara, con voz en off. Solo tres casos:

| Tiempo | Contenido |
|---|---|
| 0:00–0:15 | Apertura, hasta "dónde decide no hacerlo" |
| 0:15–0:50 | **Caso 1** — WhatsApp → PDF. Mencionar que el cálculo es script, no modelo |
| 0:50–1:25 | **Caso 2** — la greca. "Un asistente genérico aquí inventa un precio" |
| 1:25–1:50 | **Caso 5** — el contraste Nogal (sin la pregunta al público) |
| 1:50–2:00 | Cierre: la frase del campo vacío + pantallazo del repositorio |

Grabarlo **antes del miércoles**. Si el jueves falla la conexión, se acaba la
cuota o el contenedor se cae, el video es la demo.

---

## Preguntas probables del jurado

**"¿Por qué no dejas que el modelo calcule?"**
Porque falla en silencio. Un total mal sumado sale igual de bien formateado que
uno correcto, y nadie lo revisa. El script tiene 86 tests con la aritmética
calculada a mano en los comentarios; el modelo no puede equivocarse en algo que
no hace.

**"¿Esto sirve para otra empresa?"**
Los datos están separados de la lógica: catálogo, clientes y políticas son tres
archivos. Cambiarlos es cambiar de empresa; el motor y el workflow no se tocan.

**"¿Cuánto costó / cuánto cuesta operarlo?"**
Cero adicional. Corre sobre el plan que la pyme ya paga. Sin servidor, sin base
de datos, sin licencias.

**"¿Qué pasa si el catálogo tiene 5.000 productos?"**
Aguanta: es lectura de archivo plano y búsqueda exacta por SKU. Donde deja de
servir es con varios vendedores cotizando al tiempo — ahí la numeración
consecutiva sobre archivo se rompe y hay que ir a un servidor con transacciones.
Está documentado en `docs/arquitectura.md`.

**"¿Y si el cliente no está en su base? A mí me llegan clientes nuevos todos
los días."**
Se cotiza igual: el vendedor dicta NIT, razón social, contacto y ciudad, y el
documento sale. Pero hace dos cosas que vale la pena destacar.

Primero, **no lo mete en la base de datos**. Ese cliente vale para esa
cotización. Dar de alta a un cliente es trabajo de cartera, con su estudio de
crédito; si la herramienta empieza a escribir en su propia fuente de datos,
ya nadie sabe quién metió qué.

Segundo, **pregunta si el cliente es agente retenedor**. Ese dato no lo asume,
y podría: lo más común es que no lo sea. Pero suponerlo sería inventar una
condición tributaria de una empresa que no conoce. Es la misma regla de no
inventar un precio.

*(Si hay espacio, rematar:)* Y no le pregunta la condición de pago, porque la
política de la empresa ya la define: primera compra de cliente nuevo, de
contado. El sistema no negocia eso ni aunque el vendedor lo pida.

**"¿Y cómo sabe que 'Constructora Sierra Alta' no es la 'Constructora
Altamira' que ya tiene registrada?"** — *la respuesta más valiosa del bloque;
no esconder que el bug existió.*
Al principio no lo sabía, y ese fue un bug real. Probé diez clientes nuevos
con razones sociales colombianas realistas y **cuatro salieron facturados a
nombre de otra empresa** — con NIT ajeno, ciudad ajena y régimen tributario
ajeno, sin una sola alerta. "Sierra Alta" contra "Altamira" daba 79% de
parecido.

El problema era que aceptaba al único candidato que quedara sin mirar cuánto
se parecía. Ahora hay dos umbrales con una banda muerta entre ellos: identifica
con NIT exacto o con más del 85% de parecido; entre 60 y 85 no identifica a
nadie, muestra los candidatos con su puntaje y pregunta. Y hay test de
regresión con esos cuatro nombres exactos.

*Por qué contarlo así: demuestra método — probar hasta romper, entender la
causa, blindar con tests. Un evaluador con criterio premia eso más que un
sistema que nunca falló porque nunca se probó a fondo.*

**"¿Cómo lo construiste?"**
Dos fases: arquitectura y plan en un chat de Claude, ejecución por fases en
Claude Code. Todo el proceso está en el repositorio — el plan original, el
registro cronológico de prompts y las correcciones que hubo en el camino.
