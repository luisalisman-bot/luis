# Kit de mapas profesionales

[Descargar el paquete ZIP](kit-mapas-profesionales.zip) · [Copiar el mensaje de arranque](PROMPT_PARA_CLAUDE_O_MUSE.txt)

El ZIP incluye 182 archivos: proyecto editable de Remotion, mapas y texturas, tipografía, sonido del montaje, miniatura 3:4, 11 skills públicos y una guía propia de producción, contexto del proyecto y scripts para exportar y validar.

## Uso

1. Descarga el ZIP y adjúntalo en Claude, Muse u otro agente con acceso a archivos y terminal.
2. Adjunta también el MP3 original. Los videos de referencia se pueden adjuntar aparte si quieres que el agente los vuelva a analizar.
3. Pega el mensaje de arranque. El agente debe leer START_HERE.md y comprobar las capacidades del entorno antes de ejecutar.

El kit no incluye la grabación original, los videos privados de referencia, node_modules, credenciales ni cuentas conectadas. Incluye los recursos gráficos y sonoros del montaje ya preparados. Las dependencias se instalan con npm ci cuando sea necesario.

Se probaron la compilación, una muestra renderizada de 132 fotogramas, su decodificación y la generación del SRT desde una carpeta separada. Los detalles están en evidence/package-check.json dentro del ZIP. No se ha probado en todos los productos de chat.

La base aprobada es [la versión 2 del video](../../videos/este-mapa-te-miente/v2/README.md). Su entrega se conserva sin cambios.

Verificación del ZIP: 24.687.306 bytes; SHA-256 en SHA256SUMS.txt. El manifiesto interior permite comprobar la integridad de los archivos.
