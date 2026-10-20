# ROT.PRODS — Motion OS: fuentes, storytelling y reparación de Spotify V6

Fecha: 20 de octubre de 2026 · Investigación solicitada por Roberto Gil Ortega.
Estado: INVESTIGACIÓN Y PROPUESTA CREATIVA. No es un nuevo render ni una aprobación de calidad final.
Base protegida: Spotify Your Sound V6, 15 s, 1080p60.
SHA-256 V6: e704a7f23de6b3596c1025bdd1a84fc3290a54c0170d00df8dfdafc0eb137a23.
El proyecto y el MP4 V6 no se modifican en esta intervención.

## 1. Hallazgo principal

El conocimiento ya existe en el sistema. La pieza ha seguido bastante bien la gramática de producto Spotify, pero no ha desarrollado con igual precisión la transformación emocional que exige la dirección creativa. La sucesión de funciones y el cambio visual por segundo no garantizan una historia.

Diagnóstico editorial: se ha optimizado acabado, densidad de media, tipografía y microinteracciones antes de resolver suficientemente la pregunta inicial, la causalidad del montaje y el payoff. Esto es una inferencia a partir de la secuencia conocida, el proyecto V6 y las fuentes; no una nueva revisión humana continua del MP4.

La reparación prioritaria es el montaje narrativo, manteniendo el sistema visual ya construido. La siguiente versión debe existir en otra copia; la V6 sigue siendo la referencia aceptada.

## 2. Fuentes con mayor autoridad creativa

### S01 — MOTION GRAPHICS DIRECTOR OS
Repositorio: https://github.com/rotprods/motion-OS
Documento: https://github.com/rotprods/motion-OS/blob/main/director.md
Commit consultado: f578adea6046bde9f8f36ce2680fe16391da6b97.
Lectura: documento completo, 24 apartados y regla maestra.

Define intención emocional inicial/desarrollo/final; beats con función narrativa; jerarquía primaria/secundaria; composición cambiante; física; tipografía; transformaciones; sonido, música, continuidad y control de atención.
Reglas clave:
- Todo movimiento debe dirigir atención, comunicar, generar emoción o conectar estados.
- Entre escenas debe existir vínculo visual o narrativo.
- La transición debe nacer, cuando sea posible, de un elemento ya presente.
- El sonido se diseña junto al movimiento.
- Hay que distinguir sincronía, anticipación, síncopa y retraso; sincronizarlo todo empobrece el ritmo.
- Un texto debe ser legible antes de su transformación.
- La pieza tiene que explicar qué se sabe al comienzo, qué se descubre, qué cambia y cuál es el payoff.
- Nunca tres movimientos disputando simultáneamente el foco.

Aplicación: sustituir la enumeración de pantallas por una acción musical con consecuencias.

### S02 — MOTION.OS · VIDEO EDIT PROTOCOL V1
https://docs.google.com/document/d/1JpiDpdSz8gGKOpolzlfsy3FApc-Mv9Fbyugo8plcKcY/edit

Orden: historia → rough cut → story lock → fine cut → picture lock → motion → sonido → color → master.
Prueba: el relato debe funcionar al retirar los efectos.
Prioridad: los problemas de historia y comprensión preceden al pulido visual.
Reparación: defecto → timecode → causa → cambio mínimo → render → comparación.
Exige visionado completo humano separado de QA técnico. Ese gate sigue pendiente; no se sustituye con muestreo o métricas de fotogramas.

### S03 — Gramática de movimiento y variante Spotify
https://github.com/rotprods/motion-OS/blob/main/knowledge/motion_grammar/MOTION_GRAMMAR_SYSTEM_V1.md
https://github.com/rotprods/motion-OS/blob/main/knowledge/motion_grammar/BRAND_COMMERCIAL_EXAMPLES.md
https://github.com/rotprods/motion-OS/blob/main/config/motion_grammars.yaml

Gramática: HYPER_COMMERCIAL_AUDIO. Overlay: SPOTIFY_FLUID_AUDIO_UI.
Una idea dominante por beat. UI plausible, texto íntegro, acciones del producto auténticas, contraste de densidad, cierre estable.
Secuencia de referencia: player → playlists → discovery → guardado → letras → pulso → artista → estadísticas → dispositivos → muro → pausa → recogida → logo.
Esto explica la estructura que hemos seguido. Es un ejemplo reutilizable de gramática, no una obligación de mantener cada función como capítulo independiente ni una garantía de storytelling.
Los valores 0,7–1,2 s son una política de ritmo, no una obligación de cambiar de tema cada segundo.

