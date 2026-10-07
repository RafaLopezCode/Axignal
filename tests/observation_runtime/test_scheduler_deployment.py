"""Run unchanged with pytest, or stdlib unittest in the Linux candidate image."""

from __future__ import annotations

import configparser
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "production"


class SchedulerUnitContract(unittest.TestCase):
    def test_timer_wakes_one_existing_runtime_entry_and_bounds_its_lifetime(self) -> None:
        timer, service = configparser.ConfigParser(), configparser.ConfigParser()
        timer.read(DEPLOY / "axignal-observation-daily.timer")
        service.read(DEPLOY / "axignal-observation-daily.service")
        self.assertEqual(timer["Timer"]["Unit"], "axignal-observation-daily.service")
        self.assertEqual(timer["Timer"]["OnCalendar"], "*-*-* 03:17:00 UTC")
        self.assertEqual(timer["Timer"]["Persistent"], "true")
        self.assertEqual(service["Service"]["Type"], "oneshot")
        self.assertEqual(service["Service"]["TimeoutStartSec"], "30min")
        self.assertEqual(
            service["Service"]["ExecStart"],
            "/bin/sh /srv/axignal/docker/current/deploy/production/run-observation-daily.sh",
        )
        self.assertEqual(
            service["Service"]["ExecStopPost"],
            "-/usr/bin/docker stop --time 15 axignal-prod-observation-daily",
        )
        self.assertIn(
            "AXIGNAL_OBSERVATION_RUNTIME_ENABLED=false",
            (DEPLOY / "observation-scheduler.env.example").read_text(),
        )


@unittest.skipUnless(
    os.name == "posix" and Path("/usr/bin/flock").exists(),
    "POSIX deployment; exercised in isolated Linux candidate",
)
class SchedulerRunnerIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.release = self.root / ("a" * 40)
        self.release.mkdir()
        self.config = self.root / "config"
        self.config.mkdir()
        self.data = self.root / "data"
        self.data.mkdir()
        for name in ("attention.json", "enrollment.json"):
            (self.config / name).write_text("[]")
        self.log = self.root / "docker-calls.jsonl"
        self.driver = self.root / "docker-driver"
        self.driver.write_text(
            f"#!{sys.executable}\n"
            + """import json,os,subprocess,sys,time
from pathlib import Path
a=sys.argv[1:]
with open(os.environ['TEST_DOCKER_LOG'],'a') as f: f.write(json.dumps(a)+'\\n')
if a[:2]==['container','inspect']: sys.exit(1)
if a[:2]==['image','inspect']: sys.exit(0)
if a[0]!='run': sys.exit(99)
assert a[-2:]==['-m','tools.runtime.observation_daily']
if os.getenv('TEST_GATE'):
    p=Path(os.environ['TEST_GATE']); p.with_suffix('.entered').write_text('entered')
    deadline=time.monotonic()+10
    while p.exists() and time.monotonic()<deadline: time.sleep(0.01)
    assert not p.exists(), 'test gate timed out'
if os.getenv('TEST_DOCKER_FAILURE'): sys.exit(7)
env={**os.environ,'AXIGNAL_DATA_DIR':os.environ['TEST_DATA_DIR'],
     'AXIGNAL_SUBSCRIBER_OBSERVATION_PLAN_FILE':os.environ['TEST_CONFIG_DIR']+'/attention.json',
     'AXIGNAL_OBSERVATION_RUNTIME_ENROLLMENT_FILE':os.environ['TEST_CONFIG_DIR']+'/enrollment.json'}
sys.exit(subprocess.run([sys.executable,'-m','tools.runtime.observation_daily'],env=env).returncode)
"""
        )
        self.driver.chmod(0o755)
        self.env = {
            **os.environ,
            "AXIGNAL_OBSERVATION_RUNTIME_ENABLED": "true",
            "AXIGNAL_OBSERVATION_RELEASE": str(self.release),
            "AXIGNAL_OBSERVATION_CONFIG_DIR": str(self.config),
            "AXIGNAL_DATA_DIR": str(self.data),
            "AXIGNAL_OBSERVATION_DOCKER": str(self.driver),
            "AXIGNAL_OBSERVATION_NETWORK": "none",
            "AXIGNAL_OBSERVATION_CONTAINER_NAME": "axignal-t12-test",
            "PYTHONPATH": str(ROOT),
            "TEST_DOCKER_LOG": str(self.log),
            "TEST_DATA_DIR": str(self.data),
            "TEST_CONFIG_DIR": str(self.config),
        }

    def run_script(self, **env: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["/bin/sh", str(DEPLOY / "run-observation-daily.sh")],
            env={**self.env, **env},
            capture_output=True,
            text=True,
            timeout=20,
        )

    def calls(self) -> list[list[str]]:
        return (
            []
            if not self.log.exists()
            else [json.loads(line) for line in self.log.read_text().splitlines()]
        )

    def test_one_wakeup_one_entry_and_safe_no_work(self) -> None:
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["stop"], "NOTHING_DUE")
        self.assertEqual(json.loads(result.stdout)["requests"], 0)
        runs = [c for c in self.calls() if c[0] == "run"]
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0][-2:], ["-m", "tools.runtime.observation_daily"])
        self.assertNotIn("--publish", runs[0])
        self.assertIn("--read-only", runs[0])
        replay = self.run_script()
        self.assertEqual(json.loads(replay.stdout)["state"], "ALREADY_COMPLETED")

    def test_disabled_or_missing_config_never_invokes_docker(self) -> None:
        result = self.run_script(AXIGNAL_OBSERVATION_RUNTIME_ENABLED="false")
        self.assertEqual(json.loads(result.stdout)["state"], "DISABLED")
        (self.config / "enrollment.json").unlink()
        result = self.run_script()
        self.assertEqual(json.loads(result.stdout)["state"], "NOT_CONFIGURED")
        self.assertFalse(self.calls())
        self.assertFalse((self.data / "observation-runtime.sqlite3").exists())

    def test_overlapping_wakeups_do_not_enter_the_runtime_twice(self) -> None:
        gate = self.root / "gate"
        gate.touch()
        first = subprocess.Popen(
            ["/bin/sh", str(DEPLOY / "run-observation-daily.sh")],
            env={**self.env, "TEST_GATE": str(gate)},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.monotonic() + 10
            while not gate.with_suffix(".entered").exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(gate.with_suffix(".entered").exists())
            second = self.run_script()
            self.assertEqual(json.loads(second.stdout)["state"], "INVOCATION_HELD")
        finally:
            gate.unlink(missing_ok=True)
            stdout, stderr = first.communicate(timeout=15)
        self.assertEqual(first.returncode, 0, stderr)
        self.assertEqual(json.loads(stdout)["state"], "COMPLETED")
        self.assertEqual(len([c for c in self.calls() if c[0] == "run"]), 1)

    def test_container_failure_and_bad_configuration_are_bounded(self) -> None:
        failed = self.run_script(TEST_DOCKER_FAILURE="true")
        self.assertEqual(failed.returncode, 7)
        self.assertEqual(len([c for c in self.calls() if c[0] == "run"]), 1)
        (self.config / "enrollment.json").write_text("invalid private content")
        bad = self.run_script()
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(json.loads(bad.stdout)["state"], "INVALID_CONFIGURATION")
        self.assertNotIn("private content", bad.stdout + bad.stderr)
        self.assertFalse((self.data / "observation-runtime.sqlite3").exists())


if __name__ == "__main__":
    unittest.main()
