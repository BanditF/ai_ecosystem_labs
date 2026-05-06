#!/usr/bin/env python3
import argparse
import ast
import json
import re
import sys
from pathlib import Path


SKILL_PATH = Path(__file__).with_name("term-count.skill.yaml")


class SkillError(Exception):
    pass


def parse_scalar(value):
    if value in {"true", "false"}:
        return value == "true"
    if value in {"null", "~"}:
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return ast.literal_eval(value)
    return value


def parse_simple_yaml(text):
    lines = text.splitlines()
    index = 0

    def parse_block(indent):
        nonlocal index
        container = None
        while index < len(lines):
            raw = lines[index]
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                index += 1
                continue

            current_indent = len(raw) - len(raw.lstrip(" "))
            if current_indent < indent:
                break
            if current_indent != indent:
                raise SkillError(f"Unsupported YAML indentation on line {index + 1}: {raw}")

            if stripped.startswith("- "):
                if container is None:
                    container = []
                if not isinstance(container, list):
                    raise SkillError("Cannot mix mappings and lists in the simple YAML loader")
                value_text = stripped[2:].strip()
                index += 1
                if value_text:
                    container.append(parse_scalar(value_text))
                else:
                    container.append(parse_block(indent + 2))
                continue

            if container is None:
                container = {}
            if not isinstance(container, dict):
                raise SkillError("Cannot mix lists and mappings in the simple YAML loader")

            key, sep, value_text = stripped.partition(":")
            if not sep:
                raise SkillError(f"Expected a key/value pair on line {index + 1}: {raw}")
            key = key.strip()
            value_text = value_text.strip()
            index += 1
            if value_text:
                container[key] = parse_scalar(value_text)
            else:
                container[key] = parse_block(indent + 2)

        return container if container is not None else {}

    return parse_block(0)


def load_skill_definition(path):
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        return parse_simple_yaml(text)
    return yaml.safe_load(text)


def build_parser(skill, skill_path):
    parser = argparse.ArgumentParser(description=skill.get("description", "Run a skill."))
    parser.add_argument(
        "--skill",
        default=str(skill_path),
        help="Path to a skill definition file. Defaults to term-count.skill.yaml.",
    )

    inputs = skill.get("inputs", {})
    for name, spec in inputs.items():
        option = f"--{name.replace('_', '-')}"
        arg_type = spec.get("type")
        required = bool(spec.get("required", False))
        default = spec.get("default")
        help_text = spec.get("description", "")

        if arg_type == "boolean":
            if default:
                parser.add_argument(
                    f"--no-{name.replace('_', '-')}",
                    dest=name,
                    action="store_false",
                    default=default,
                    help=help_text,
                )
            else:
                parser.add_argument(option, dest=name, action="store_true", default=default, help=help_text)
        else:
            parser.add_argument(option, dest=name, required=required, default=default, help=help_text)

    return parser


def validate_inputs(skill, values):
    errors = []
    for name, spec in skill.get("inputs", {}).items():
        if spec.get("required") and values.get(name) in {None, ""}:
            errors.append(f"missing required input: {name}")
    if errors:
        raise SkillError("; ".join(errors))


def run_term_count(values):
    path = Path(values["path"])
    if not path.is_file():
        raise SkillError(f"missing file: {path}")

    term = values["term"]
    case_sensitive = bool(values.get("case_sensitive", False))
    needle = term if case_sensitive else term.lower()
    matches = []

    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        haystack = line if case_sensitive else line.lower()
        occurrences = haystack.count(needle)
        for _ in range(occurrences):
            matches.append({"line_number": line_number, "line": line})

    return {
        "term": term,
        "count": len(matches),
        "matches": matches,
    }


def apply_validation(skill, result):
    validation = skill.get("validation", {})
    if validation.get("count_non_negative") and result.get("count", -1) < 0:
        raise SkillError("validation failed: count must be non-negative")
    if validation.get("matches_length_equals_count") and len(result.get("matches", [])) != result.get("count"):
        raise SkillError("validation failed: matches length must equal count")


def format_output(skill, result):
    fields = skill.get("output", {}).get("fields", {})
    ordered = {}
    for name in fields:
        ordered[name] = result.get(name)
    return ordered


def main():
    boot_parser = argparse.ArgumentParser(add_help=False)
    boot_parser.add_argument("--skill", default=str(SKILL_PATH))
    boot_args, _ = boot_parser.parse_known_args()

    skill_path = Path(boot_args.skill)
    skill = load_skill_definition(skill_path)
    parser = build_parser(skill, skill_path)
    args = parser.parse_args()

    skill = load_skill_definition(Path(args.skill))
    values = {name: getattr(args, name) for name in skill.get("inputs", {})}
    validate_inputs(skill, values)

    action = skill.get("action") or skill.get("name")
    if action != "term_count":
        raise SkillError(f"unsupported skill action: {action}")

    result = run_term_count(values)
    apply_validation(skill, result)
    print(json.dumps(format_output(skill, result), indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SkillError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        raise SystemExit(1)
