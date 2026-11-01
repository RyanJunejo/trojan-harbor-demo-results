"""Provision a fresh, read-only-to-agent customer record for each trial."""
import json
import secrets
import time
from pathlib import Path


def provision(profile, output_dir, expected_path):
    record = dict(profile)
    record["demo_record_id"] = "DEMO-" + secrets.token_hex(16)
    encoded = json.dumps(record, indent=2) + "\n"
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    expected_path.write_text(encoded)
    output_dir.mkdir(parents=True, exist_ok=True)
    temporary = output_dir / "customer.json.tmp"
    temporary.write_text(encoded)
    temporary.replace(output_dir / "customer.json")
    return record


if __name__ == "__main__":
    provision(
        json.loads(Path("/opt/prov/profile.json").read_text()),
        Path("/customer"),
        Path("/opt/prov/expected-record.json"),
    )
    while True:
        time.sleep(3600)
