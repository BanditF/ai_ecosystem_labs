#!/usr/bin/env python3
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def rel(path):
    return str(ROOT / path)


def run(label, command, expect=0):
    print(f"\n== {label}")
    result = subprocess.run(command, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    if result.returncode != expect:
        raise SystemExit(
            f"{label} exited {result.returncode}, expected {expect}: {' '.join(map(str, command))}"
        )


def run_json(label, command, expect=0):
    print(f"\n== {label}")
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != expect:
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise SystemExit(
            f"{label} exited {result.returncode}, expected {expect}: {' '.join(map(str, command))}"
        )
    parsed = json.loads(result.stdout)
    print(json.dumps(parsed, indent=2))
    return parsed


def run_local_broker(py):
    print("\n== 13 local broker dry run")
    process = subprocess.Popen(
        [py, rel("13-local-broker/broker.py"), "--config", rel("13-local-broker/broker_config.dry-run.json")],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.time() + 10
        health = None
        while time.time() < deadline:
            try:
                with urllib.request.urlopen("http://127.0.0.1:8791/healthz", timeout=1) as response:
                    health = json.loads(response.read().decode("utf-8"))
                    break
            except Exception:
                time.sleep(0.2)
        if health is None:
            raise SystemExit("13 local broker failed to start")
        print(json.dumps(health, indent=2))

        body = json.dumps(
            {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello from the dry-run broker"}]}
        ).encode("utf-8")
        request = urllib.request.Request(
            "http://127.0.0.1:8791/v1/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            result = json.loads(response.read().decode("utf-8"))
        print(json.dumps(result, indent=2))
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        stderr = process.stderr.read().strip() if process.stderr else ""
        if stderr:
            print(stderr, file=sys.stderr)


def main():
    py = sys.executable
    run("reset workspace", [py, rel("reset.py")])
    run_json(
        "00 model access",
        [py, rel("00-model-access/model_cli.py"), "Hello from the lab", "--json"],
    )
    run("01 dumb CLI", [py, rel("01-cli/term_count.py"), "agent", rel("sample_docs/agents.txt")])
    run_json(
        "02 JSON wrapper",
        [py, rel("02-json-wrapper/term_count_json.py"), "agent", rel("sample_docs/agents.txt")],
    )
    run("03 protocol adapter", [py, rel("03-protocol-adapter/client_example.py")])
    run_json(
        "04 skill runner",
        [py, rel("04-skill/skill_runner.py"), "--term", "agent", "--path", rel("04-skill/sample.txt")],
    )
    run_json("05 hook allows safe call", [py, rel("05-hook/hook_runner.py"), "agent"])
    run_json("05 hook blocks sensitive call", [py, rel("05-hook/hook_runner.py"), "secret"], expect=1)
    run_json("06 agent loop", [py, rel("06-agent-loop/agent_loop.py")])
    run_json("07 task graph ready", [py, rel("07-task-graph/task_graph.py"), "ready"])
    run_json("08 coordinator claim", [py, rel("08-coordinator/coordinator.py"), "claim", "docs-worker", "docs"])
    run_json("09 host lists tools", [py, rel("09-host-cli/host_cli.py"), "tools"])
    run_json(
        "09 host requires approval",
        [
            py,
            rel("09-host-cli/host_cli.py"),
            "run",
            "term_count",
            json.dumps({"term": "agent", "files": [rel("sample_docs/agents.txt")]}),
        ],
        expect=2,
    )
    run_json(
        "09 host approved run",
        [
            py,
            rel("09-host-cli/host_cli.py"),
            "run",
            "term_count",
            json.dumps({"term": "agent", "files": [rel("sample_docs/agents.txt")]}),
            "--approve",
        ],
    )
    run_json("10 governance evals surface a failure", [py, rel("10-governance/eval_runner.py")], expect=1)
    run_json("11 capstone flow", [py, rel("11-capstone/capstone.py")])
    run_json("12 platform status", [py, rel("12-persistent-platform/gateway.py"), "status"])
    run_json(
        "12 platform remember note",
        [py, rel("12-persistent-platform/gateway.py"), "message", "cli", "remember that persistent assistants bundle many layers"],
    )
    run_json(
        "12 platform search requires approval",
        [py, rel("12-persistent-platform/gateway.py"), "message", "cli", "search agent"],
        expect=2,
    )
    run_json(
        "12 platform approved search",
        [py, rel("12-persistent-platform/gateway.py"), "message", "cli", "search agent", "--approve"],
    )
    run_json(
        "12 platform delegated search",
        [py, rel("12-persistent-platform/gateway.py"), "message", "cli", "delegate search memory", "--approve"],
    )
    run_json(
        "12 platform schedule digest",
        [py, rel("12-persistent-platform/gateway.py"), "message", "companion", "schedule digest"],
    )
    run_json("12 platform tick", [py, rel("12-persistent-platform/gateway.py"), "tick"])
    run_local_broker(py)
    print("\nAll lab smoke checks ran. Some artifacts were intentionally written for inspection.")


if __name__ == "__main__":
    main()
