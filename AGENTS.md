# AGENTS.md

Agent instructions for QuizApp. See also `CLAUDE.md`.

## Commands

```bash
uv run flet run            # desktop (dev)
uv run flet run --web      # web (dev)

flet build apk -v          # Android
flet build ipa -v          # iOS
flet build macos -v        # macOS
flet build linux -v        # Linux
flet build windows -v      # Windows
flet build web -v          # Web
```

- Use `uv run flet run`, not `python src/main.py` directly (though the latter works via `ft.run(main)` fallback).
- Use `flet build`, not `uv run flet build`, for distribution builds.
- **No tests, no linter, no formatter, no type-checker configured.** Do not invent commands for these.

## Architecture

- **Single file:** the entire app is `src/main.py` (~900 lines). No sub-modules.
- Flet entry point is resolved via `pyproject.toml`: `[tool.flet.app] path = "src"`, `module = "main"`.
- If you ever split `main.py`, update that config key.
- Single class `QuizApp` holds all state as instance variables; no external state management.
- UI flow: start page → question page → result page → (optional retry wrong answers) → start page.
- No navigation stack — views call `self.page.controls.clear()` then repopulate directly.
- Design tokens (colors) are now centralized as instance attributes in `QuizApp.__init__` and reused across views.

## Flet version quirks (0.82.0)

Pinned to `flet==0.82.0`. This version still expects **uppercase** enums/namespaces:

```python
ft.Colors.BLUE          # not ft.colors.blue
ft.FontWeight.BOLD      # not ft.FontWeight.bold  
ft.Padding.only(...)    # not ft.padding.only(...)
ft.Alignment.CENTER     # not ft.alignment.center
```

Do not use the older lowercase Flet APIs — they will fail at this version.
Hex color strings (e.g. `"#2563EB"`) are also valid and are used in the app theme.

## Quiz CSV format

Files live in `src/quizzes/` (dev) or `$FLET_APP_STORAGE_DATA/quizzes/` (packaged mobile builds).

```
question;answer1;answer2;answer3;answer4;correctAnswer
```

- Delimiter is `;` (semicolon), **not** comma.
- **No header row** — row 0 is the first question. A header row will be parsed as a broken question.
- Exactly 6 fields per row required.
- Empty answer cells are allowed (for questions with fewer than 4 choices): e.g., `Q;A;B;;;B`
- `correctAnswer` must be an **exact string match** (case- and whitespace-sensitive) of one of the 4 answer cells.
- File encoding must be UTF-8.
- Validation happens during load/upload (`load_questions()`), and invalid files are rejected with a `Dateifehler` message.

## Runtime storage path

`load_questions()` resolves the quiz directory conditionally:

```python
if os.environ.get("FLET_APP_STORAGE_DATA"):
    # packaged (mobile/desktop distribution)
    quiz_dir = Path(os.environ["FLET_APP_STORAGE_DATA"]) / "quizzes"
else:
    # dev run
    quiz_dir = Path(__file__).parent / "quizzes"
```

When testing CSV parsing, use the dev path (`src/quizzes/`).

## OpenCode-specific tooling

- **`ui-ux-pro-max` skill** (`.opencode/skills/ui-ux-pro-max/`): queries a local design database. Invoke via:
  ```bash
  python3 .opencode/skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system
  ```
  Default stack is `html-tailwind`. Only available in OpenCode sessions.

- **`graphify` plugin** (`.opencode/plugins/graphify.js`): injects suggestions to use `graphify query` if a `graphify-out/graph.json` knowledge graph exists. That file does not currently exist, so the plugin is a no-op.

## Miscellaneous

- `uv.lock` is gitignored (`*.lock` rule in `.gitignore`) — it exists locally but is not committed.
- `.venv/` is gitignored; do not add environment contents to commits.
- `.gitignore` now centrally includes rules for secrets (`.env*`, cert/key files), local tool caches, and `.opencode` local dependency files.
- No CI configured (no `.github/` directory).
- Python `>=3.11` required.