### S04 — Storytelling cinematográfico
https://docs.google.com/document/d/1eDbhcEhK49vFYi5a-sVuVnRKB6Z6coISnHfspwOqyNE/edit

Tema, pregunta dramática, estado inicial/final, deseo, obstáculo, quiebre, clímax y consecuencia visible.
Adaptación a 15 s: una microtransformación reconocible. No introducir biografía, conflicto épico y sacrificio que la pieza no necesita.

### S05 — Narrativa simbólica
https://docs.google.com/document/d/1io7seoV0S5XLs3kF5a1tCDTwE4EbaiMopX6lu7SH-vg/edit

Elegir un símbolo sencillo, repetirlo con variación e intensificarlo hasta la resolución.
Aplicación propuesta: un pulso/línea verde que comienza en el control de reproducción, conecta música y mundo y regresa como recuerdo guardado. Su evolución debe tener significado; no sumar ondas aleatorias.

### S06 — Sound OS
https://drive.google.com/file/d/1l_nBnLfQTIQXC0NBU9GHnKrdUxJAaLqA/view

Intención sonora → rol de música → SFX y ambiente → voz → mezcla.
El sonido dirige emoción y espacio. Efectos motivados, licencias y loudness según destino.
Aplicación: crear mundo cotidiano, umbral de escucha, expansión musical y regreso íntimo. El número de efectos no es una métrica de calidad.

### S07 — Motion general
https://drive.google.com/file/d/1P37tjDwy_DeTjlWCcc_gj1P4q0uiv0Lm/view

Anticipación, staging, acción secundaria, follow-through y easing según intención. Microinteracciones de 100–300 ms y transiciones de 300–600 ms se proponen como rangos de trabajo, no tiempos universales.
Aplicación: la pulsación anticipa la expansión, el arte conduce y los elementos secundarios responden después.

### S08 — Motion Graphics IA / sistema profesional
https://docs.google.com/document/d/1OB8ctFuGBOqG6xqRQ-Tu8DOV6iVNcXoKSMBPHpB0YZ8/edit

Extraer estructura de referencias; definir tokens, no drift, integridad de texto y continuidad. Traducir guion a comportamiento visual: significado → acción gráfica.
Separa información, jerarquía, ritmo y sonido. No basta con animar una frase.
Sus afirmaciones sobre qué modelos son los únicos capaces de ciertas tareas son información temporal no verificada; no se adoptan como hechos actuales.

### S09 — Director AE Motion design
https://docs.google.com/document/d/1Sqcj9kRkTyc4O6jp_muk1ek40WFYMH22A-gdE5iEoL0/edit

El contenido real es un canon de reconstrucción exacta vídeo→SVG, aunque su título parezca dirección general.
Prioriza fidelidad de frames, texto exacto, geometría estable y tiempo determinista. Distingue vectores de fotografía/metraje.
Sirve para reconstruir una referencia; no determina por sí solo una historia original mejor. Separar GENERATE y RECONSTRUCT_EXACT.

## 3. Leyes operativas aplicables a esta pieza

| Regla extraída | Prueba práctica |
|---|---|
| Evolución emocional | Puede describirse un antes y un después perceptibles. |
| Causa y consecuencia | Cada escena nace de una decisión o estado anterior. |
| Una idea dominante | Se identifica un foco por beat, sin competir con tres acciones. |
| Significado → comportamiento | El verbo del mensaje tiene una acción visual correspondiente. |
| Permanencia | Canción, portada y estado sobreviven a los cambios de layout. |
| Transición motivada | Se puede nombrar el objeto/gesto que origina el relevo. |
| Repetición con evolución | Un motivo reaparece cambiando su función, no solo su escala. |
| Anticipación y peso | La interacción prepara el cambio y produce respuesta. |
| Texto íntegro | Se puede leer sin perseguirlo ni inferir letras ocultas. |
| Contraste de ritmo | La densidad alterna con una pausa que sirve al relato. |
| Sonido como dirección | Hay una razón para cada entrada, silencio y acento. |
| Payoff | El final responde a lo planteado al inicio. |

