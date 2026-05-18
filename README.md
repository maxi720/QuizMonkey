# SkyMonkey

![SkyMonkey Logo](src/assets/icon.png)

SkyMonkey is a cross-platform quiz application built with Flet.

You can run the same app as desktop or web, load your own quizzes from CSV,
play through questions, and review your results (including retrying only the
incorrect questions).

## What the app does

- Lists all available quiz files.
- Lets you upload and delete quiz CSV files directly in the app.
- Validates CSV data before a quiz starts.
- Runs one question at a time with immediate feedback.
- Shows result statistics (correct/wrong + score in percent).
- Supports "repeat incorrect questions" for focused practice.

## Tech stack

- Python `>=3.11`
- Flet `0.82.0`
- Project entry point: `src/main.py`

## Run locally

Install dependencies with `uv` and run:

```bash
uv run flet run
```

Run web mode:

```bash
uv run flet run --web
```

## Build targets

Use `flet build` for packaging:

```bash
flet build apk -v      # Android
flet build ipa -v      # iOS
flet build macos -v    # macOS
flet build linux -v    # Linux
flet build windows -v  # Windows
flet build web -v      # Web
```

Flet packaging docs: <https://docs.flet.dev/publish/>

## Quiz CSV format

Quiz files are loaded from:

- `src/quizzes/` during local development
- `$FLET_APP_STORAGE_DATA/quizzes/` in packaged app environments

Each row must follow exactly this schema:

```text
question;answer1;answer2;answer3;answer4;correctAnswer
```

Rules:

- Delimiter is `;` (semicolon), not comma.
- No header row.
- Exactly 6 fields per row.
- At least 2 non-empty answer options are required.
- Empty answer cells are allowed for shorter multiple choice sets.
- `correctAnswer` must exactly match one of `answer1..answer4`
  (case- and whitespace-sensitive).
- File must be UTF-8 encoded.

Example:

```text
What is the capital city of Austria?;Vienna;Salzburg;Innsbruck;Dresden;Vienna
```

## Repository structure

```text
src/
  main.py
  quizzes/
    myFirstQuiz.csv
    Weltgeographie.csv
    Wirtschaft_Grundlagen.csv
  assets/
    icon.png
    splash_android.png
README.md
LICENSE
pyproject.toml
```

## License

This project is licensed under the MIT License.

See `LICENSE` for the full text.

## Third-party licenses

This repository's MIT license applies to this project's source code.

Dependencies (including Flet) are separate third-party software and keep their
own licenses.

## Community

- Contribution guide: `CONTRIBUTING.md`
- Security policy: `SECURITY.md`
