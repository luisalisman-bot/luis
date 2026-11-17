"""Open the portable edition without installing anything on Windows."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent


def alive(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=1) as r:
            return json.load(r).get("ok") is True
    except (OSError, ValueError):
        return False


def available_port():
    for port in range(8765, 8795):
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                pass
    raise RuntimeError("No hay un puerto local disponible. Cierra otras copias de PeakCut.")


def main():
    os.chdir(ROOT)
    if sys.platform != "win32" or sys.maxsize < 2**32:
        raise RuntimeError("Este paquete es para Windows de 64 bits.")
    required = [ROOT / "runtime/python.exe", ROOT / "bin/ffmpeg.exe", ROOT / "bin/ffprobe.exe",
                ROOT / "models/whisper-base/base-encoder.int8.onnx",
                ROOT / "models/whisper-base/base-decoder.int8.onnx",
                ROOT / "models/whisper-base/base-tokens.txt"]
    if any(not p.is_file() for p in required):
        raise RuntimeError("Faltan archivos. Haz clic derecho en el ZIP, elige Extraer todo y abre la carpeta extraida.")
    data = ROOT / "data"
    data.mkdir(exist_ok=True)
    state = data / "sesion-portatil.json"
    try:
        previous = json.loads(state.read_text(encoding="utf-8"))
        port = int(previous["port"])
        if 8765 <= port < 8795 and alive(port):
            webbrowser.open(f"http://127.0.0.1:{port}/app")
            return
    except (OSError, ValueError, KeyError, TypeError):
        pass
    port = available_port()
    base = f"http://127.0.0.1:{port}"
    env = dict(os.environ)
    env.update(PEAKCUT_HOST="127.0.0.1", PEAKCUT_PORT=str(port), PEAKCUT_PUBLIC_URL=base,
               PEAKCUT_ACCOUNTS="0", PEAKCUT_AUTO_RELOAD="0", PEAKCUT_TRUST_PROXY="",
               PEAKCUT_ASR_BACKEND="whisper", PEAKCUT_CAPTION_LANGUAGE="original",
               PEAKCUT_MODELS=str(ROOT / "models"), PEAKCUT_FFMPEG_DIR=str(ROOT / "bin"),
               PEAKCUT_UPDATE_CHECK="0", PYTHONUNBUFFERED="1")
    env["PATH"] = str(ROOT / "runtime") + os.pathsep + str(ROOT / "bin") + os.pathsep + env.get("PATH", "")
    # Ignore unrelated global Python settings; all dependencies are in this ZIP.
    for name in ("PYTHONPATH", "PYTHONHOME"):
        env.pop(name, None)
    python = str(ROOT / "runtime/python.exe")
    log_path = data / "inicio.log"
    print("\nPeakCut para Windows\n")
    print("Comprobando componentes incluidos...")
    with log_path.open("w", encoding="utf-8") as log:
        check = subprocess.run([python, "-E", "-s", "-X", "utf8", "-c",
                                "import fastapi,numpy,sqlalchemy,soundfile; from studio.transcribe import _sherpa; _sherpa()"],
                               cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        if check.returncode:
            raise RuntimeError(f"No se pudo cargar un componente. El detalle esta en {log_path}")
        for tool in ("ffmpeg", "ffprobe"):
            checked = subprocess.run([str(ROOT / "bin" / (tool + ".exe")), "-version"],
                                     stdout=log, stderr=subprocess.STDOUT, env=env)
            if checked.returncode:
                raise RuntimeError(f"No se pudo abrir {tool}. El detalle esta en {log_path}")
        child = subprocess.Popen([python, "-E", "-s", "-X", "utf8", "-m", "studio.server"],
                                 cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(120):
                if child.poll() is not None:
                    raise RuntimeError(f"PeakCut no pudo iniciar. El detalle esta en {log_path}")
                if alive(port):
                    break
                time.sleep(0.5)
            else:
                raise RuntimeError(f"El inicio esta tardando demasiado. El detalle esta en {log_path}")
            state.write_text(json.dumps({"port": port, "pid": child.pid}), encoding="utf-8")
            print(f"Listo: {base}/app")
            print("\nSe abrira tu navegador. Sube un video para empezar.")
            print("Subtitulos en espanol. No necesitas una clave API para el recorte basico.")
            print("\nDeja esta ventana abierta mientras usas PeakCut.")
            print("Para salir, pulsa Ctrl+C o cierra esta ventana.\n")
            if os.environ.get("PEAKCUT_PORTABLE_CHECK") == "1":
                print("PEAKCUT_WINDOWS_STARTUP_OK")
                return
            webbrowser.open(base + "/app")
            child.wait()
            if child.returncode:
                raise RuntimeError(f"PeakCut se detuvo. El detalle esta en {log_path}")
        except KeyboardInterrupt:
            print("\nCerrando PeakCut...")
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            state.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\n{error}\n", file=sys.stderr)
        sys.exit(1)
