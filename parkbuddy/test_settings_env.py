"""Settings must take secrets from the environment and keep debug off by default.

Run with: python -m unittest parkbuddy.test_settings_env
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SETTINGS = Path(__file__).with_name('settings.py')
REQUIRED = {'DJANGO_SECRET_KEY': 'x', 'DB_PASSWORD': 'x', 'KHALTI_SECRET_KEY': 'x'}
MANAGED = [*REQUIRED, 'DJANGO_DEBUG', 'DJANGO_ALLOWED_HOSTS', 'SPARROW_SMS_TOKEN']
READ_SETTINGS = (
    "import json, runpy;"
    "s = runpy.run_path('parkbuddy/settings.py');"
    "print(json.dumps({k: s.get(k) for k in ['DEBUG', 'ALLOWED_HOSTS', 'SECRET_KEY', 'KHALTI_SECRET_KEY']}))"
)


def load_settings(env, dotenv=''):
    """Run a copy of settings.py in an empty project, away from any real .env."""
    with tempfile.TemporaryDirectory() as root:
        (Path(root) / 'parkbuddy').mkdir()
        shutil.copy(SETTINGS, Path(root) / 'parkbuddy' / 'settings.py')
        (Path(root) / '.env').write_text(dotenv)
        clean = {k: v for k, v in os.environ.items() if k not in MANAGED}
        return subprocess.run(
            [sys.executable, '-c', READ_SETTINGS],
            cwd=root, env={**clean, **env}, capture_output=True, text=True,
        )


class SettingsEnvTests(unittest.TestCase):
    def values(self, env, dotenv=''):
        result = load_settings(env, dotenv)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_each_required_secret_stops_startup_when_missing(self):
        for name in REQUIRED:
            env = {k: v for k, v in REQUIRED.items() if k != name}
            result = load_settings(env)
            self.assertNotEqual(result.returncode, 0, name)
            self.assertIn(name, result.stderr)

    def test_debug_is_off_unless_asked_for(self):
        self.assertFalse(self.values(REQUIRED)['DEBUG'])
        self.assertFalse(self.values({**REQUIRED, 'DJANGO_DEBUG': 'False'})['DEBUG'])
        self.assertFalse(self.values({**REQUIRED, 'DJANGO_DEBUG': 'yes please'})['DEBUG'])
        self.assertTrue(self.values({**REQUIRED, 'DJANGO_DEBUG': 'True'})['DEBUG'])

    def test_allowed_hosts_default_to_local_and_can_be_set(self):
        self.assertEqual(self.values(REQUIRED)['ALLOWED_HOSTS'], ['localhost', '127.0.0.1'])
        hosts = self.values({**REQUIRED, 'DJANGO_ALLOWED_HOSTS': 'a.example,b.example'})
        self.assertEqual(hosts['ALLOWED_HOSTS'], ['a.example', 'b.example'])

    def test_dotenv_file_is_read_and_keeps_special_characters(self):
        # Django's generated keys can contain all of these characters.
        key = 'a#b$c=d(e)&f%g'
        dotenv = f'DJANGO_SECRET_KEY={key}\nDB_PASSWORD=x\nKHALTI_SECRET_KEY=from-file\n'
        values = self.values({}, dotenv)
        self.assertEqual(values['SECRET_KEY'], key)
        self.assertEqual(values['KHALTI_SECRET_KEY'], 'from-file')

    def test_real_environment_wins_over_dotenv_file(self):
        dotenv = 'DJANGO_SECRET_KEY=x\nDB_PASSWORD=x\nKHALTI_SECRET_KEY=from-file\n'
        values = self.values({'KHALTI_SECRET_KEY': 'from-env'}, dotenv)
        self.assertEqual(values['KHALTI_SECRET_KEY'], 'from-env')


if __name__ == '__main__':
    unittest.main()
