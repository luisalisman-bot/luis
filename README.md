# PeakCut gratis en el navegador con Google Colab

[**ABRIR PEAKCUT GRATIS EN COLAB**](https://colab.research.google.com/github/luisalisman-bot/luis/blob/peakcut-colab/PeakCut_Gratis_Colab.ipynb)

1. Entra con tu cuenta de Google.
2. Pulsa **Entorno de ejecución → Ejecutar todo**.
3. Selecciona un video cuando aparezca el selector de archivos.
4. Espera al procesamiento en Google y descarga el ZIP de los clips.

Usa una sesión alojada gratuita de CPU. No necesitas instalar el programa en
Windows, activar una GPU, pagar un servidor ni conectar una API de pago.
El trabajo de transcripción y exportación se realiza en Google. El navegador
se usa para subir el archivo, manejar el cuaderno y descargar el resultado.

Las sesiones son temporales y Google aplica cuotas variables. Descarga los
clips antes de cerrar. La selección básica se basa en el volumen y los
subtítulos automáticos están configurados para español; conviene revisarlos.
Esta adaptación incluye subida, procesamiento y descarga dentro del cuaderno.
El editor completo de escritorio y la publicación en redes siguen en la
aplicación original.

[Condiciones y límites oficiales de Colab](https://research.google.com/colaboratory/faq.html).

Basado en [PeakCut](https://github.com/haziqahmedqasmi/PeakCut), MIT, con
Whisper multilingüe. El motor y el modelo se extraen de una versión verificada
del paquete publicado; el Python de Windows queda fuera del entorno de Google.
Los archivos subidos y generados pertenecen a la sesión del usuario y no se
incluyen en este repositorio.

La comprobación automatizada valida el cuaderno y el procesamiento real en
Linux con el mismo ayudante. El inicio de sesión de Google, el selector de
archivos y la descarga dentro de la interfaz de Colab requieren la sesión del
usuario y no se han comprobado con su cuenta.
