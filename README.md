# SkyMonkey

<p align="center">
  <img src="src/assets/icon.png" alt="SkyMonkey Logo" width="512" />
</p>

SkyMonkey is a cross-platform quiz application built with Flet.

You can run the same app on desktop, mobile or web, load your own quizzes from CSV,
play through questions, and review your results (including retrying only the
incorrect questions).

## What the app does

- Lists all available quiz files.
- Lets you upload and delete quiz CSV files directly in the app.
- Validates CSV data before a quiz starts.
- Runs one question at a time with immediate feedback.
- Shows result statistics (correct/wrong + score in percent).
- Supports "repeat incorrect questions" for focused practice.
- Saves an interrupted quiz so you can resume it later or start over.
- Has a statistics page showing how often each quiz was completed, with a
  reset button (behind a confirmation) to clear all counts.

## Saved state

Completion counts and interrupted quiz runs are stored in a `state.json` file
next to the quiz folder (`$FLET_APP_STORAGE_DATA/state.json` in packaged
builds, `src/state.json` during local development).

Quizzes finished via "repeat incorrect questions" and quizzes you end early do
not count toward the statistics.

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
flet build apk -v            # Android
flet build ipa -v            # iOS
flet build ios-simulator -v  # iOS Simulator (.app bundle)
flet build macos -v          # macOS
flet build linux -v          # Linux
flet build windows -v        # Windows
flet build web -v            # Web
```

To try the app in the iPhone Simulator:

```bash
xcrun simctl boot "iPhone 16 Pro"
open -a Simulator
flet build ios-simulator
xcrun simctl install booted build/ios-simulator/monkeyquiz.app
xcrun simctl launch booted com.maxdev.monkeyquiz
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
