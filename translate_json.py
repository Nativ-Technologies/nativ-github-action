"""Translate a JSON i18n file (flat or nested) using the Nativ SDK."""
import argparse
import json
from nativ import Nativ


def collect_strings(obj, prefix=""):
    """Flatten nested dict into (key_path, value) pairs."""
    pairs = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, str):
                pairs.append((path, v))
            elif isinstance(v, dict):
                pairs.extend(collect_strings(v, path))
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, str):
                        pairs.append((f"{path}[{i}]", item))
                    elif isinstance(item, dict):
                        pairs.extend(collect_strings(item, f"{path}[{i}]"))
    return pairs


def set_nested(obj, path, value):
    """Set a value at a dotted path (supporting [n] array indices)."""
    import re
    parts = re.split(r'\.', path)
    cur = obj
    for i, part in enumerate(parts[:-1]):
        m = re.match(r'(.+)\[(\d+)\]$', part)
        if m:
            key, idx = m.group(1), int(m.group(2))
            cur = cur.setdefault(key, [])[idx] if isinstance(cur.get(key), list) else cur.setdefault(key, {})[idx]
        else:
            if part not in cur:
                next_part = parts[i + 1]
                cur[part] = [] if re.match(r'.*\[\d+\]$', next_part) else {}
            cur = cur[part]
    last = parts[-1]
    m = re.match(r'(.+)\[(\d+)\]$', last)
    if m:
        key, idx = m.group(1), int(m.group(2))
        if key not in cur:
            cur[key] = []
        while len(cur[key]) <= idx:
            cur[key].append(None)
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
        data = json.load(f)

    pairs = collect_strings(data)
    if not pairs:
        with open(args.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
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
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"    Translated {len(translated)} strings")


if __name__ == "__main__":
    main()
