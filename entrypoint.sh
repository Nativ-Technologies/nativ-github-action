#!/usr/bin/env bash
set -euo pipefail

# ── Inputs from action.yml (GitHub populates INPUT_* env vars) ──
SOURCE_PATH="${INPUT_SOURCE_PATH:?source_path is required}"
TARGET_LANGUAGES="${INPUT_TARGET_LANGUAGES:?target_languages is required}"
SOURCE_LANGUAGE="${INPUT_SOURCE_LANGUAGE:-English}"
FILE_PATTERN="${INPUT_FILE_PATTERN:-*.json}"
OUTPUT_DIR="${INPUT_OUTPUT_DIR:-locales}"
FORMALITY="${INPUT_FORMALITY:-}"
DO_COMMIT="${INPUT_COMMIT:-false}"
COMMIT_MSG="${INPUT_COMMIT_MESSAGE:-chore(i18n): update translations via Nativ}"
CREATE_PR="${INPUT_CREATE_PR:-false}"
PR_TITLE="${INPUT_PR_TITLE:-chore(i18n): update translations via Nativ}"
PR_BRANCH="${INPUT_PR_BRANCH:-nativ/translations}"

echo "::group::Nativ Localize"
echo "  source_path:      $SOURCE_PATH"
echo "  target_languages: $TARGET_LANGUAGES"
echo "  source_language:  $SOURCE_LANGUAGE"
echo "  file_pattern:     $FILE_PATTERN"
echo "  output_dir:       $OUTPUT_DIR"
echo "::endgroup::"

nativ --version

# ── Resolve source files ──
FILES=()
if [ -f "$SOURCE_PATH" ]; then
  FILES+=("$SOURCE_PATH")
elif [ -d "$SOURCE_PATH" ]; then
  while IFS= read -r -d '' f; do
    FILES+=("$f")
  done < <(find "$SOURCE_PATH" -name "$FILE_PATTERN" -type f -print0 | sort -z)
else
  echo "::error::source_path '$SOURCE_PATH' does not exist"
  exit 1
fi

if [ ${#FILES[@]} -eq 0 ]; then
  echo "::warning::No files matching '$FILE_PATTERN' found in '$SOURCE_PATH'"
  echo "files_translated=0" >> "$GITHUB_OUTPUT"
  echo "languages=" >> "$GITHUB_OUTPUT"
  exit 0
fi

echo "Found ${#FILES[@]} source file(s):"
printf "  %s\n" "${FILES[@]}"

# ── Build formality flag ──
FORMALITY_FLAG=""
if [ -n "$FORMALITY" ]; then
  FORMALITY_FLAG="--formality $FORMALITY"
fi

# ── Translate each file into each target language ──
IFS=',' read -ra LANGS <<< "$TARGET_LANGUAGES"
TOTAL_TRANSLATED=0

for LANG in "${LANGS[@]}"; do
  LANG="$(echo "$LANG" | xargs)"  # trim whitespace
  LANG_LOWER="$(echo "$LANG" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')"
  LANG_DIR="${OUTPUT_DIR}/${LANG_LOWER}"
  mkdir -p "$LANG_DIR"

  echo ""
  echo "::group::Translating to $LANG -> $LANG_DIR"

  for SRC_FILE in "${FILES[@]}"; do
    BASENAME="$(basename "$SRC_FILE")"
    OUT_FILE="${LANG_DIR}/${BASENAME}"

    echo "  $SRC_FILE -> $OUT_FILE"

    # Detect file type and translate accordingly
    EXT="${BASENAME##*.}"

    case "$EXT" in
      json)
        python3 /translate_json.py \
          --source-file "$SRC_FILE" \
          --output-file "$OUT_FILE" \
          --target-language "$LANG" \
          --source-language "$SOURCE_LANGUAGE" \
          $FORMALITY_FLAG
        ;;
      yaml|yml)
        python3 /translate_yaml.py \
          --source-file "$SRC_FILE" \
          --output-file "$OUT_FILE" \
          --target-language "$LANG" \
          --source-language "$SOURCE_LANGUAGE" \
          $FORMALITY_FLAG
        ;;
      po)
        python3 /translate_po.py \
          --source-file "$SRC_FILE" \
          --output-file "$OUT_FILE" \
          --target-language "$LANG" \
          --source-language "$SOURCE_LANGUAGE" \
          $FORMALITY_FLAG
        ;;
      *)
        # For plain text or unknown formats, translate line by line
        python3 /translate_lines.py \
          --source-file "$SRC_FILE" \
          --output-file "$OUT_FILE" \
          --target-language "$LANG" \
          --source-language "$SOURCE_LANGUAGE" \
          $FORMALITY_FLAG
        ;;
    esac

    TOTAL_TRANSLATED=$((TOTAL_TRANSLATED + 1))
  done

  echo "::endgroup::"
done

LANG_LIST="$(IFS=','; echo "${LANGS[*]}")"
echo ""
echo "Translated $TOTAL_TRANSLATED file(s) across ${#LANGS[@]} language(s)."

echo "files_translated=$TOTAL_TRANSLATED" >> "$GITHUB_OUTPUT"
echo "languages=$LANG_LIST" >> "$GITHUB_OUTPUT"

# ── Commit / PR ──
if [ "$DO_COMMIT" = "true" ] || [ "$CREATE_PR" = "true" ]; then
  git config user.name "nativ-bot"
  git config user.email "bot@usenativ.com"

  if [ "$CREATE_PR" = "true" ]; then
    git checkout -b "$PR_BRANCH" 2>/dev/null || git checkout "$PR_BRANCH"
  fi

  git add "$OUTPUT_DIR"
  if git diff --cached --quiet; then
    echo "No translation changes to commit."
  else
    git commit -m "$COMMIT_MSG"

    if [ "$CREATE_PR" = "true" ]; then
      git push origin "$PR_BRANCH" --force
      echo "::notice::Pushed to branch $PR_BRANCH. Create a PR manually or use gh cli."
    elif [ "$DO_COMMIT" = "true" ]; then
      echo "Changes committed. Push is up to your workflow."
    fi
  fi
fi

echo "Done!"
