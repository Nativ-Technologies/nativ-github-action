"""Translate a YAML i18n file using the Nativ SDK."""
import argparse
import sys

try:
    import yaml
except ImportError:
    print("PyYAML not installed, skipping YAML file", file=sys.stderr)
    sys.exit(0)

from nativ import Nativ


def collect_strings(obj, prefix=""):
    pairs = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, str):
                pairs.append((path, v))
            elif isinstance(v, (dict, list)):
                pairs.extend(collect_strings(v, path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            path = f"{prefix}[{i}]"
            if isinstance(item, str):
                pairs.append((path, item))
            elif isinstance(item, (dict, list)):
                pairs.extend(collect_strings(item, path))
    return pairs


def set_nested(obj, path, value):
    import re
    parts = re.split(r'(?<!\[)\.', path)
    cur = obj
    for i, part in enumerate(parts[:-1]):
        m = re.match(r'(.+)\[(\d+)\]$', part)
        if m:
            key, idx = m.group(1), int(m.group(2))
            cur = cur[key][idx]
        else:
            cur = cur[part]
    last = parts[-1]
    m = re.match(r'(.+)\[(\d+)\]$', last)
    if m:
        key, idx = m.group(1), int(m.group(2))
        cur[key][idx] = value
    else:
        cur[last] = value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--target-language", required=True)
    parser.add_argument("--source-language", default="English")
    parser.add_argument("--formality", default=None)
    args = parser.parse_args()

    with open(args.source_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    pairs = collect_strings(data)
    if not pairs:
        with open(args.output_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        return

    texts = [v for _, v in pairs]
    keys = [k for k, _ in pairs]

    client = Nativ()
    try:
        kwargs = dict(
            target_language=args.target_language,
            source_language=args.source_language,
        )
        if args.formality:
            kwargs["formality"] = args.formality

        BATCH_SIZE = 50
        translated = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            results = client.translate_batch(batch, **kwargs)
            translated.extend(r.translated_text for r in results)
    finally:
        client.close()

    import copy
    output = copy.deepcopy(data)
    for key, val in zip(keys, translated):
        set_nested(output, key, val)

    with open(args.output_file, "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, default_flow_style=False)

    print(f"    Translated {len(translated)} strings")


if __name__ == "__main__":
    main()
