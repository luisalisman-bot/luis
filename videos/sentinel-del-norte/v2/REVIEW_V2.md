# Auditoría y reparación V2
## Fallos encontrados en V1
0:00–fin: demasiadas capas de texto y créditos que el usuario rechaza.
0:00–0:06: canoa fuera del margen; gancho presentado como tarjeta.
~30 segundos acumulados: isla poligonal centrada repetida; zooms con pausas largas.
0:28,37: helicóptero empieza fuera de cuadro y su diseño plano contrasta con el fondo.
0:31,63: obturador adelantado respecto a «fotografiado», que comienza en 32,52 s.
0:43–0:51: año 1991 adelantado; cocos y agua se movían como una única imagen.
0:53–0:62: símbolos médicos genéricos sin conexión clara con quien llega.
Todo el metraje: captions de 47 px dominados por títulos de hasta 160 px, con grupos débiles.

Un revisor independiente confirmó estos fallos a partir de código y fotogramas; no escuchó el audio, por lo que no se afirma auditoría auditiva humana.

## Cambios implementados
Eliminación de encabezados y créditos en el encuadre; fuentes trasladadas a SOURCES.md y descripción externa. Tipografía Anton, 65 grupos semánticos, palabra activa y contorno legible. Nuevos objetos detallados y separados del fondo. Nuevas trayectorias de cámara para las 17 escenas. Flash y obturador en cuadro 975 (32,5 s), fechas 2004/2018/1991 y 5 km sincronizados. Cocos con caída, salpicadura y flotación independientes. Representación conceptual del posible riesgo de infección, no de un brote real. Mezcla de sonido nueva con cues vinculados a eventos visuales.

Estado: muestras revisadas y fallos corregidos; la validación final se detalla abajo.

## Segunda revisión y reparaciones
- Un revisor independiente detectó círculos antes de sus cues: Pulse quedó limitado a [at, at+18).
- Separación horizontal entre palabras ampliada a 25 px para compensar el contorno.
- Fuselaje del helicóptero reducido y reposicionado para evitar cortar nariz o cola accidentalmente. Recorrido interpolado en los cuadros locales96–110.
- Nuevo fondo de costa vertical; se retiró la ampliación excesiva de agua de la celda pequeña. Cocos con máscara de flotación y ondas.
- Años redundantes retirados; se muestran en los captions (2004,2018,1991). Datos geográficos puntuales únicamente.
- Planos de paraíso/nombre desconocido rehechos para reducir el uso de imagen satelital de baja resolución ampliada.
- Muestras nuevas del gancho (195 cuadros) y helicóptero (210 cuadros) renderizadas y revisadas como secuencia.
- Verificación de sincronía de voz: fotografiado,2004,cinco y1991 a menos de40 ms del cue de imagen/sonido. Contactos de cocos en cuadros1389,1452,1502.
- TypeScript sin errores antes de la exportación completa.

## Dictamen de las muestras corregidas
El revisor independiente no detectó fallos visuales bloqueantes en los PNG nuevos ni en los contactos de las muestras: Pulse fuera de intervalo eliminado, fuselaje completo y trayectoria continua, costa nítida sin fugas del atlas, flotación de cocos integrada, captions legibles y sin encabezados/créditos persistentes. El alcance fue visual; no se afirma escucha del audio ni validación final del archivo completo por ese revisor.

## Validación del archivo final
Se decodificaron los2289 fotogramas y el audio del archivo terminado. MP4 H.264/AAC,1080×1920,30fps,76,3s; átomos completos y ningún intervalo negro detectado. Audio codificado medido: −16,1LUFS integrados, −2,0dBFS de pico verdadero. Revisión del metraje completo a2fps en cuatro hojas de contacto. Un revisor independiente dio visto bueno visual sobre esas cuatro hojas, sin fallos bloqueantes; no se afirma escucha de audio. Las celdas vacías del final de la última hoja son relleno, no pertenecen al metraje.

SHA256 final: 3a914d853bdb88c0b5ce5dfb7ea04f79ab369d60f95db548dca2644cf254a2e4
