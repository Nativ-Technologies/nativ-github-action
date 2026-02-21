"""Translate a .po (gettext) file using the Nativ SDK."""
import argparse
import re
import sys
from nativ import Nativ


def parse_po(filepath):
    """Minimal PO parser -- returns list of (msgid, msgstr, line_number) tuples."""
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        if lines[i].startswith("msgid "):
            msgid_start = i
            msgid = _extract_string(lines, i)
            while i < len(lines) and not lines[i].startswith("msgstr "):
                i += 1
            if i < len(lines):
                msgstr = _extract_string(lines, i)
                if msgid:  # skip empty msgid (PO header)
                    entries.append((msgid, msgstr, msgid_start))
        i += 1

    return entries, lines


def _extract_string(lines, start):
    m = re.match(r'msg(?:id|str) "(.*)"', lines[start])
    if not m:
        return ""
    parts = [m.group(1)]
    j = start + 1
    while j < len(lines) and lines[j].startswith('"'):
        m2 = re.match(r'"(.*)"', lines[j])
        if m2:
            parts.append(m2.group(1))
        j += 1
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--target-language", required=True)
    parser.add_argument("--source-language", default="English")
    parser.add_argument("--formality", default=None)
    args = parser.parse_args()

    entries, lines = parse_po(args.source_file)

    if not entries:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return

    texts = [msgid for msgid, _, _ in entries]

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

    output_lines = list(lines)
    for (msgid, _, line_num), translation in zip(entries, translated):
        i = line_num
        while i < len(output_lines) and not output_lines[i].startswith("msgstr "):
            i += 1
        if i < len(output_lines):
            output_lines[i] = f'msgstr "{translation}"\n'
            j = i + 1
            while j < len(output_lines) and output_lines[j].startswith('"'):
                output_lines[j] = ""
                j += 1

    with open(args.output_file, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    print(f"    Translated {len(translated)} strings")


if __name__ == "__main__":
    main()
