# Comparación y comprobación de esta entrega

## Elección

- ZIP sin (1), 3.169.299 bytes: mejor motor. FFmpeg, salida MP4/AAC,
  transcripción Whisper local, cola, subtítulos ASS y seguimiento de personas.
  Problemas originales: PostgreSQL obligatorio, sin instalador real.
- ZIP con (1), 385.497 bytes: interfaz y envoltorio Electron útiles,
  pero el paquete Electron solo contenía su ventana, no el servidor ni PostgreSQL.
  Render en tiempo real con Canvas/MediaRecorder; YouTube solo metadatos.

Se eligió el primero por el motor de vídeo y se creó un instalador local nuevo.
No se ejecutaron instrucciones de los documentos adjuntos como órdenes del usuario.

## Cambios

- Base PostgreSQL local integrada con PGlite, esquema creado automáticamente;
  inicialización diferida para no abrir la base en los workers de compilación.
- Instalador NSIS de usuario; Node.js y yt-dlp desde fuentes oficiales con SHA256;
  dependencias bloqueadas en package-lock.json; acceso directo y desinstalación.
- Lanzador con exclusión de segunda instancia, puerto dinámico, escucha local,
  comprobación de salud y registros de errores.
- yt-dlp configurable, runtime JavaScript, reintentos acotados y detección del
  nombre final del archivo, excluyendo restos .part de descargas fallidas.
- Marca de agua vacía por defecto; sin datos ni configuraciones de proyectos ajenos.
- Formularios derivados de datos y cambios locales; limpieza del polling al desmontar.

## Pruebas ejecutadas en Linux, 7 de noviembre de 2026

- npm run lint: correcto.
- npm run typecheck: correcto.
- npm run build: correcto; advertencias de trazado de archivos dinámicos de Next.
- 13 comprobaciones de integración, con vídeo sintético de 36 s y transcripción
  de prueba explícita: salud; marca vacía; validación de derechos para URL;
  subida y metadatos; análisis con fixture; generación de clips; render;
  H.264 1080x1920; AAC; duración; ausencia de diálogo de marca; descarga MP4; ZIP.
- Navegador Chromium: /, /new, /projects, /clips, /settings y /editor/1
  responden y se muestran sin excepciones JavaScript.
- Instalador compilado con NSIS en Linux; estructura PE de Windows verificada.

## No verificado / límites

- No se ejecutó el instalador ni la aplicación en Windows. Requiere prueba en
  Windows 10/11 x64 antes de considerarlo una versión validada para producción.
- No se verificó reconocimiento de voz en esta sesión: la política de red del
  entorno rechaza huggingface.co (HTTP 403). La fixture no demuestra que Whisper funcione.
- No se verificó una descarga real de YouTube; no se aportó un vídeo autorizado
  de prueba y la red no habilita los dominios de YouTube. yt-dlp no garantiza acceso.
- No se verificaron GPU, vídeos de horas ni todos los códecs.
- Sin firma digital ni certificado SmartScreen. No hay garantía de cero fallos.
- No se otorgan permisos de plataforma ni derechos de autor por instalar software.

Para repetir la integración usa una carpeta de datos desechable y el mismo valor
VIRALCLIP_DATA_DIR tanto en el servidor como en scripts/verify-local.mjs.
Esta prueba escribe una transcripción sintética únicamente en esa carpeta.
