"""Build the Windows ZIP from pinned public distributions and checked-in source."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'work'
DOWNLOADS = WORK / 'downloads'
PACKAGE = WORK / 'PeakCut-Windows'
OUT = ROOT / 'dist'


def download(item):
    target = DOWNLOADS / item['file']
    if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != item['sha256']:
        print('Downloading', item['file'], flush=True)
        req = urllib.request.Request(item['url'], headers={'User-Agent': 'PeakCut-Windows-builder'})
        with urllib.request.urlopen(req, timeout=180) as response, target.open('wb') as file:
            shutil.copyfileobj(response, file)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == item['sha256'], target
    return target


def extract_wheel(wheel, runtime):
    site = runtime / 'Lib/site-packages'
    with zipfile.ZipFile(wheel) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            rel = Path(member.filename)
            if rel.parts[0].endswith('.data'):
                kind, sub = rel.parts[1], Path(*rel.parts[2:])
                if kind in ('purelib', 'platlib'):
                    target = site / sub
                elif kind == 'data':
                    target = runtime / sub
                elif kind == 'scripts':
                    target = runtime / 'Scripts' / sub
                else:
                    continue
            else:
                target = site / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))


def build():
    for path in (WORK, DOWNLOADS, PACKAGE, OUT):
        path.mkdir(parents=True, exist_ok=True)
    assets = json.loads((ROOT / 'distribution/assets.json').read_text())
    files = {key: download(value) for key, value in assets.items()}
    wheels = DOWNLOADS / 'wheels'
    wheels.mkdir(exist_ok=True)
    subprocess.run([sys.executable, '-m', 'pip', 'download', '--only-binary=:all:', '--require-hashes',
                    '--platform', 'win_amd64', '--python-version', '312', '--implementation', 'cp', '--abi', 'cp312',
                    '--dest', str(wheels), '-r', str(ROOT / 'distribution/windows-requirements.lock')], check=True)
    for name in ('studio', 'web', 'tests'):
        shutil.copytree(ROOT / name, PACKAGE / name, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('LICENSE', 'README.md', 'README-ORIGINAL.md', 'requirements.txt', '.env.example',
                 'iniciar.py', 'ABRIR_PEAKCUT.cmd', 'LEEME.txt'):
        shutil.copy2(ROOT / name, PACKAGE / name)
    # Always retain CRLF for the Windows entry point regardless of Git settings.
    launcher = PACKAGE / 'ABRIR_PEAKCUT.cmd'
    launcher.write_bytes(launcher.read_text().replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8'))
    shutil.copy2(ROOT / 'portable.env', PACKAGE / '.env')
    shutil.copytree(ROOT / 'distribution/licencias', PACKAGE / 'licencias', dirs_exist_ok=True)
    shutil.copytree(ROOT / 'distribution/fuentes-modelo', PACKAGE / 'fuentes-modelo', dirs_exist_ok=True)
    shutil.copy2(ROOT / 'distribution/COMPROBACIONES-LINUX.txt', PACKAGE / 'COMPROBACIONES-LINUX.txt')
    runtime = PACKAGE / 'runtime'
    with zipfile.ZipFile(files['python']) as archive:
        for member in archive.infolist():
            if member.is_dir() or not member.filename.startswith('tools/'):
                continue
            rel = Path(member.filename.removeprefix('tools/'))
            if rel.parts[0].lower() in ('include', 'libs'):
                continue
            target = runtime / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
    for wheel in wheels.glob('*.whl'):
        extract_wheel(wheel, runtime)
    with zipfile.ZipFile(files['ffmpeg']) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            rel = Path(*Path(member.filename).parts[1:])
            if rel.parts[0] == 'bin':
                if rel.name == 'ffplay.exe':
                    continue
                target = PACKAGE / rel
            else:
                target = PACKAGE / 'licencias/ffmpeg' / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
    with zipfile.ZipFile(files['deno']) as archive:
        (PACKAGE / 'bin/deno.exe').write_bytes(archive.read('deno.exe'))
    # Only the compact models and a public test recording are required.
    model_source = WORK / 'whisper-base'
    with tarfile.open(files['whisper'], 'r|bz2') as archive:
        for member in archive:
            if not member.isfile():
                continue
            parts = Path(member.name).parts
            if not (member.name.endswith('.int8.onnx') or member.name.endswith('-tokens.txt')
                    or member.name.endswith('test_wavs/1.wav')):
                continue
            target = model_source / Path(*parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, target.open('wb') as dest:
                shutil.copyfileobj(source, dest)
    shutil.copy2(ROOT / 'distribution/fuentes-modelo/whisper-init.py', WORK / 'whisper-init.py')
    subprocess.run([sys.executable, str(ROOT / 'distribution/fuentes-modelo/preparar_modelo.py')], cwd=ROOT, check=True)
    shutil.copytree(WORK / 'model-whisper-base', PACKAGE / 'models/whisper-base', dirs_exist_ok=True)
    shutil.copy2(ROOT / 'distribution/windows-requirements.lock', PACKAGE / 'dependencias-windows.lock')
    print('Portable Windows files prepared', flush=True)


def pack():
    if not (PACKAGE / 'COMPROBACIONES-WINDOWS.txt').exists():
        raise RuntimeError('The Windows smoke test must pass before packaging a release.')
    # All test data are outside the package; the launcher test only creates this log folder.
    shutil.rmtree(PACKAGE / 'data', ignore_errors=True)
    manifest = {}
    for path in sorted(PACKAGE.rglob('*')):
        if path.is_file() and path.suffix.lower() in ('.exe', '.dll', '.pyd', '.onnx'):
            manifest[path.relative_to(PACKAGE).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    (PACKAGE / 'integridad.json').write_text(json.dumps(manifest, indent=2))
    destination = OUT / 'PeakCut-Windows.zip'
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(PACKAGE.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                archive.write(path, Path('PeakCut') / path.relative_to(PACKAGE))
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
    sha = hashlib.sha256(destination.read_bytes()).hexdigest()
    (OUT / 'PeakCut-Windows.sha256.txt').write_text(f'{sha}  PeakCut-Windows.zip\n')
    print('ZIP ready:', destination.stat().st_size, 'bytes; SHA256', sha, flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'pack':
        pack()
    else:
        build()
