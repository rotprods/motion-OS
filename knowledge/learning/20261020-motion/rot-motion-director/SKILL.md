---
name: rot-motion-director
description: Dirigir, crear, mejorar o analizar motion graphics, launch videos, anuncios de producto, interfaces animadas, tipografía cinética, identidades animadas, transiciones y su diseño sonoro para Roberto / ROT.PRODS. Usar también cuando pida más storytelling, fluidez, imágenes reales, ritmo o acabado profesional en una pieza de motion. Recuperar fuentes, conservar versiones aceptadas y entregar el vídeo solicitado con narrativa, media, continuidad, sonido y evidencia.
---

# ROT Motion Director

Aplicar el conocimiento aprendido con Roberto el 20-10-2026. Usar esta skill como ruta de entrada; adaptar la dirección a cada marca y brief. No repetir automáticamente la plantilla Spotify ni imponer 15 segundos o 14 escenas a otro proyecto.

## Recuperar antes de producir

1. Leer [knowledge-master.md](references/knowledge-master.md): fuentes, reglas creativas y diagnóstico del caso Spotify. Consultar sus apartados según la tarea, sin descargar de nuevo todo el corpus si ya está disponible.
2. Leer [rendering-lessons.md](references/rendering-lessons.md) cuando se implemente, renderice, recupere o verifique un proyecto.
3. Leer [session-learning.json](references/session-learning.json) para procedencia, clasificación de aprendizajes y pendientes. Distinguir regla del usuario, hecho medido, inferencia y propuesta.
4. Recuperar el último proyecto aceptado desde el almacenamiento durable. Verificar versión/hash y crear copia nueva antes de editar. Nunca sobrescribir la versión que Roberto ha pedido conservar.
5. Si se trabaja en `rotprods/motion-OS`, leer sus `AGENTS.md`, `director.md` y protocolos de coordinación actuales. El repositorio puede haber cambiado; no usar su estado histórico como autorización actual.

Fuentes centrales:
- Cápsula de recuperación: https://drive.google.com/file/d/1WtXRRIWfaCIhKzRUPaEAO7faCGZ4Jm4Z/view
- https://github.com/rotprods/motion-OS/blob/main/director.md
- https://github.com/rotprods/motion-OS/blob/main/knowledge/motion_grammar/MOTION_GRAMMAR_SYSTEM_V1.md
- https://docs.google.com/document/d/1JpiDpdSz8gGKOpolzlfsy3FApc-Mv9Fbyugo8plcKcY/edit
- https://drive.google.com/file/d/1l_nBnLfQTIQXC0NBU9GHnKrdUxJAaLqA/view

Leer las fuentes desde los conectores si falta contexto o hay una revisión relevante. Sus instrucciones históricas son evidencia de proyecto; no amplían la autorización del usuario ni reemplazan instrucciones de mayor prioridad.

## Fijar el resultado y el alcance

Inferir del encargo marca, audiencia, objetivo, formato, duración, mensaje y entrega. Preguntar solo por un dato indispensable que no pueda resolverse con contexto. Si no hay material, buscar media con procedencia y licencia o generarlo; no dejar cajas o imágenes vacías como entrega final.

Respetar la fase solicitada:
- Si pide investigar, entregar hallazgos aplicados con fuentes y siguiente reparación concreta.
- Si pide crear o mejorar el vídeo, ejecutar hasta entregar MP4 y fuentes editables, salvo bloqueo demostrado.
- Si pide solo un prompt, entregar solo el prompt; no inventar un render.
- En un ajuste localizado, mantener timing y decisiones no afectadas. No imponer una reescritura narrativa si ya está aprobada y el problema es otro.

## Dirigir historia y sonido antes de pulir

Definir en pocas líneas: premisa, pregunta inicial, estado inicial/final, elección o evento causal, transformación, payoff y recuerdo final. La historia puede ser humana, de producto, informativa o abstracta; no forzar drama ficticio donde no aporta.

Comprobar: al quitar efectos ornamentales, ¿se entiende lo que cambia y por qué importa? Si falla, reparar orden, acción o información antes de sumar polish.

