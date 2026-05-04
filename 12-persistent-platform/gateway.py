#!/usr/bin/env python3
import argparse
import json
import pathlib
import subprocess
import sys
import time


ROOT = pathlib.Path("labs/12-persistent-platform")
STATE_PATH = ROOT / "state.json"
SKILLS_PATH = ROOT / "skills.json"
EVENTS_PATH = ROOT / "events.jsonl"
MESSAGES_PATH = ROOT / "messages.jsonl"
SAMPLE_FILES = [
    "labs/sample_docs/agents.txt",
    "labs/sample_docs/protocols.txt",
    "labs/sample_docs/memory.txt",
]


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_state():
    return load_json(STATE_PATH)


def save_state(state):
    save_json(STATE_PATH, state)


def load_skills():
    return load_json(SKILLS_PATH)


def append_jsonl(path, record):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")


def event(kind, **payload):
    append_jsonl(EVENTS_PATH, {"time": now(), "event": kind, **payload})


def message_record(channel, role, content, meta=None):
    append_jsonl(
        MESSAGES_PATH,
        {
            "time": now(),
            "channel": channel,
            "role": role,
            "content": content,
            "meta": meta or {},
        },
    )


def bump_channel_count(state, channel):
    state["channels"][channel]["messages"] += 1


def skill_index():
    return {skill["name"]: skill for skill in load_skills()}


def select_skill(text):
    lowered = text.lower()
    for skill in load_skills():
        prefix = skill["trigger_prefix"]
        if lowered.startswith(prefix):
            return skill
    return None


