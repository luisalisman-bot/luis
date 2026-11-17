"""Run with the bundled Windows interpreter before publishing the ZIP."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(sys.argv[1]).resolve()
SAMPLE = Path(sys.argv[2]).resolve()
assert sys.platform == 'win32'
sys.path.insert(0, str(ROOT))
import httpx

python = ROOT / 'runtime/python.exe'
env = dict(os.environ)
env.update(PEAKCUT_PORTABLE_CHECK='1', PEAKCUT_UPDATE_CHECK='0')
opened = subprocess.run(['cmd.exe', '/d', '/c', str(ROOT / 'ABRIR_PEAKCUT.cmd')], cwd=ROOT,
                        env=env, capture_output=True, text=True, encoding='utf-8', timeout=120)
print(opened.stdout)
print(opened.stderr)
assert opened.returncode == 0 and 'PEAKCUT_WINDOWS_STARTUP_OK' in opened.stdout, 'Windows launcher did not complete'

with tempfile.TemporaryDirectory(prefix='peakcut-ci-') as tmp:
    work = Path(tmp)
    base = 'http://127.0.0.1:8787'
    env.update(PEAKCUT_DATA=str(work / 'data'), PEAKCUT_MODELS=str(ROOT / 'models'),
               PEAKCUT_ASR_BACKEND='whisper', PEAKCUT_ASR_LANGUAGE='en',
               PEAKCUT_CAPTION_LANGUAGE='original', PEAKCUT_FETCH_MODEL='0',
               PEAKCUT_PORT='8787', PEAKCUT_PUBLIC_URL=base, PEAKCUT_ACCOUNTS='0',
               PEAKCUT_HOST='127.0.0.1', PEAKCUT_YT_TRANSCRIPT='0', PEAKCUT_JOB_WORKERS='1')
    env['PATH'] = str(ROOT / 'bin') + os.pathsep + str(ROOT / 'runtime') + os.pathsep + env.get('PATH', '')
    video = work / 'test.mp4'
    subprocess.run([str(ROOT / 'bin/ffmpeg.exe'), '-y', '-loglevel', 'error', '-f', 'lavfi',
                    '-i', 'testsrc2=size=640x360:rate=12', '-i', str(SAMPLE), '-c:v', 'libx264',
                    '-preset', 'ultrafast', '-c:a', 'aac', '-shortest', str(video)], env=env, check=True, timeout=90)
    with (work / 'server.log').open('w', encoding='utf-8') as log:
        server = subprocess.Popen([str(python), '-E', '-s', '-X', 'utf8', '-m', 'studio.server'],
                                   cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            client = httpx.Client(base_url=base, headers={'Origin': base}, timeout=60)
            for _ in range(120):
                try:
                    if client.get('/healthz').status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                if server.poll() is not None:
                    raise RuntimeError((work / 'server.log').read_text(errors='replace'))
                time.sleep(0.5)
            assert client.get('/app').status_code == 200
            with video.open('rb') as file:
                response = client.post('/api/upload', files={'file': ('test.mp4', file, 'video/mp4')},
                                       data={'options': json.dumps({'max_clips': 1, 'min_len': 5, 'max_len': 10, 'captions': True})})
            response.raise_for_status()
            job = response.json()
            for _ in range(300):
                job = client.get('/api/jobs/' + job['id']).json()
                if job.get('status') in ('done', 'error'):
                    break
                time.sleep(1)
            assert job.get('status') == 'done', job
            assert job.get('word_count', 0) >= 10, job
            assert any(c.get('status') == 'done' for c in job['clips']), job
            clip = next((work / 'data').rglob('clip01.mp4'))
            result = subprocess.run([str(ROOT / 'bin/ffprobe.exe'), '-v', 'error', '-show_entries',
                                     'stream=codec_name,width,height', '-of', 'json', str(clip)],
                                    env=env, capture_output=True, text=True, check=True)
            streams = json.loads(result.stdout)['streams']
            assert any(s.get('codec_name') == 'h264' and s.get('width') == 1080 and s.get('height') == 1920 for s in streams)
            assert any(s.get('codec_name') == 'aac' for s in streams)
            words_file = next((work / 'data').rglob('words.json'))
            words = json.loads(words_file.read_text(encoding='utf-8'))
            assert len(words) >= 10
            assert all(w['e'] > w['s'] >= 0 for w in words)
            print('Windows end-to-end clip export passed:', job['word_count'], 'words')
        finally:
            server.terminate()
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
    (ROOT / 'COMPROBACIONES-WINDOWS.txt').write_text(
        'Verificado en GitHub Actions, Windows x64, con el Python incluido en el ZIP.\n'
        'El iniciador ABRIR_PEAKCUT.cmd arranca y comprueba el servidor.\n'
        'Se sube un video de prueba publico, se transcribe con tiempos de palabras,\n'
        'y se exporta un clip H.264 + AAC de 1080 x 1920 con subtitulos.\n'
        'No se usa clave API. La prueba Windows usa un audio publico en ingles;\n'
        'la transcripcion en espanol se verifico tambien en Linux.\n'
        'Los enlaces y las publicaciones en redes sociales no se probaron.\n', encoding='utf-8')
    # The release readme refers to both sets of checks without claiming every platform or service was tested.
    text = (ROOT / 'LEEME.txt').read_text(encoding='utf-8')
    text = text.replace('No se ha ejecutado este paquete en un equipo Windows durante esta entrega.',
                        'El iniciador y la exportacion se han verificado en Windows en GitHub Actions.')
    text = text.replace('Consulta COMPROBACIONES.txt para los resultados y limites exactos.',
                        'Consulta COMPROBACIONES-WINDOWS.txt y COMPROBACIONES-LINUX.txt.')
    (ROOT / 'LEEME.txt').write_text(text, encoding='utf-8')