Estas son reglas de producción sintetizadas de las fuentes, no una lista atribuida a Disney. No se localizó en la búsqueda una fuente específica y claramente pertinente titulada «12 principios de animación»; motion.md sí enumera principios concretos.

## 4. Defectos narrativos de V6 y objetivos de reparación

| Timecode V6 | Observación | Causa inferida | Objetivo |
|---|---|---|---|
| 0–2 s | Hero y reproductor atractivos, pero no plantean una necesidad concreta. | Se abre con una promesa visual y no con una pregunta o situación. | Introducir situación cotidiana reconocible con el metraje ya existente. |
| 2–4 s | Se vuelve a playlists y búsqueda después de mostrar reproducción. | Orden basado en catálogo de funciones. | Descubrimiento antes de escucha, o explicitar una elipsis. |
| 4–5 s | Guardar tiene una consecuencia visible: es un punto fuerte. | Acción → respuesta está demostrada. | Preservar y convertirlo en decisión emocional. |
| 5–7 s | Letras y DJ generan energía; la relación con una canción concreta es ilustrativa. | Cambio de media sin transformación del contexto plenamente construida. | La expansión debe sentirse causada por la reproducción; no fingir que el DJ es Mira Sol. |
| 7–9 s | Perfil y estadísticas abren dos temas nuevos. | Se intenta cubrir toda la gramática en 15 s. | Integrar como apoyo o reservar para otra pieza. No fabricar un historial de una canción recién descubierta. |
| 9–11 s | Multi-device demuestra continuidad; el tríptico amplía el mundo. | Beneficio presente, pero aún separado del arranque. | Misma canción y motivo; que acompañar al oyente sea consecuencia de su elección. |
| 11–15 s | Pausa, recogida y logo cierran gráficamente. | Falta una pregunta inicial cuya resolución recordar. | Recuperar la situación inicial transformada y resolver antes de la marca. |

Es un diagnóstico del diseño y orden conocidos, no una certificación de visionado continuo. No se declaran puntuaciones creativas nuevas.

## 5. Historia propuesta — siguiente variante, V6 intacta

Concepto: «Dale play a tu día».
Logline: en un día corriente, una canción encontrada transforma la forma de vivir el entorno; al guardarla, ese momento se vuelve propio y acompaña al oyente.
Transformación: rutina → descubrimiento → conexión → pertenencia.
Protagonista: el oyente. La canción/portada es el objeto continuo. Spotify facilita el cambio.
Símbolo: pulso verde con progresión y retorno.
Suposición creativa: mantener 15 s, 16:9, misma identidad y recursos principales. No es un cambio aplicado.

| Tiempo propuesto | Acción y propósito | Enlace | Tratamiento sonoro |
|---|---|---|---|
| 0–1,4 | Paseo cotidiano. «Un día cualquiera.» Presentar situación, un único foco humano. | Una pequeña señal verde conduce hacia discovery. | Ambiente urbano contenido; música aún filtrada y baja. |
| 1,4–3,0 | Playlists/búsqueda encuentran la portada. «Hasta que te encuentra.» Descubrimiento. | La portada seleccionada conserva posición y domina el frame. | Escritura breve, selección limpia; primera aparición de un motivo musical. |
| 3,0–4,2 | La portada se integra en el player y se pulsa play. Decisión visible. | El pulso nace del botón existente. | Microanticipación y entrada clara de la música. |
| 4,2–6,0 | Letras y mundo empiezan a responder. «Y cambia el ritmo.» Mostrar consecuencia. | Pulso, máscara y composición heredan dirección del player. | Música abierta; acentos editoriales selectivos. Sin falsa sincronía de canto. |
| 6,0–8,0 | DJ/concierto como expansión cultural y emocional. Un momento de máxima energía. | Un gesto o cambio de luz resuelve hacia la acción de guardar. | Ambiente de directo muy breve; subida y respiro antes de la decisión. |
| 8,0–10,0 | Corazón y confirmación: «Guárdate este momento.» Payoff de la conexión. | Misma portada llega a biblioteca y al siguiente dispositivo. | Click táctil y firma corta de confirmación; reducir otras capas. |
| 10,0–11,6 | La canción continúa en los dispositivos y vuelve al paseo. Beneficio demostrado. | Progreso y motivo conservados. | Un solo evento de conexión; puente musical continuo. |
| 11,6–13,0 | Momento íntimo y recogida. «Ahora suena a ti.» Resolver el antes/después. | Las imágenes vividas regresan al mismo arte, no a módulos arbitrarios. | Caída de percusión, espacio, motivo musical resuelto. |
| 13,0–15,0 | Marca estable. «Dale play a tu día.» Cierre legible. | Resolver con trazado de marca protegido; sin deformarlo. | Firma breve y cola controlada. |

