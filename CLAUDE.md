# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run as desktop app
uv run flet run

# Run as web app
uv run flet run --web

# Build for distribution
flet build apk -v       # Android
flet build ipa -v       # iOS
flet build macos -v     # macOS
flet build web -v       # Web
```

No test or lint commands are configured.

## Architecture

**QuizApp** is a cross-platform quiz app built with [Flet](https://flet.dev/) (Flutter for Python). The entire application lives in a single file: [src/main.py](src/main.py).

### Entry point

`main()` (async) in `src/main.py` instantiates `QuizApp(page)` and passes it the Flet `Page` object. The class constructor sets up the theme, detects platform, configures responsive sizing, and renders the start page.

### UI flow

Start page → Question page → Result page → (optional) retry wrong questions → Start page

- **Start page** (`show_startpage`): Lists available quizzes discovered from CSV files in `src/quizzes/`. Users can upload new quizzes (via `FilePicker`) or delete existing ones.
- **Question page** (`show_question_page`): Renders the current question with up to 4 multiple-choice answer buttons. `check_answer()` highlights buttons green/red and advances to the next question.
- **Result page** (`show_result`): Displays correct/wrong counts and score percentage. Can retry only the incorrectly answered questions.

### State

All state is held as instance variables on `QuizApp`:
- `fragen`: list of parsed questions from the active CSV
- `current_question`: index into `fragen`
- `correct_count` / `wrong_questions`: scoring
- `answer_buttons` and other UI element references for in-place updates

### Quiz data format

CSV files in `src/quizzes/` use a semicolon delimiter:

```
question;answer1;answer2;answer3;answer4;correctAnswer
```

Empty cells are allowed when a question has fewer than 4 options. The `correctAnswer` column must exactly match one of the answer columns.

### Responsive design

`_on_resize()` is called on window resize events. `_get_scale()`, `_get_text_size()`, and `_get_pad()` return values derived from the current window dimensions and are used throughout the UI to adapt layouts for desktop, mobile, and web.
