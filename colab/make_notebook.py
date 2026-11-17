from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent.parent
runtime_hash = hashlib.sha256((ROOT / 'colab/runtime.py').read_bytes()).hexdigest()

def markdown(text):
    return {'cell_type': 'markdown', 'metadata': {}, 'source': text.splitlines(keepends=True)}

def code(text):
    return {'cell_type': 'code', 'metadata': {'cellView': 'form'}, 'source': text.splitlines(keepends=True),
            'execution_count': None, 'outputs': []}

cells = [markdown('''# PeakCut gratis en la nube

El motor trabaja en una sesión alojada de **Google Colab**. Tu computadora sirve para subir el video y descargar los clips.

**Para empezar:** entra con Google y pulsa **Entorno de ejecución → Ejecutar todo**. Espera a que aparezca el selector de archivos, elige un video y mantén esta pestaña abierta hasta descargar los resultados.

- Usa el entorno alojado gratuito de Python/CPU. No hace falta activar una GPU ni contratar un plan.
- Los subtítulos están configurados para español. Puedes cambiar el idioma en el paso 3.
- La selección de clips usa el volumen del audio. No se llama a una IA externa ni se necesita una clave API.
- **Colab tiene cuotas y sesiones temporales.** Descarga el ZIP al terminar: los videos y resultados pueden desaparecer cuando termina o se reinicia la sesión.
- Para una primera prueba, elige un video con voz clara y de al menos 20 segundos. Los subtítulos automáticos pueden contener errores.

[Información oficial de Google sobre Colab gratuito y sus límites](https://research.google.com/colaboratory/faq.html).
'''), code('''#@title ▶ 1. Preparar PeakCut en la nube
import hashlib
import importlib.util
from pathlib import Path
import urllib.request

try:
    from google.colab import files
except ImportError:
    raise RuntimeError("Abre este enlace dentro de Google Colab y usa su entorno alojado.")

CARPETA = Path("/content/peakcut_gratis")
CARPETA.mkdir(parents=True, exist_ok=True)
AYUDANTE = CARPETA / "peakcut_colab_runtime.py"
URL_AYUDANTE = "https://raw.githubusercontent.com/luisalisman-bot/luis/peakcut-colab/colab/runtime.py"
with urllib.request.urlopen(URL_AYUDANTE, timeout=60) as respuesta:
    codigo = respuesta.read()
if hashlib.sha256(codigo).hexdigest() != "RUNTIME_SHA":
    raise RuntimeError("El ayudante ha cambiado. Vuelve a abrir la versión actual del cuaderno.")
AYUDANTE.write_bytes(codigo)
especificacion = importlib.util.spec_from_file_location("peakcut_colab_runtime", AYUDANTE)
peakcut = importlib.util.module_from_spec(especificacion)
especificacion.loader.exec_module(peakcut)
peakcut.install(CARPETA)
'''.replace('RUNTIME_SHA', runtime_hash)), code('''#@title ▶ 2. Subir un video
from google.colab import files
from pathlib import Path
import os
import uuid

if "peakcut" not in globals():
    raise RuntimeError("Ejecuta primero el paso 1: Preparar PeakCut.")
RESULTADO_ZIP = None
entrada = CARPETA / "entradas" / uuid.uuid4().hex
entrada.mkdir(parents=True)
carpeta_anterior = Path.cwd()
try:
    os.chdir(entrada)
    subidos = files.upload()
finally:
    os.chdir(carpeta_anterior)
validos = [nombre for nombre in subidos if Path(nombre).suffix.lower() in peakcut.VIDEO_TYPES]
if len(validos) != 1:
    raise RuntimeError("Selecciona un solo video MP4, MOV, MKV o WEBM y vuelve a ejecutar este paso.")
VIDEO = (entrada / validos[0]).resolve()
if not VIDEO.is_relative_to(entrada.resolve()) or not VIDEO.is_file():
    raise RuntimeError("No se pudo guardar el video en la sesión. Vuelve a subirlo.")
del subidos
print("Video preparado:", VIDEO.name)
'''), code('''#@title ▶ 3. Crear los clips en Google
#@markdown Puedes dejar estos valores como están. Las partes pesadas se ejecutan en Google.
Cantidad_de_clips = 3 #@param {type:"slider", min:1, max:6, step:1}
Duracion_maxima_segundos = 30 #@param {type:"slider", min:10, max:90, step:5}
Idioma = "Español" #@param ["Español", "Inglés", "Detectar automáticamente"]

if "VIDEO" not in globals():
    raise RuntimeError("Ejecuta el paso 2 y selecciona un video.")
idiomas = {"Español": "es", "Inglés": "en", "Detectar automáticamente": ""}
RESULTADO_ZIP = peakcut.process(CARPETA, VIDEO, max_clips=Cantidad_de_clips,
                              max_length=Duracion_maxima_segundos, language=idiomas[Idioma])
'''), code('''#@title ▶ 4. Descargar mis clips
from google.colab import files
if not globals().get("RESULTADO_ZIP") or not RESULTADO_ZIP.is_file():
    raise RuntimeError("Primero termina el paso 3: Crear los clips.")
files.download(str(RESULTADO_ZIP))
print("Descargando tus clips. Guarda el ZIP antes de cerrar la sesión.")
'''), markdown('''Para otro video, vuelve a ejecutar los pasos **2, 3 y 4**, o pulsa otra vez **Ejecutar todo**.

Esta es una adaptación de [PeakCut](https://github.com/haziqahmedqasmi/PeakCut) para un cuaderno interactivo. El código y el modelo proceden del [paquete preparado en GitHub](https://github.com/luisalisman-bot/luis/releases/tag/peakcut-windows-v1.0.0). No incluye publicación automática en redes ni el editor completo de la aplicación de escritorio.
''')]
notebook = {'nbformat': 4, 'nbformat_minor': 0, 'metadata': {'colab': {'name': 'PeakCut gratis en la nube', 'provenance': []},
              'kernelspec': {'display_name': 'Python 3', 'name': 'python3'}, 'language_info': {'name': 'python'}}, 'cells': cells}
(ROOT / 'PeakCut_Gratis_Colab.ipynb').write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Notebook generated with runtime hash', runtime_hash)