El cambio de ritmo no significa cambiar de tema cada segundo. Las microacciones pueden seguir siendo rápidas dentro de capítulos conectados.
No hace falta que los catorce layouts actuales se conviertan en catorce capítulos. Sus diseños, assets y comportamientos se conservan para el montaje y futuras piezas.

## 6. Contrato de sonido para esa variante

Intención: pasar de exterior cotidiano a escucha personal, expandirse al mundo musical y regresar a una pertenencia íntima.
Música: conservar la composición existente como material de partida y remezclarla por secciones; una progresión continua, no reinicios por escena.
SFX: selección, reproducción, guardado y conexión tienen prioridad. Whooshes subordinados a movimientos reales.
Ambiente: calle y directo solo cuando orienten el espacio; obtener fuentes válidas antes de afirmar que están incorporadas.
Silencio relativo: preparar el acto de guardar y la pausa previa al cierre.
Voz: opcional; el animatic debe funcionar sin ella. No añadir locución para ocultar una narrativa visual débil.
Mezcla: loudness y pico se verifican sobre el archivo codificado, después de decidir destino. Los –18 LUFS y fades de 2 s del documento Azores pertenecen a aquel proyecto y no se copian como ley universal.
No se afirma que las URLs históricas de Freesound sigan disponibles ni que sus licencias hayan sido revalidadas en esta investigación.

## 7. Próxima ejecución concreta

1. Conservar V6 y su ZIP como baseline; crear nueva copia narrativa.
2. Montar un animatic de 15 s con los recursos existentes y audio guía; reordenar antes de producir más efectos.
3. Comprobar pregunta → elección → cambio → pertenencia sin animación ornamental.
4. Revisar continuidad de canción, sujeto y tiempo; no atribuir a la artista ficticia las personas del stock.
5. Solo después afinar las transiciones de ese montaje y su mapa de sonido.
6. Comparar con V6; registrar BETTER / EQUIVALENT / WORSE / INCONCLUSIVE por dimensión. No promover por tener más efectos.
7. Exportar review y obtener visionado continuo con escucha antes de declarar master creativo definitivo.

No se ha modificado el repositorio remoto, no se han fusionado PRs y no se ha instalado ningún sistema global. Leer los contratos no significa que un motor haya aplicado o validado automáticamente todas sus reglas.

## 8. Registro complementario de búsqueda

Drive: búsquedas de motion, director, sound, storytelling, graphics, leyes, Motion Director, sonido, narrativa, principios de animación y Gestalt.
GitHub: búsqueda de repositorios y de contenido; el repositorio pertinente recuperado fue rotprods/motion-OS. El primer barrido de rot.knowledge tuvo ruido de otros proyectos y se refinó.
No se recorrieron todas las carpetas de Drive ni todas las ramas de GitHub. Hay copias duplicadas de varios documentos y páginas de agentes; se seleccionaron las fuentes de mayor pertinencia creativa.
A continuación, archivos recuperados y nivel de lectura. «Extractos» no significa lectura integral.

