# Nativ Localize — GitHub Action

Automatically translate your i18n files on every push or PR using the [Nativ](https://usenativ.com) AI localization platform.

Supports **JSON**, **YAML**, **PO/gettext**, and plain text files out of the box.

## Quick Start

```yaml
name: Localize

on:
  push:
    paths:
      - "locales/en/**"

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: Nativ-Technologies/nativ-github-action@v1
        with:
          api_key: ${{ secrets.NATIV_API_KEY }}
          source_path: locales/en
          target_languages: "French,German,Japanese"
          output_dir: locales
          commit: true

      - run: git push
```

This will:
1. Watch for changes to your English locale files
2. Translate them into French, German, and Japanese
3. Write output to `locales/french/`, `locales/german/`, `locales/japanese/`
4. Commit the translated files

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `api_key` | **Yes** | — | Your Nativ API key. Store as `NATIV_API_KEY` in repo secrets. |
| `source_path` | **Yes** | `locales/en` | File or directory containing source locale files |
| `target_languages` | **Yes** | — | Comma-separated target languages (e.g. `French,German`) |
| `source_language` | No | `English` | Source language name |
| `file_pattern` | No | `*.json` | Glob pattern for i18n files |
| `output_dir` | No | `locales` | Base directory for translated output |
| `formality` | No | — | `very_informal`, `informal`, `neutral`, `formal`, `very_formal` |
| `commit` | No | `false` | Auto-commit translated files |
| `commit_message` | No | `chore(i18n): update translations via Nativ` | Commit message |
| `create_pr` | No | `false` | Push to a branch for PR creation |
| `pr_branch` | No | `nativ/translations` | Branch name when `create_pr=true` |

## Outputs

| Output | Description |
|--------|-------------|
| `files_translated` | Number of files translated |
| `languages` | Comma-separated list of languages translated |

## Supported File Formats

| Format | Pattern | Notes |
|--------|---------|-------|
| JSON | `*.json` | Flat and nested keys, arrays |
| YAML | `*.yaml`, `*.yml` | Rails-style nested locale files |
| PO/gettext | `*.po` | Django, WordPress, PHP projects |
| Plain text | `*` | Line-by-line translation |

## Examples

### Translate on PR (with review)

```yaml
name: Localize PR

on:
  pull_request:
    paths:
      - "src/i18n/en.json"

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: Nativ-Technologies/nativ-github-action@v1
        with:
          api_key: ${{ secrets.NATIV_API_KEY }}
          source_path: src/i18n/en.json
          target_languages: "Spanish,Portuguese,French"
          output_dir: src/i18n

      - name: Show diff
        run: git diff
```

### Rails YAML locales

```yaml
- uses: Nativ-Technologies/nativ-github-action@v1
  with:
    api_key: ${{ secrets.NATIV_API_KEY }}
    source_path: config/locales
    target_languages: "French,German"
    file_pattern: "en.yml"
    output_dir: config/locales
```

### Django PO files with formal tone

```yaml
- uses: Nativ-Technologies/nativ-github-action@v1
  with:
    api_key: ${{ secrets.NATIV_API_KEY }}
    source_path: locale/en/LC_MESSAGES
    target_languages: "German,Japanese"
    file_pattern: "*.po"
    output_dir: locale
    formality: formal
```

### Use outputs in subsequent steps

```yaml
- uses: Nativ-Technologies/nativ-github-action@v1
  id: localize
  with:
    api_key: ${{ secrets.NATIV_API_KEY }}
    source_path: locales/en
    target_languages: "French"

- run: echo "Translated ${{ steps.localize.outputs.files_translated }} files"
```

## Getting Your API Key

1. Go to [dashboard.usenativ.com](https://dashboard.usenativ.com)
2. Navigate to **Settings → API Keys**
3. Create a new key
4. Add it as `NATIV_API_KEY` in your repo's **Settings → Secrets → Actions**

## How It Works

The action uses the [Nativ Python SDK](https://pypi.org/project/nativ/) under the hood. For each source file, it:

1. Parses the file and extracts translatable strings
2. Sends them to the Nativ API in batches (respecting your brand voice, translation memory, and style guides)
3. Writes the translated file to the output directory under a language-specific subdirectory

Your brand voice, translation memory, and style guides are automatically applied — the same quality you get from the Nativ dashboard.

## License

MIT — see [LICENSE](LICENSE).
