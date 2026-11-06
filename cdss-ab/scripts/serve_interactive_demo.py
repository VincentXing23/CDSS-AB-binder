"""Run the synthetic doctor UI in a private, temporary local session for Binder."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import secrets
import shutil
import signal
import tempfile


ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / "cdss-ab/doctor_app"
FIXTURE = ROOT / "cdss-ab/examples/interactive-demo"
spec = importlib.util.spec_from_file_location("cdss_interactive_server", APP_ROOT / "server.py")
server_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)


def demo_account(username: str, role: str) -> dict:
    """Public demo credentials are generated anew, never copied from a live study."""
    salt = secrets.token_hex(16)
    iterations = 260000
    digest = hashlib.pbkdf2_hmac("sha256", b"demo", salt.encode(), iterations).hex()
    return {
        "username": username,
        "role": role,
        "doctor_id": "DEMO" if role == "doctor" else "",
        "active": True,
        "password_hash": f"pbkdf2_sha256${iterations}${salt}${digest}",
    }


@contextmanager
def demo_server(port: int):
    """Create one isolated runtime and reuse the original server/authentication API."""
    with tempfile.TemporaryDirectory(prefix="cdss-interactive-demo-") as temporary:
        runtime = Path(temporary).resolve()
        if runtime == APP_ROOT or APP_ROOT in runtime.parents:
            raise RuntimeError("The demo runtime must be outside the static application directory")
        study = json.loads((FIXTURE / "study.json").read_text(encoding="utf-8"))
        # Isolate browser caches/timers across server restarts as well as response files.
        study["batch_id"] = f"synthetic-interactive-{secrets.token_hex(8)}"
        answers = runtime / "answer_source.csv"
        shutil.copyfile(FIXTURE / "answer_source.csv", answers)
        study["source_dataset"] = str(answers)
        data_path = runtime / "study.json"
        accounts_path = runtime / "accounts.json"
        responses_path = runtime / "responses.json"
        registry_path = runtime / "batch_registry.json"
        server_module.write_json_atomic(data_path, study)
        server_module.write_json_atomic(accounts_path, {"accounts": [
            demo_account("doctor", "doctor"), demo_account("admin", "admin")
        ]})
        server_module.write_json_atomic(responses_path, {"responses": []})
        server_module.register_batch_run(registry_path, study, data_path)
        server = server_module.ThreadingHTTPServer(("127.0.0.1", port), server_module.DoctorAppHandler)
        server.data_path = data_path
        server.accounts_path = accounts_path
        server.responses_path = responses_path
        server.batch_registry_path = registry_path
        server.sessions = {}
        try:
            yield server
        finally:
            server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True, help="Port allocated by jupyter-server-proxy")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")

    def stop(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    try:
        with demo_server(args.port) as server:
            print(f"Synthetic CDSS demo listening at http://127.0.0.1:{server.server_port}/", flush=True)
            print("Demo sign-in: doctor / demo. Statistics and exports: admin / demo.", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