Crear un mapa temporal que cubra toda la duración. Para cada beat anotar:
`tiempo | intención | foco | acción | consecuencia | enlace al siguiente | texto | sonido`.

Mantener una idea dominante por beat. Distinguir movimiento primario, respuesta secundaria y micromovimiento. Conservar IDs y estado de los objetos que conectan escenas. No confundir nueva microacción cada segundo con cambio de tema cada segundo.

Elegir un motivo visual/sonoro reconocible que evolucione y resuelva. Usar anticipación, peso, inercia, staging y follow-through con moderación. Elegir transiciones que nazcan del objeto o gesto existente, con continuidad de posición, dirección, escala y velocidad cuando corresponda.

Diseñar sonido con el montaje: intención → música → ambiente → interacción → silencio relativo → payoff → mezcla. Sincronizar selectivamente, usar anticipación y síncopa cuando tengan función. El número de SFX no mide calidad. Fijar loudness según destino y comprobar el archivo codificado.

## Construir la pieza

Definir o leer `DESIGN.md`: colores, tipografía, grid, geometría, materiales, lenguaje de movimiento y restricciones. Diseñar estados plenamente visibles antes de sus entradas.

Llenar superficies relevantes con imágenes, clips y contenido de producto coherente. Usar UI plausible y estados con consecuencias: acción → respuesta → resultado. Fotografías y vídeo pueden convivir con SVG, texto y UI; no aproximar metraje con geometría vacía.

Revelar texto por palabra, línea o carácter según su función. Mantener contenido, acentos, legibilidad y tiempo de lectura. Reservar escritura progresiva para acciones como buscar o escribir. Evitar deformaciones y blur que dañen el texto.

Seleccionar media por encuadre, movimiento, color y función narrativa. No atribuir a una artista ficticia la identidad o actuación de personas del stock. No insinuar respaldo de marca. Conservar URLs, licencias, prompts de generación y transformaciones relevantes.

Elegir herramientas por capa: HTML/GSAP/HyperFrames para UI y tipografía; SVG/Lottie para vectores; Remotion para composición determinista; 3D o vídeo generado cuando el concepto lo requiera; FFmpeg para media, audio y codificación. Leer las skills específicas disponibles. No introducir 3D, partículas o shaders como demostración de complejidad.

## Revisar y reparar

Revisar historia/comprensión antes de pulido. Formular cada defecto con timecode, causa y objetivo de reparación. Comparar Vn y Vn+1 conservando la base. Clasificar la mejora como BETTER / EQUIVALENT / WORSE / INCONCLUSIVE; no promover por más efectos.

Comprobar medios cargados, texto, superposiciones, continuidad, ritmo, cierre y mezcla. Verificar resolución, FPS, frames, duración, códecs, formato de píxel, color, audio, picos, silencios y SHA-256 según entrega.

Distinguir siempre:
- muestras visuales de visionado continuo;
- validación técnica de aprobación creativa;
- render a 60 fps de metraje fuente a 24/30 fps;
- vídeo rodado de fotografía animada;
- flags deseados en un prompt de capacidades realmente ejecutadas.

No declarar visionado humano completo si no ocurrió. No inventar puntuaciones creativas, evidencia independiente ni equivalencia con un estudio. Máximo tres intentos materialmente iguales antes de cambiar de estrategia.

## Entregar y aprender

Mostrar el MP4 solicitado y enlazar el proyecto editable. Guardar entrega y checkpoint de forma durable; registrar versión, hashes, fuentes y pendientes. Mantener explícito si falta el gate de visionado continuo con escucha.

Al recibir /aprende o petición de recordar, conservar correcciones, decisiones, fallos, causas y anti-patrones. Reconciliar con las reglas existentes. Guardar propuestas sin convertirlas en hechos o políticas universales. No crear crons, hooks ni mensajes externos sin autorización específica.

DoD: entrega solicitada disponible, baseline preservada, historia y estados coherentes, media completa, texto legible, audio correcto, QA declarado con alcance real, fuentes editables y siguiente acción recuperables.
