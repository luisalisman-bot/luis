"""Run PeakCut inside an interactive Google Colab notebook, using its cloud CPU.

No public server, tunnel, billing API, external chat model or local-PC worker
is used. This helper also supports ordinary Linux for an integration check.
"""
from pathlib import Path
import hashlib
import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import uuid
import venv
import zipfile

ARCHIVE_URL = 'https://github.com/luisalisman-bot/luis/releases/download/peakcut-windows-v1.0.0/PeakCut-Windows.zip'
ARCHIVE_SHA256 = '86719ac3471106db507d089477c51b7b184d5c277fb7e540b7714818d077ebb4'
VIDEO_TYPES = {'.mp4', '.mov', '.mkv', '.webm', '.m4v', '.ts', '.flv'}


def interpreter(root):
    return Path(root) / 'entorno/bin/python'


def install(root, message=print, archive_file=None):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    stamp = root / 'instalado.json'
    version = {'archive': ARCHIVE_SHA256, 'python': list(sys.version_info[:2])}
    if stamp.is_file() and interpreter(root).is_file():
        if json.loads(stamp.read_text()) == version:
            message('PeakCut ya esta preparado en esta sesion de Google.')
            return root
    if sys.platform != 'linux':
        raise RuntimeError('Abre este cuaderno en Google Colab con su entorno alojado de Python.')
    archive = Path(archive_file) if archive_file else root / 'paquete.zip'
    if not archive.exists():
        message('Descargando el motor en la nube. Tu PC no lo ejecuta...')
        with urllib.request.urlopen(ARCHIVE_URL, timeout=180) as response, archive.open('wb') as file:
            shutil.copyfileobj(response, file)
    with archive.open('rb') as file:
        digest = hashlib.file_digest(file, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else hashlib.sha256(file.read()).hexdigest()
    if digest != ARCHIVE_SHA256:
        if archive_file is None:
            archive.unlink(missing_ok=True)
        raise RuntimeError('La descarga no esta completa. Vuelve a ejecutar Preparar PeakCut.')
    app = root / 'app'
    with zipfile.ZipFile(archive) as package:
        for item in package.infolist():
            if item.is_dir():
                continue
            name = item.filename
            if not (name.startswith(('PeakCut/studio/', 'PeakCut/web/', 'PeakCut/models/whisper-base/'))
                    or name in ('PeakCut/requirements.txt', 'PeakCut/LICENSE')):
                continue
            rel = Path(name).relative_to('PeakCut')
            if '..' in rel.parts or rel.is_absolute():
                raise RuntimeError('El paquete contiene una ruta inesperada.')
            target = app / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(package.read(item))
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        message('Preparando las herramientas de video en Google...')
        subprocess.run(['apt-get', 'update', '-qq'], check=True)
        subprocess.run(['apt-get', 'install', '-y', '-qq', 'ffmpeg'], check=True)
    message('Instalando los componentes en una carpeta aislada de la sesion...')
    if not interpreter(root).is_file():
        venv.EnvBuilder(with_pip=True).create(root / 'entorno')
    with (root / 'instalacion.log').open('w') as log:
        result = subprocess.run([str(interpreter(root)), '-m', 'pip', 'install', '--disable-pip-version-check',
                                 '-r', str(app / 'requirements.txt')], stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('No se pudo preparar el motor. Detalle:\n' + (root / 'instalacion.log').read_text(errors='replace')[-2500:])
    stamp.write_text(json.dumps(version))
    message('Listo. Elige tu video en el siguiente paso.')
    return root


def server_environment(root, data, port, language='es'):
    root, data = Path(root), Path(data)
    env = dict(os.environ)
    env.update(PEAKCUT_DATA=str(data), PEAKCUT_MODELS=str(root / 'app/models'),
               PEAKCUT_HOST='127.0.0.1', PEAKCUT_PORT=str(port), PEAKCUT_PUBLIC_URL=f'http://127.0.0.1:{port}',
               PEAKCUT_ACCOUNTS='0', PEAKCUT_ASR_BACKEND='whisper', PEAKCUT_ASR_LANGUAGE=language,
               PEAKCUT_CAPTION_LANGUAGE='original', PEAKCUT_FETCH_MODEL='0', PEAKCUT_UPDATE_CHECK='0',
               PEAKCUT_AUTO_RELOAD='0', PEAKCUT_TRUST_PROXY='', PEAKCUT_YT_TRANSCRIPT='0',
               PEAKCUT_JOB_WORKERS='1', PEAKCUT_ASR_COPIES='1', PEAKCUT_ASR_THREADS='2',
               PEAKCUT_REQUEST_THREADS='8', PEAKCUT_AI_KEY='', PEAKCUT_AI_KEY_FILE='',
               PEAKCUT_AI_MODELS='', DATABASE_URL='', OMP_NUM_THREADS='2')
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONHOME', None)
    return env


def upload(port, video, options):
    video = Path(video)
    boundary = 'peakcut' + uuid.uuid4().hex
    prefix = (f'--{boundary}\r\nContent-Disposition: form-data; name="options"\r\n\r\n'
              + json.dumps(options) + f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; '
              + f'filename="video{video.suffix.lower()}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()
    suffix = f'\r\n--{boundary}--\r\n'.encode()
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=180)
    try:
        connection.putrequest('POST', '/api/upload')
        connection.putheader('Origin', f'http://127.0.0.1:{port}')
        connection.putheader('Content-Type', 'multipart/form-data; boundary=' + boundary)
        connection.putheader('Content-Length', str(len(prefix) + video.stat().st_size + len(suffix)))
        connection.endheaders()
        connection.send(prefix)
        with video.open('rb') as file:
            while block := file.read(1024 * 1024):
                connection.send(block)
        connection.send(suffix)
        response = connection.getresponse()
        payload = json.loads(response.read())
        if response.status >= 400:
            raise RuntimeError(payload.get('detail', 'No se pudo leer el video.'))
        return payload
    finally:
        connection.close()


def export_result(data, job, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    jobdir = Path(data) / 'users/u_local/jobs' / job['id']
    result = destination / (job['id'] + '-clips.zip')
    clips = [c for c in job.get('clips', []) if c.get('status') == 'done']
    if not clips:
        raise RuntimeError('No se genero ningun clip. Prueba un video con voz clara y de al menos 20 segundos.')
    with zipfile.ZipFile(result, 'w', zipfile.ZIP_STORED) as archive:
        for index, clip in enumerate(clips, 1):
            # Names come from a completed job, but keep every exported file inside its clip folder.
            source = (jobdir / 'clips' / Path(clip['file']).name).resolve()
            if not source.is_relative_to((jobdir / 'clips').resolve()) or not source.is_file():
                raise RuntimeError('No se pudo encontrar uno de los clips terminados.')
            archive.write(source, f'clip_{index:02d}.mp4')
        archive.writestr('LEEME.txt', 'Clips creados en tu sesion de Google Colab.\n'
                        'Seleccion basica por volumen, sin proveedor de IA de pago.\n'
                        'Los subtitulos son automaticos: revisalos antes de publicar.\n')
    return result


def process(root, video, max_clips=3, max_length=30, language='es', message=print):
    root, video = Path(root).resolve(), Path(video).resolve()
    if not interpreter(root).is_file() or not (root / 'instalado.json').is_file():
        raise RuntimeError('Ejecuta primero Preparar PeakCut.')
    if not video.is_file() or video.suffix.lower() not in VIDEO_TYPES:
        raise RuntimeError('Selecciona un archivo de video MP4, MOV, MKV o WEBM.')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    data = root / 'sesiones' / uuid.uuid4().hex
    data.mkdir(parents=True)
    env = server_environment(root, data, port, language)
    base = f'http://127.0.0.1:{port}'
    logpath = data / 'motor.log'
    stages = {'Getting the audio': 'Leyendo el audio', 'Writing the transcript': 'Transcribiendo la voz',
              'Finishing the clips': 'Creando los clips con subtitulos', 'Waiting': 'Preparando el video',
              'Done': 'Terminado'}
    with logpath.open('w', encoding='utf-8') as log:
        server = subprocess.Popen([str(interpreter(root)), '-E', '-s', '-X', 'utf8', '-m', 'studio.server'],
                                   cwd=root / 'app', env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(120):
                try:
                    with urllib.request.urlopen(base + '/healthz', timeout=2):
                        break
                except OSError:
                    if server.poll() is not None:
                        raise RuntimeError('El motor no pudo iniciar.\n' + logpath.read_text(errors='replace')[-2000:])
                    time.sleep(0.5)
            else:
                raise RuntimeError('El motor esta tardando demasiado. Vuelve a ejecutar este paso.')
            job = upload(port, video, {'max_clips': max(1, min(6, int(max_clips))), 'min_len': 5,
                                      'max_len': max(10, min(90, int(max_length))), 'captions': True})
            last = None
            while True:
                if server.poll() is not None:
                    raise RuntimeError('La sesion detuvo el motor.\n' + logpath.read_text(errors='replace')[-2000:])
                with urllib.request.urlopen(base + '/api/jobs/' + job['id'], timeout=10) as response:
                    job = json.load(response)
                stage = job.get('stage', '')
                progress = int(float(job.get('progress', 0)) * 100)
                state = (stage, progress // 10)
                if state != last:
                    message(f'{stages.get(stage, "Procesando el video")}: {progress}%')
                    last = state
                if job.get('status') == 'error':
                    raise RuntimeError(job.get('error') or 'No se pudo procesar este video.')
                if job.get('status') == 'done':
                    break
                time.sleep(2)
            result = export_result(data, job, root / 'resultados')
            message('Clips preparados. Descarga el ZIP en el ultimo paso.')
            return result
        finally:
            server.terminate()
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
