"""Exercise the cloud notebook's actual Linux processing path on a public sample."""
from pathlib import Path
import importlib.util
import os
import subprocess
import tempfile
import urllib.request
import zipfile
import json

spec = importlib.util.spec_from_file_location('colab_runtime', Path(__file__).with_name('runtime.py'))
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)
root = Path(os.environ.get('PEAKCUT_COLAB_TEST_ROOT', '/tmp/peakcut-colab-check')).resolve()
archive = os.environ.get('PEAKCUT_COLAB_TEST_ARCHIVE')
runtime.install(root, archive_file=archive)
with tempfile.TemporaryDirectory() as folder:
    sample = Path(folder) / 'sample.wav'
    with urllib.request.urlopen('https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/samples/jfk.wav', timeout=60) as response:
        sample.write_bytes(response.read())
    video = Path(folder) / 'sample.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=12',
                    '-i', str(sample), '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', '-shortest', str(video)], check=True)
    result = runtime.process(root, video, max_clips=1, max_length=10, language='en')
    with zipfile.ZipFile(result) as package:
        assert package.testzip() is None
        assert 'clip_01.mp4' in package.namelist()
        target = Path(folder) / 'export.mp4'
        target.write_bytes(package.read('clip_01.mp4'))
    info = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,width,height',
                           '-of', 'json', str(target)], capture_output=True, text=True, check=True)
    streams = json.loads(info.stdout)['streams']
    assert any(s.get('codec_name') == 'h264' and s.get('width') == 1080 and s.get('height') == 1920 for s in streams)
    assert any(s.get('codec_name') == 'aac' for s in streams)
    print('COLAB_PROCESSING_CHECK_OK:', result)