| Documento | Fuente | Caracteres recuperados | Revisión |
|---|---|---:|---|
| MOTION.OS — VIDEO EDIT PROTOCOL V1 | [Abrir](https://drive.google.com/file/d/1JpiDpdSz8gGKOpolzlfsy3FApc-Mv9Fbyugo8plcKcY/view) | 10968 | Texto recuperado leído completo |
| Storytelling cinematográfico | [Abrir](https://drive.google.com/file/d/1eDbhcEhK49vFYi5a-sVuVnRKB6Z6coISnHfspwOqyNE/view) | 4100 | Texto recuperado leído completo |
| Guía Storytelling en Short Form Content | [Abrir](https://drive.google.com/file/d/1h-cuhPsGEJG4FMqFdNFNRIL2ceYmB93f9FIim-pRJ-o/view) | 3137 | Texto recuperado leído completo |
| Motion Graphics IA | [Abrir](https://drive.google.com/file/d/1OB8ctFuGBOqG6xqRQ-Tu8DOV6iVNcXoKSMBPHpB0YZ8/view) | 5396 | Texto recuperado leído completo |
| soundos.md | [Abrir](https://drive.google.com/file/d/1l_nBnLfQTIQXC0NBU9GHnKrdUxJAaLqA/view) | 1923 | Texto recuperado leído completo |
| Director AE Motion design | [Abrir](https://drive.google.com/file/d/1Sqcj9kRkTyc4O6jp_muk1ek40WFYMH22A-gdE5iEoL0/view) | 7349 | Texto recuperado leído completo |
| Narrativa simbólica | [Abrir](https://drive.google.com/file/d/1io7seoV0S5XLs3kF5a1tCDTwE4EbaiMopX6lu7SH-vg/view) | 2520 | Texto recuperado leído completo |
| motion.md | [Abrir](https://drive.google.com/file/d/1P37tjDwy_DeTjlWCcc_gj1P4q0uiv0Lm/view) | 2239 | Texto recuperado leído completo |
| Director de videoclips VISIÓN | [Abrir](https://drive.google.com/file/d/1Ek6kfufOMVTePj7kzdRz8LX8xhpEd7Jgwy-CfrHBzl0/view) | 8441 | Consulta por apartados / extractos; no se afirma lectura integral |
| cinematic-production-director.md | [Abrir](https://drive.google.com/file/d/14kPXHpihIAMwtsLh8-QIRwK8I7UnoIin/view) | 15289 | Consulta por apartados / extractos; no se afirma lectura integral; Respuesta termina durante SHOT 014; usar como ejemplo parcial, no especificación completa |
| paisajes_sonoros.txt | [Abrir](https://drive.google.com/file/d/1ZSAAgS6vUyZ0bZy_-8uf5RRaueyBtCDu/view) | 1915 | Consulta por apartados / extractos; no se afirma lectura integral |
| Motion style | [Abrir](https://drive.google.com/file/d/1c5wS_jMCQ8Py-NHDplvnBlB2R4No_-oL43bcHh3NE7A/view) | 288732 | Consulta por apartados / extractos; no se afirma lectura integral |
| Motion-Graphics-con-IA.md | [Abrir](https://drive.google.com/file/d/1HoLTDNAv-gkEErnD-F35-uZWr1Ye2s9E/view) | 14178 | Consulta por apartados / extractos; no se afirma lectura integral |
| Motion graphics prompts | [Abrir](https://drive.google.com/file/d/1fMTthC0tZXO4g8YQC1UPO9vxIx11ia_JeFUVXCVXmxk/view) | 36053 | Consulta por apartados / extractos; no se afirma lectura integral |
| Director de cine MASTER PROMPT — | [Abrir](https://drive.google.com/file/d/1TM8MU2r011u6YG0zSzXsRC1kPc0Z-YrDT4noZCPYJ0M/view) | 20305 | Consulta por apartados / extractos; no se afirma lectura integral |
| AI motion graphics ebook | [Abrir](https://drive.google.com/file/d/1qO7vCaQhC9InKRUmRpUdz44_iGNuWT1L3FgxCDdg1nE/view) | 23999 | Consulta por apartados / extractos; no se afirma lectura integral |

Los documentos de dirección cinematográfica y el caso Prada sirven como ejemplos de propósito de plano, motivos y respiración; su estética, duración y lentes no se convierten en reglas para esta pieza Spotify. El ebook y los prompts son referencias de intención, no prueba de ejecución de flags de render ni de capacidades actuales de modelos.



# Protocolo reutilizable aprendido — 20-10-2026

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


# Lecciones de implementación

# Lecciones de implementación y recuperación

## Contenido
- Preservación
- Render determinista
- Media real
- Audio
- QA
- Recuperación

## Preservación

V4 → V5 → V6 son versiones independientes. V5 SHA-256 `0f2b2af6d49d673e73ade0239cd7854a86b5723c8fe51e3bb9cbf240dae3f65c`; V6 `e704a7f23de6b3596c1025bdd1a84fc3290a54c0170d00df8dfdafc0eb137a23`. V6 conserva copia byte-idéntica de música y HTML V5; no editar los ZIP aceptados.

Durable V5: `libfile_2c9e72ce4ba08191b8631f51e28915d6`, SPOTIFY_YourSound_V5_Proyecto.zip, 18.564.365 bytes. Durable V6: `libfile_656ed3cad91881918c586184a9a7368a`, SPOTIFY_YourSound_V6_Proyecto.zip, 22.085.723 bytes. Informe de investigación: `libfile_4a4ad1fda4a48191a25b08c8b6796e46`. Estos IDs son localizadores, no prueba de que un archivo ya esté materializado.

## Render determinista

Caso validado: HTML/CSS/SVG y GSAP pausado, 1920×1080, 15 s, 900 frames a 60 fps; captura con Puppeteer y FFmpeg H.264/AAC. No imponer estos parámetros a futuros briefs.

- En `page.evaluate`, usar un bloque sin devolver la timeline: `t => { window.__timelines.main.seek(t, false); }`. Devolver un objeto GSAP coincidió con bloqueo de serialización; el bloque vacío funcionó. Tratar como lección de esa integración, no demostrar causalidad universal.
- En el runtime Puppeteer de la sesión, `executablePath()` devolvió Promise; esperar el resultado o usar CHROME_BIN explícito. Chrome completo falló por restricciones de sockets; Chrome Headless Shell funcionó. Elegir según entorno, no desactivar protecciones globales.
- Preparar fuentes e imágenes antes de capturar. No construir timelines asíncronamente. Evitar tweens que compitan por la misma propiedad y entradas `from()` duplicadas que dejan contenido transparente.
- Los puentes deben ocultar solo los píxeles relevados, no todo un componente con sus controles. Comprobar geometría durante el relevo, no solo el frame final.
- Guardar baselines como `.source` u otro recurso no ejecutable fuera de entradas HTML. Varias raíces con `data-composition-id` provocaron error de lint y riesgo de descubrimiento duplicado.
- No añadir grano SVG de feTurbulence a pantalla completa sin medir coste. No afirmar GPU física cuando el render usa llvmpipe.
- La captura intermedia JPEG 97 es con pérdidas; no afirmar master sin pérdidas ni blur temporal multisample.

## Media real

Tres clips de la V6: Mixkit 4855 y 42417, y Pexels 12695733. Tres fotos añadidas: Pexels 8138677, 12499887 y 3394668. Mantener los manifests de fuentes/licencias. Para nuevos usos, revalidar derechos y disponibilidad; no asumir por la marca del proveedor.

Stock rodado, fotografías animadas y media generada son categorías diferentes. El MP4 final a 60 fps no convierte fuentes 23,976/24/29,97 fps en metraje capturado a 60. No afirmar interpolación óptica no ejecutada.

Caso V6: secuencias JPEG a 30 fps seleccionadas por tiempo desde el renderer, interfaz a 60 fps. El autor media-stepper mantiene sincronía determinista; no usar autoplay ni reloj real.

## Audio

La V6 añade 21 eventos a la música preservada. Mezcla codificada medida: –16,0 LUFS integrados, pico verdadero –1,2 dBFS. Son resultados del caso, no objetivos universales. Separar score original, mezcla y cue map; volver a medir el archivo final.

Ecualizadores existentes pasan a 16 bandas FFT offline con 900 muestras. No confundir un patrón periódico con análisis real. No añadir más ecualizadores como decoración por defecto. Las letras ficticias no están cantadas: su revelado es editorial.

## QA

Verificar frames, dimensiones, duración, audio, color, medios ausentes y texto. Los 60 samples cada 0,25 s, las hojas de contacto y un lint no equivalen a un visionado continuo con escucha. Mantener ese gate pendiente hasta que ocurra.

V6: lint 0 errores y 6 avisos por imágenes repetidas; validate 36 elementos muestreados AA; inspect 0 errores, 0 warnings y 1 info por cabecera sobre gradiente. No generalizar a accesibilidad total ni calidad semántica perfecta.

Revisar defecto→timecode→causa→reparación→comparación. No reemplazar la crítica narrativa por métricas de diferencia de frames. No declarar equivalencia con campaña de estudio sin evaluación del resultado.

## Recuperación

El scratch puede desaparecer por mantenimiento. Recuperar fuentes editables y media desde el ZIP durable; comprobar hashes antes de continuar y guardar checkpoints. No fingir que un path histórico sigue existiendo. Usar herramientas autenticadas y metadatos de Library según su skill. No reconstruir un proyecto completo de memoria cuando existe copia recuperable.

Siguiente acción pendiente del caso: variante narrativa «Dale play a tu día» en copia V7; no está renderizada. La V6 sigue intacta.


# Cosecha y clasificación

- **MOTION-L01 · PREFERENCE · high · SHARED_ADAPTER**: Preservar versiones aceptadas; mejorar en copias independientes. Fuente: Usuario: No rompas nada de lo que hay ahora solo mejora.
- **MOTION-L02 · INFERENCE · high · SHARED_ADAPTER**: Reparar storytelling antes de aumentar efectos. Fuente: Usuario detecta falta de storytelling después de V6; contraste con director.md y protocolo.
- **MOTION-L03 · RULE · high · SHARED_ADAPTER**: Leer director.md y fuentes pertinentes antes de dirigir una pieza. Fuente: AGENTS.md y director.md de motion-OS, consultados f578adea.
- **MOTION-L04 · RULE · high · SHARED_ADAPTER**: Cada movimiento debe comunicar, orientar, emocionar o conectar. Fuente: director.md y gramática universal.
- **MOTION-L05 · RULE · high · SHARED_ADAPTER**: Mantener vínculo causal o visual entre escenas y una idea dominante por beat. Fuente: director.md y MOTION_GRAMMAR_SYSTEM_V1.md.
- **MOTION-L06 · PREFERENCE · high · SHARED_ADAPTER**: Integrar imágenes y media con contenido; evitar superficies vacías. Fuente: Correcciones reiteradas del usuario en V4–V6.
- **MOTION-L07 · RULE · high · SHARED_ADAPTER**: Diseñar música, ambiente, interacción, silencio y payoff con el montaje. Fuente: soundos.md y director.md.
- **MOTION-L08 · RULE · high · SHARED_ADAPTER**: Separar muestreo visual, QA técnico y visionado continuo con escucha. Fuente: Protocolo Motion.OS y QA V6 con full_watch pendiente.
- **MOTION-L09 · FACT · high · PROJECT_ONLY**: V6 disponible como proyecto durable; 1080p60, 15 s, 900 frames, audio AAC. Fuente: VERIFICATION.json y Library libfile_656ed3cad91881918c586184a9a7368a.
- **MOTION-L10 · FACT · high · SHARED_ADAPTER**: Separar fuentes reales, vectores y fotografías; registrar procedencia. Fuente: Director AE y manifests de clips/fotos V6.
- **MOTION-L11 · INFERENCE · medium · PROJECT_ONLY**: En esta captura evitar devolver objetos GSAP y comprobar executablePath asíncrono. Fuente: Fallos y correcciones ejecutados en V4/V6.
- **MOTION-L12 · DECISION · high · SHARED_ADAPTER**: Persistir una skill de entrada reutilizable para motion relacionado. Fuente: Petición explícita actual del usuario y flujo repetido V4–V6.
- **MOTION-L13 · DECISION · high · SHARED_ADAPTER**: Usar skill para entrada, Git para versión, Drive para recuperación y Mem para índice semántico. Fuente: Petición de todas las superficies necesarias; evita copias con autoridad rival.
- **MOTION-L14 · OPEN_QUESTION · high · PROJECT_ONLY**: La variante narrativa siguiente y el visionado completo siguen pendientes. Fuente: MASTER research: propuesta de 15 s, sin nuevo render.
- **MOTION-L15 · FACT · high · PROJECT_ONLY**: cosecha: hay inventario y alias pero no body recuperado ni brain_query callable. Fuente: Búsquedas Drive/GitHub de esta sesión y registro previo.

Se consideraron 17 clases RC1; las clases sin candidatos se registran con cero. No se promovió aprende RC1 ni se ejecutó un brain runtime.
