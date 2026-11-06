"""Register the interactive demo with the Jupyter server in this image."""
from pathlib import Path
import json
import sys
from jupyter_core.paths import jupyter_config_dir

root = Path(__file__).resolve().parents[1]
config_dir = Path(jupyter_config_dir())
config_dir.mkdir(parents=True, exist_ok=True)
config = {
    'ServerApp': {'jpserver_extensions': {'jupyter_server_proxy': True}},
    'ServerProxy': {
        'servers': {
            'cdss-demo': {
                'command': [sys.executable, str(root / 'cdss-ab/scripts/serve_interactive_demo.py'), '--port', '{port}'],
                'timeout': 30,
                'absolute_url': False,
                'launcher_entry': {'title': 'CDSS-AB: doctor and administrator demo'},
            }
        }
    },
}
destination = config_dir / 'jupyter_server_config.json'
existing = json.loads(destination.read_text()) if destination.exists() else {}
existing.setdefault('ServerApp', {}).setdefault('jpserver_extensions', {}).update(config['ServerApp']['jpserver_extensions'])
existing.setdefault('ServerProxy', {}).setdefault('servers', {}).update(config['ServerProxy']['servers'])
destination.write_text(json.dumps(existing, indent=2) + '\n')
