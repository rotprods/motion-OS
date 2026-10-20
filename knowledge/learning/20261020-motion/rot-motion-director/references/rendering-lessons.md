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
