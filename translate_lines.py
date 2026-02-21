"""Translate a plain text file line-by-line using the Nativ SDK."""
import argparse
from nativ import Nativ


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--target-language", required=True)
    parser.add_argument("--source-language", default="English")
    parser.add_argument("--formality", default=None)
    args = parser.parse_args()

    with open(args.source_file, "r", encoding="utf-8") as f:
        lines = [l.rstrip("\n") for l in f.readlines()]

    non_empty = [(i, l) for i, l in enumerate(lines) if l.strip()]

    if not non_empty:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return

    texts = [l for _, l in non_empty]

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

    output = list(lines)
    for (idx, _), tr in zip(non_empty, translated):
        output[idx] = tr

    with open(args.output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output) + "\n")

    print(f"    Translated {len(translated)} lines")


if __name__ == "__main__":
    main()