def run_search(term):
    result = subprocess.run(
        [sys.executable, "labs/02-json-wrapper/term_count_json.py", term, *SAMPLE_FILES],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {"ok": False, "error": result.stderr.strip() or "search_failed"}
    return json.loads(result.stdout)


def remember_note(state, channel, text):
    note = {
        "id": f"memory-{state['next_ids']['memory']}",
        "text": text.strip(),
        "channel": channel,
        "time": now(),
    }
    state["next_ids"]["memory"] += 1
    state["memory"].append(note)
    return {
        "ok": True,
        "skill": "remember_note",
        "memory_item": note,
        "reply": f"Stored note {note['id']}.",
    }


def search_docs(state, term):
    result = run_search(term)
    if result.get("ok"):
        state["searches"].append({"term": term, "time": now(), "summary": result.get("summary", {})})
        total = result.get("summary", {}).get("total", 0)
        reply = f"Found {total} matches for '{term}' across sample docs."
    else:
        reply = f"Search for '{term}' failed."
    result.update({"skill": "search_docs", "reply": reply})
    return result


def delegate_search(state, term):
    delegation = {
        "id": f"delegation-{state['next_ids']['delegation']}",
        "worker": "docs-worker",
        "term": term,
        "status": "running",
        "time": now(),
    }
    state["next_ids"]["delegation"] += 1
    state["delegations"].append(delegation)
    bump_channel_count(state, "ops")
    message_record("ops", "assistant", f"docs-worker accepted {delegation['id']} for '{term}'.", {"delegation_id": delegation["id"]})
    result = run_search(term)
    delegation["status"] = "done" if result.get("ok") else "failed"
    delegation["summary"] = result.get("summary", {})
    if result.get("ok"):
        state["searches"].append({"term": term, "time": now(), "summary": result.get("summary", {})})
        total = result.get("summary", {}).get("total", 0)
        reply = f"Delegated search {delegation['id']} found {total} matches for '{term}'."
    else:
        reply = f"Delegated search {delegation['id']} failed for '{term}'."
    result.update({"skill": "delegate_search", "delegation": delegation, "reply": reply})
    return result


def schedule_digest(state, channel):
    schedule = {
        "id": f"schedule-{state['next_ids']['schedule']}",
        "kind": "digest",
        "channel": channel,
        "status": "pending",
        "time": now(),
    }
    state["next_ids"]["schedule"] += 1
    state["schedules"].append(schedule)
    return {
        "ok": True,
        "skill": "schedule_digest",
        "schedule": schedule,
        "reply": f"Queued digest job {schedule['id']} for {channel}.",
    }


def help_reply():
    skills = [
        {"name": skill["name"], "kind": skill["kind"], "description": skill["description"]}
        for skill in load_skills()
    ]
    return {
        "ok": True,
        "skill": "help",
        "reply": "Available commands: help, remember <note>, search <term>, delegate search <term>, schedule digest.",
        "skills": skills,
        "channels": ["cli", "companion", "ops"],
    }


def process_message(channel, text, approve=False):
    state = load_state()
    if channel not in state["channels"]:
        return {"ok": False, "error": "unknown_channel"}

    bump_channel_count(state, channel)
    message_record(channel, "user", text)
    skill = select_skill(text)
    if skill is None:
        reply = {
            "ok": False,
            "error": "no_matching_skill",
            "reply": "No skill matched. Try help, remember <note>, search <term>, or schedule digest.",
        }
    elif skill["name"] == "remember_note":
        reply = remember_note(state, channel, text[len(skill["trigger_prefix"]):])
    elif skill["name"] == "search_docs":
        if skill.get("requires_approval") and not approve:
            reply = {
                "ok": False,
                "approval_required": True,
                "skill": skill["name"],
                "reply": "search_docs requires approval because it calls a toolset.",
            }
        else:
            reply = search_docs(state, text[len(skill["trigger_prefix"]):].strip())
    elif skill["name"] == "delegate_search":
        if skill.get("requires_approval") and not approve:
            reply = {
                "ok": False,
                "approval_required": True,
                "skill": skill["name"],
                "reply": "delegate_search requires approval because it routes work through a worker channel.",
            }
        else:
            reply = delegate_search(state, text[len(skill["trigger_prefix"]):].strip())
    elif skill["name"] == "schedule_digest":
        reply = schedule_digest(state, "companion")
    else:
        reply = help_reply()

    if "reply" in reply:
        bump_channel_count(state, channel)
        message_record(channel, "assistant", reply["reply"], {"skill": reply.get("skill")})

    event(
        "message_processed",
        channel=channel,
        text=text,
        skill=reply.get("skill"),
        ok=reply.get("ok", False),
        approval_required=reply.get("approval_required", False),
    )
    save_state(state)
    return {
        "ok": reply.get("ok", False),
        "channel": channel,
        "skill": reply.get("skill"),
        "approval_required": reply.get("approval_required", False),
        "reply": reply.get("reply"),
        "memory_count": len(state["memory"]),
        "delegation_count": len(state["delegations"]),
        "pending_schedules": sum(1 for job in state["schedules"] if job["status"] == "pending"),
        "result": reply,
    }


def tick():
    state = load_state()
    pending = next((job for job in state["schedules"] if job["status"] == "pending"), None)
    if pending is None:
        result = {"ok": False, "error": "no_pending_schedule"}
        event("tick", ok=False, error="no_pending_schedule")
        return result

    pending["status"] = "done"
    channel = pending["channel"]
    summary = {
        "memory_items": len(state["memory"]),
        "recent_search_terms": [item["term"] for item in state["searches"][-3:]],
        "pending_schedules": sum(1 for job in state["schedules"] if job["status"] == "pending"),
    }
    reply = (
        f"Digest complete: {summary['memory_items']} memory items, "
        f"recent searches={summary['recent_search_terms'] or ['none']}."
    )
    bump_channel_count(state, channel)
    message_record(channel, "assistant", reply, {"schedule_id": pending["id"], "kind": "digest"})
    save_state(state)
    event("tick", ok=True, schedule_id=pending["id"], channel=channel)
    return {"ok": True, "schedule": pending, "digest": summary, "reply": reply}


def status():
    state = load_state()
    return {
        "assistant_name": state["assistant_name"],
        "channels": state["channels"],
        "skills": [
            {
                "name": skill["name"],
                "kind": skill["kind"],
                "requires_approval": skill.get("requires_approval", False),
            }
            for skill in load_skills()
        ],
        "memory_count": len(state["memory"]),
        "search_count": len(state["searches"]),
        "delegation_count": len(state["delegations"]),
        "pending_schedules": sum(1 for job in state["schedules"] if job["status"] == "pending"),
    }


def history(limit):
    if not MESSAGES_PATH.exists():
        return {"messages": []}
    rows = [json.loads(line) for line in MESSAGES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {"messages": rows[-limit:]}


def main():
    parser = argparse.ArgumentParser(description="Toy persistent assistant platform.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    history_cmd = sub.add_parser("history")
    history_cmd.add_argument("--limit", type=int, default=6)
    message_cmd = sub.add_parser("message")
    message_cmd.add_argument("channel")
    message_cmd.add_argument("text")
    message_cmd.add_argument("--approve", action="store_true")
    sub.add_parser("tick")
    args = parser.parse_args()

    if args.command == "status":
        result = status()
    elif args.command == "history":
        result = history(args.limit)
    elif args.command == "message":
        result = process_message(args.channel, args.text, approve=args.approve)
    else:
        result = tick()

    print(json.dumps(result, indent=2))
    if result.get("approval_required"):
        return 2
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
