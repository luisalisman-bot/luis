from pathlib import Path
import importlib.util
import json
import os
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location('colab_runtime', Path(__file__).with_name('runtime.py'))
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

class ColabTests(unittest.TestCase):
    def test_no_paid_ai_or_public_server(self):
        with patch.dict(os.environ, {'PEAKCUT_AI_KEY': 'dummy-test-value', 'PEAKCUT_AI_MODELS': 'paid-model',
                                     'PEAKCUT_AI_KEY_FILE': '/unrelated/key', 'DATABASE_URL': 'postgresql://example'}):
            env = runtime.server_environment('/tmp/app', '/tmp/private', 9876)
        self.assertEqual(env['PEAKCUT_HOST'], '127.0.0.1')
        self.assertEqual(env['PEAKCUT_AI_KEY'], '')
        self.assertEqual(env['PEAKCUT_AI_MODELS'], '')
        self.assertEqual(env['PEAKCUT_AI_KEY_FILE'], '')
        self.assertEqual(env['DATABASE_URL'], '')
        self.assertEqual(env['PEAKCUT_ASR_BACKEND'], 'whisper')

    def test_only_finished_clips_are_exported(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            clips = base / 'data/users/u_local/jobs/test-job/clips'
            clips.mkdir(parents=True)
            (clips / 'clip01.mp4').write_bytes(b'clip')
            (clips / 'clip02.mp4').write_bytes(b'incomplete')
            (clips.parent / 'source.mp4').write_bytes(b'private source')
            job = {'id': 'test-job', 'clips': [{'status': 'done', 'file': 'clip01.mp4'},
                                               {'status': 'error', 'file': 'clip02.mp4'}]}
            result = runtime.export_result(base / 'data', job, base / 'out')
            with zipfile.ZipFile(result) as archive:
                self.assertEqual(set(archive.namelist()), {'clip_01.mp4', 'LEEME.txt'})
                self.assertEqual(archive.read('clip_01.mp4'), b'clip')

    def test_unverified_package_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            bad = base / 'bad.zip'
            bad.write_bytes(b'incomplete')
            with patch('urllib.request.urlopen', side_effect=AssertionError('unexpected request')):
                with self.assertRaisesRegex(RuntimeError, 'descarga'):
                    runtime.install(base / 'app', message=lambda _: None, archive_file=bad)

    def test_notebook_has_no_saved_user_outputs_and_cells_compile(self):
        notebook = json.loads((Path(__file__).resolve().parent.parent / 'PeakCut_Gratis_Colab.ipynb').read_text())
        self.assertEqual(notebook['nbformat'], 4)
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                self.assertEqual(cell['outputs'], [])
                self.assertIsNone(cell['execution_count'])
                compile(''.join(cell['source']), 'colab-cell', 'exec')

if __name__ == '__main__':
    unittest.main()
