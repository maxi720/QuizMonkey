import csv
import io
import os
import shutil
from pathlib import Path

import flet as ft


class QuizApp:
    def __init__(self, page: ft.Page):
        self.page = page

        self.page.title = "SkyMonkey"
        # Self-hosted font bundled in assets — no runtime fetch from Google
        # Fonts servers, so no user IP is leaked (GDPR/DSGVO compliant).
        self.page.fonts = {"Fredoka": "fonts/Fredoka.ttf"}
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.padding = 0

        self.color_bg = "#0F172A"
        self.color_text = "#F8FAFC"
        self.color_muted = "#CBD5E1"
        self.color_primary = "#4F46E5"
        self.color_info = "#2563EB"
        self.color_success = "#16A34A"
        self.color_danger = "#DC2626"
        self.color_warning = "#EA580C"
        self.color_answer = "#334155"
        self.color_answer_border = "#64748B"
        self.logo_src = "icon.png"
        self.page.bgcolor = self.color_bg

        platform = self.page.platform
        self.is_mobile = platform is not None and platform.is_mobile()

        if not self.is_mobile and not self.page.web:
            self.page.window.min_width = 320
            self.page.window.width = 600
            self.page.window.height = 700

        data_dir = os.environ.get("FLET_APP_STORAGE_DATA")
        if data_dir:
            self.quiz_folder = os.path.join(data_dir, "quizzes")
        else:
            self.quiz_folder = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "quizzes"
            )

        self.default_quiz_folder = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "quizzes"
        )

        os.makedirs(self.quiz_folder, exist_ok=True)
        self._ensure_default_quizzes()

        self.fragen: list[list[str]] = []
        self.current_question = 0
        self.correct_answer = ""
        self.correct_count = 0
        self.selected_answer: str | None = None
        self.answer_locked = False
        self.wrong_questions: list[list[str]] = []
        self.quiz_buttons: list[ft.Control] = []
        self.answer_buttons: list[ft.Button] = []
        self.next_button: ft.Button | None = None

        self.file_picker = ft.FilePicker()
        self.page.services.append(self.file_picker)

        self.page.on_resize = self._on_resize
        self._current_view = "start"
        self._layout_cache: dict[str, float | int | str] = {
            "width": 0,
            "height": 0,
            "scale": 1.0,
            "mode": "medium",
        }
        self._last_resize_signature: tuple[int, int, str] | None = None

        self._refresh_layout_cache(force=True)

        self.show_startpage()

    def show_message(self, text: str) -> None:
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text(text),
                duration=3000,
            )
        )
        self.page.update()

    def _get_scale(self) -> float:
        self._refresh_layout_cache()
        return float(self._layout_cache["scale"])

    def _get_view_mode(self) -> str:
        self._refresh_layout_cache()
        return str(self._layout_cache["mode"])

    def _refresh_layout_cache(self, force: bool = False) -> None:
        width = int(self.page.width or 600)
        height = int(self.page.height or 800)

        cached_width = int(self._layout_cache["width"])
        cached_height = int(self._layout_cache["height"])

        if not force and width == cached_width and height == cached_height:
            return

        if width < 520:
            mode = "compact"
        elif width < 880:
            mode = "medium"
        else:
            mode = "expanded"

        scale = max(0.5, min(1.5, min(width / 600, height / 750)))
        self._layout_cache = {
            "width": width,
            "height": height,
            "scale": scale,
            "mode": mode,
        }

    def _side_padding(self) -> int:
        mode = self._get_view_mode()
        if mode == "compact":
            return 10
        if mode == "medium":
            return 16
        return 24

    def _get_text_size(self, base: int) -> int:
        return max(10, int(base * self._get_scale()))

    def _get_pad(self, base: int) -> int:
        return max(2, int(base * self._get_scale()))

    def _logo(self, base_size: int = 120) -> ft.Container:
        mode = self._get_view_mode()
        size = base_size
        if mode == "compact":
            size = int(base_size * 0.68)
        elif mode == "medium":
            size = int(base_size * 0.82)

        logo_size = self._get_pad(size)
        return ft.Container(
            content=ft.Image(
                src=self.logo_src,
                width=logo_size,
                height=logo_size,
                fit=ft.BoxFit.CONTAIN,
                error_content=ft.Container(width=logo_size, height=logo_size),
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.only(top=self._get_pad(8), bottom=self._get_pad(8)),
        )

    def make_button_style(
        self,
        bgcolor,
        text_size=20,
        radius=12,
        padding=None,
        side=None,
        weight=ft.FontWeight.W_600,
        font_family=None,
    ) -> ft.ButtonStyle:
        return ft.ButtonStyle(
            text_style=ft.TextStyle(
                size=text_size, weight=weight, font_family=font_family
            ),
            color=self.color_text,
            bgcolor=bgcolor,
            padding=padding,
            shape=ft.RoundedRectangleBorder(radius=radius),
            side=side,
        )

    def _fit_action_button(
        self, button_width: float, label_len: int = 6
    ) -> tuple[int, int]:
        """Return the largest bold font size whose label fits inside a button
        of the given width (leaving a little horizontal breathing room), plus a
        matching button height."""
        side_margin = button_width * 0.16  # "ein wenig Seitenabstand"
        usable = max(1.0, button_width - 2 * side_margin)
        char_factor = 0.60  # approx. em-width per bold character
        fit = int(usable / (label_len * char_factor))
        text_size = max(14, min(fit, self._get_text_size(34)))
        height = int(text_size * 2.1)
        return text_size, height

    def _render_current_view(self) -> None:
        self._refresh_layout_cache(force=True)
        if self._current_view == "start":
            self.show_startpage()
        elif self._current_view == "result":
            self.show_result()
        elif self._current_view == "question":
            self.show_question_page()

    def _set_root(self, *controls: ft.Control) -> None:
        """Mount a view inside a SafeArea so content never overlaps the
        notch/dynamic island at the top or the home indicator at the bottom."""
        self.page.controls.clear()
        self.page.controls.append(
            ft.SafeArea(
                content=ft.Column(
                    controls=list(controls),
                    expand=True,
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                expand=True,
            )
        )

    def _list_quiz_files(self) -> list[str]:
        quiz_path = Path(self.quiz_folder)
        return sorted(
            entry.name
            for entry in quiz_path.iterdir()
            if entry.is_file() and entry.suffix.lower() == ".csv"
        )

    def _ensure_default_quizzes(self) -> None:
        source_dir = Path(self.default_quiz_folder)
        target_dir = Path(self.quiz_folder)

        if source_dir == target_dir or not source_dir.exists():
            return

        for source_file in source_dir.glob("*.csv"):
            target_file = target_dir / source_file.name
            if target_file.exists():
                continue
            try:
                shutil.copy(source_file, target_file)
            except OSError:
                continue

    def _parse_quiz_text(self, quiz_text: str) -> tuple[list[list[str]], list[str]]:
        reader = csv.reader(io.StringIO(quiz_text), delimiter=";")
        return self._parse_quiz_rows(reader)

    def _get_quiz_destination(self, original_filename: str) -> str:
        safe_name = os.path.basename(original_filename)
        if not safe_name.lower().endswith(".csv"):
            safe_name = f"{safe_name}.csv"

        destination = Path(self.quiz_folder) / safe_name
        if not destination.exists():
            return str(destination)

        stem = destination.stem
        suffix = destination.suffix
        index = 1
        while True:
            candidate = destination.with_name(f"{stem}_{index}{suffix}")
            if not candidate.exists():
                return str(candidate)
            index += 1

    def _validate_row(self, row: list[str], row_number: int) -> tuple[bool, str | None]:
        if len(row) != 6:
            return (
                False,
                f"Zeile {row_number}: Erwartet 6 Spalten, gefunden {len(row)}.",
            )

        row[0] = row[0].lstrip("\ufeff")

        if not row[0].strip():
            return False, f"Zeile {row_number}: Frage ist leer."

        answers = row[1:5]
        non_empty_answers = [answer for answer in answers if answer != ""]
        if len(non_empty_answers) < 2:
            return (
                False,
                f"Zeile {row_number}: Mindestens 2 Antwortoptionen erforderlich.",
            )

        if row[5] not in answers:
            return (
                False,
                f"Zeile {row_number}: correctAnswer muss exakt einer Antwort entsprechen.",
            )

        return True, None

    def _parse_quiz_rows(self, reader: csv.reader) -> tuple[list[list[str]], list[str]]:
        questions: list[list[str]] = []
        errors: list[str] = []

        for row_number, row in enumerate(reader, start=1):
            if not any(cell.strip() for cell in row):
                continue

            is_valid, error = self._validate_row(row, row_number)
            if is_valid:
                questions.append(row)
            elif error:
                errors.append(error)

        if not questions and not errors:
            errors.append("Keine Fragen gefunden.")

        return questions, errors

    def _show_validation_errors(self, errors: list[str]) -> None:
        first_error = errors[0]
        if len(errors) > 1:
            self.show_message(f"Dateifehler ({len(errors)}): {first_error}")
        else:
            self.show_message(f"Dateifehler: {first_error}")

    def show_startpage(self) -> None:
        self._current_view = "start"
        self._refresh_layout_cache(force=True)
        self.next_button = None
        self.selected_answer = None
        self.answer_locked = False
        self.load_custom_quizzes()

        side_padding = self._side_padding()
        page_w = int(self.page.width or 600)
        page_h = int(self.page.height or 800)

        # Heading: "monkeyquiz" wordmark in the bundled Fredoka display font.
        header = ft.Container(
            content=ft.Text(
                "MonkeyQuiz",
                font_family="Fredoka",
                size=self._get_text_size(48),
                weight=ft.FontWeight.BOLD,
                color=self.color_text,
            ),
            padding=ft.Padding.only(top=self._get_pad(16), bottom=self._get_pad(12)),
            alignment=ft.Alignment.CENTER,
        )

        # Quiz area: a large logo watermark centred behind a scrollable list of
        # quizzes. When more quizzes are uploaded than fit on screen, the list
        # scrolls while the logo stays centred in the same window.
        logo_bg_size = int(min(page_w, page_h) * 0.7)
        background_logo = ft.Container(
            content=ft.Image(
                src="logo_watermark.png",
                width=logo_bg_size,
                height=logo_bg_size,
                fit=ft.BoxFit.CONTAIN,
                opacity=0.22,
                error_content=ft.Container(),
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )
        quiz_scroll = ft.Column(
            controls=self.quiz_buttons,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
        )
        quiz_area = ft.Stack(
            controls=[background_logo, quiz_scroll],
            expand=True,
        )

        # Bottom actions: Upload (left) + Delete (right), always side by side,
        # equal size, rectangular, with bold text scaled to fit the button.
        container_pad = self._get_pad(side_padding)
        btn_spacing = self._get_pad(12)
        btn_w = max(80.0, (page_w - 2 * container_pad - btn_spacing) / 2)
        action_text_size, action_height = self._fit_action_button(btn_w)

        def action_btn(label: str, color: str, handler) -> ft.Button:
            return ft.Button(
                content=label,
                on_click=handler,
                expand=True,
                height=action_height,
                style=self.make_button_style(
                    color,
                    text_size=action_text_size,
                    radius=0,
                    weight=ft.FontWeight.W_800,
                    padding=ft.Padding.symmetric(horizontal=self._get_pad(6)),
                ),
            )

        action_buttons = ft.Container(
            content=ft.Row(
                controls=[
                    action_btn("Upload", self.color_success, self.upload_csv),
                    action_btn("Delete", self.color_danger, self.remove_csv),
                ],
                spacing=btn_spacing,
            ),
            padding=ft.Padding.only(
                left=container_pad,
                right=container_pad,
                top=self._get_pad(10),
                bottom=self._get_pad(20),
            ),
        )

        self._set_root(header, quiz_area, action_buttons)
        self.page.update()

    def load_custom_quizzes(self) -> None:
        self.quiz_buttons.clear()
        side_padding = self._side_padding()

        try:
            files = self._list_quiz_files()
        except OSError:
            return

        for file_name in files:
            filepath = str(Path(self.quiz_folder) / file_name)
            button_text = Path(file_name).stem

            quiz_button = ft.Button(
                content=button_text,
                data=filepath,
                expand=True,
                on_click=lambda e, f=filepath: self.start_quiz(f),
                style=self.make_button_style(
                    self.color_primary,
                    text_size=self._get_text_size(26),
                    weight=ft.FontWeight.W_700,
                    padding=ft.Padding.symmetric(
                        horizontal=self._get_pad(12),
                        vertical=self._get_pad(16),
                    ),
                ),
            )

            self.quiz_buttons.append(
                ft.Container(
                    content=ft.Row([quiz_button]),
                    padding=ft.Padding.symmetric(
                        horizontal=self._get_pad(side_padding),
                        vertical=self._get_pad(4),
                    ),
                )
            )

    async def upload_csv(self, e) -> None:
        try:
            files = await self.file_picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["csv"],
                with_data=True,
            )

            if not files:
                return

            selected_file = files[0]
            original_filename = selected_file.name or "upload.csv"

            if not original_filename.lower().endswith(".csv"):
                self.show_message("Fehler: Nur CSV-Dateien können hochgeladen werden!")
                return

            file_path = getattr(selected_file, "path", None)
            destination = self._get_quiz_destination(original_filename)

            if file_path:
                quiz_text = Path(file_path).read_text(encoding="utf-8")
            elif selected_file.bytes is not None:
                quiz_text = selected_file.bytes.decode("utf-8")
            else:
                self.show_message("Fehler: Kein Zugriff auf Dateiinhalt.")
                return

            questions, errors = self._parse_quiz_text(quiz_text)
            if errors:
                self._show_validation_errors(errors)
                return

            if file_path:
                shutil.copy(file_path, destination)
            else:
                Path(destination).write_text(quiz_text, encoding="utf-8")

            self.fragen = questions
            self.current_question = 0
            self.correct_count = 0
            self.wrong_questions = []
            self.selected_answer = None
            self.answer_locked = False

            uploaded_name = os.path.basename(destination)
            self.show_message(f"Quiz '{uploaded_name}' hochgeladen!")
            self.show_startpage()

        except UnicodeDecodeError:
            self.show_message("Dateifehler: Datei ist nicht UTF-8 kodiert.")
        except Exception as ex:
            self.show_message(f"Fehler beim Hochladen: {ex}")

    def remove_csv(self, e) -> None:
        try:
            files = self._list_quiz_files()
        except OSError as ex:
            self.show_message(f"Fehler beim Lesen des Quiz-Ordners: {ex}")
            return

        if not files:
            self.show_message("Keine Quizdaten vorhanden.")
            return

        dropdown = ft.Dropdown(
            label="Choose a file",
            options=[ft.dropdown.Option(file_name) for file_name in files],
        )

        def confirm_remove(_):
            selected_file = dropdown.value
            if not selected_file:
                self.show_message("Bitte eine Datei auswählen.")
                return

            try:
                os.remove(os.path.join(self.quiz_folder, selected_file))
                self.page.pop_dialog()
                self.page.update()
                self.show_message(f"Quiz '{selected_file}' erfolgreich gelöscht.")
                self.show_startpage()
            except OSError as ex:
                self.show_message(f"Fehler beim Löschen: {ex}")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Quiz löschen"),
            content=dropdown,
            actions=[
                ft.Button(content="Löschen", on_click=confirm_remove),
                ft.Button(
                    content="Abbrechen",
                    on_click=lambda _: (self.page.pop_dialog(), self.page.update()),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.show_dialog(dialog)
        self.page.update()

    def start_quiz(self, filename: str) -> None:
        self.load_questions(filename)
        if self.fragen:
            self.show_question_page()

    def show_question_page(self) -> None:
        self._current_view = "question"
        self._refresh_layout_cache(force=True)
        side_padding = self._side_padding()

        if self.current_question >= len(self.fragen):
            self.show_result()
            return

        frage_data = self.fragen[self.current_question]

        if len(frage_data) != 6:
            self._set_root(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self._logo(120),
                            ft.Text(
                                "FILE ERROR!",
                                size=self._get_text_size(40),
                                color=self.color_danger,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Button(
                                content="Back",
                                on_click=lambda e: self.show_startpage(),
                                style=self.make_button_style(
                                    self.color_info,
                                    text_size=self._get_text_size(30),
                                    padding=ft.Padding.all(15),
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                )
            )
            self.page.update()
            return

        self.correct_answer = frage_data[5]
        self.answer_buttons = []
        answer_containers: list[ft.Control] = []

        for i in range(1, 5):
            answer_text = frage_data[i]
            if answer_text:
                ans_text = ft.Text(
                    answer_text,
                    size=self._get_text_size(28),
                    weight=ft.FontWeight.W_500,
                    color=self.color_text,
                    text_align=ft.TextAlign.LEFT,
                )
                btn = ft.Button(
                    content=ft.Container(
                        content=ans_text,
                        alignment=ft.Alignment(-1, 0),
                        expand=True,
                    ),
                    data=answer_text,
                    expand=True,
                    on_click=lambda e, a=answer_text: self.check_answer(a),
                    style=ft.ButtonStyle(
                        color=self.color_text,
                        bgcolor=self.color_answer,
                        padding=ft.Padding.all(10),
                        shape=ft.RoundedRectangleBorder(radius=12),
                        side=ft.BorderSide(2, self.color_answer_border),
                    ),
                )
                self.answer_buttons.append(btn)
                ans_container = ft.Container(
                    content=ft.Row([btn]),
                    padding=ft.Padding.symmetric(
                        horizontal=self._get_pad(side_padding),
                        vertical=self._get_pad(3),
                    ),
                )
                answer_containers.append(ans_container)

        self.next_button = ft.Button(
            content="Next",
            on_click=self.next_question,
            disabled=not self.answer_locked,
            style=self._next_btn_style(),
        )

        back_button = ft.Button(
            content="Home",
            on_click=lambda e: self.show_startpage(),
            style=self._back_btn_style(),
        )

        question_text = ft.Text(
            frage_data[0],
            style=ft.TextStyle(
                size=self._get_text_size(30),
                weight=ft.FontWeight.W_600,
                color=self.color_text,
            ),
        )

        q_container = ft.Container(
            content=question_text,
            alignment=ft.Alignment.TOP_LEFT,
            padding=ft.Padding.only(
                left=self._get_pad(side_padding),
                top=self._get_pad(25),
                bottom=self._get_pad(15),
            ),
        )

        next_container = ft.Container(
            content=self.next_button,
            padding=ft.Padding.only(
                top=self._get_pad(10),
                right=self._get_pad(side_padding),
                bottom=self._get_pad(6),
            ),
            alignment=ft.Alignment.CENTER_RIGHT,
        )

        progress_text = ft.Text(
            f"{self.current_question + 1}/{len(self.fragen)}",
            style=ft.TextStyle(
                size=self._get_text_size(22),
                weight=ft.FontWeight.W_500,
                color=self.color_muted,
            ),
        )

        bottom_container = ft.Container(
            content=ft.Row(
                controls=[
                    back_button,
                    ft.Container(expand=True),
                    progress_text,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.only(
                left=self._get_pad(side_padding),
                right=self._get_pad(side_padding),
                bottom=self._get_pad(20),
            ),
        )

        question_content = ft.Column(
            controls=[
                self._logo(96),
                q_container,
                *answer_containers,
            ],
            expand=True,
            spacing=0,
            scroll=ft.ScrollMode.ADAPTIVE,
        )

        bottom_actions = ft.Column(
            controls=[next_container, bottom_container],
            spacing=0,
        )

        self._set_root(question_content, bottom_actions)

        if self.answer_locked and self.selected_answer is not None:
            self._apply_answer_feedback(self.selected_answer)

        self.page.update()

    def load_questions(self, filename: str, show_errors: bool = True) -> None:
        self.fragen.clear()
        self.selected_answer = None
        self.answer_locked = False

        try:
            with open(filename, "r", encoding="utf-8") as data:
                reader = csv.reader(data, delimiter=";")
                self.fragen, errors = self._parse_quiz_rows(reader)
                if errors:
                    self.fragen.clear()
                    if show_errors:
                        self._show_validation_errors(errors)
        except FileNotFoundError:
            if show_errors:
                self.show_message(f"Datei '{filename}' nicht gefunden!")
        except UnicodeDecodeError:
            if show_errors:
                self.show_message(
                    f"Datei '{filename}' hat eine ungültige Zeichenkodierung (kein UTF-8)."
                )
        except PermissionError:
            if show_errors:
                self.show_message(f"Keine Leseberechtigung für '{filename}'.")
        except Exception as ex:
            if show_errors:
                self.show_message(f"Fehler beim Laden der Datei: {ex}")

        self.current_question = 0
        self.correct_count = 0
        self.wrong_questions = []

    def check_answer(self, answer: str) -> None:
        if self.answer_locked:
            return

        is_correct = answer == self.correct_answer
        self.selected_answer = answer
        self.answer_locked = True

        if is_correct:
            self.correct_count += 1
        else:
            self.wrong_questions.append(self.fragen[self.current_question])

        self._apply_answer_feedback(answer)
        self.page.update()

    def _apply_answer_feedback(self, answer: str) -> None:
        is_correct = answer == self.correct_answer

        for button in self.answer_buttons:
            if button.data == answer:
                button.style.bgcolor = self.color_success if is_correct else self.color_danger
            elif button.data == self.correct_answer:
                button.style.bgcolor = self.color_success
            button.disabled = True

        if self.next_button:
            self.next_button.disabled = False

    def next_question(self, e) -> None:
        self.current_question += 1
        self.selected_answer = None
        self.answer_locked = False
        self.show_question_page()

    def show_result(self) -> None:
        self._current_view = "result"
        self._refresh_layout_cache(force=True)
        total = len(self.fragen)
        correct = self.correct_count
        wrong = total - correct
        score = round(correct / total * 100, 1) if total > 0 else 0.0
        side_padding = self._side_padding()
        compact = self._get_view_mode() == "compact"

        title = ft.Container(
            content=ft.Text(
                "Result",
                size=self._get_text_size(36),
                weight=ft.FontWeight.BOLD,
                color=self.color_text,
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.only(
                top=self._get_pad(20), bottom=self._get_pad(16)
            ),
        )

        logo = self._logo(120)

        score_cards = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Correct",
                            size=self._get_text_size(16),
                            color=self.color_text,
                        ),
                        ft.Text(
                            str(correct),
                            size=self._get_text_size(48),
                            weight=ft.FontWeight.BOLD,
                            color=self.color_text,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=self._get_pad(4),
                ),
                bgcolor=self.color_success,
                border_radius=12,
                padding=self._get_pad(20),
                expand=not compact,
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Wrong",
                            size=self._get_text_size(16),
                            color=self.color_text,
                        ),
                        ft.Text(
                            str(wrong),
                            size=self._get_text_size(48),
                            weight=ft.FontWeight.BOLD,
                            color=self.color_text,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=self._get_pad(4),
                ),
                bgcolor=self.color_danger,
                border_radius=12,
                padding=self._get_pad(20),
                expand=not compact,
            ),
        ]

        score_row = ft.Container(
            content=(
                ft.Column(
                    controls=score_cards,
                    spacing=self._get_pad(10),
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                )
                if compact
                else ft.Row(
                    controls=score_cards,
                    spacing=self._get_pad(12),
                )
            ),
            padding=ft.Padding.symmetric(horizontal=self._get_pad(side_padding)),
        )

        score_percent = ft.Container(
            content=ft.Text(
                f"{score} %",
                size=self._get_text_size(60),
                weight=ft.FontWeight.BOLD,
                color=self.color_text,
                text_align=ft.TextAlign.CENTER,
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(vertical=self._get_pad(20)),
        )

        btn_end = ft.Button(
            content="Back Home",
            on_click=lambda e: self.show_startpage(),
            height=self._get_pad(55),
            style=self.make_button_style(
                bgcolor=self.color_info,
                text_size=self._get_text_size(20),
                padding=ft.Padding.symmetric(vertical=self._get_pad(15)),
            ),
        )

        col_controls: list[ft.Control] = []

        if wrong > 0:
            col_controls.append(
                ft.Button(
                    content="Repeat Incorrect Questions",
                    on_click=self.restart_wrong_questions,
                    height=self._get_pad(55),
                    style=self.make_button_style(
                        bgcolor=self.color_warning,
                        text_size=self._get_text_size(20),
                        padding=ft.Padding.symmetric(vertical=self._get_pad(15)),
                    ),
                )
            )

        col_controls.append(btn_end)

        bottom_actions = ft.Column(
            controls=[
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Column(
                        controls=col_controls,
                        spacing=self._get_pad(12),
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    padding=ft.Padding.only(
                        left=self._get_pad(side_padding),
                        right=self._get_pad(side_padding),
                        bottom=self._get_pad(20),
                    ),
                ),
            ],
            expand=True,
        )

        self._set_root(title, logo, score_row, score_percent, bottom_actions)
        self.page.update()

    def restart_wrong_questions(self, e) -> None:
        self.fragen = self.wrong_questions.copy()
        self.wrong_questions = []
        self.current_question = 0
        self.correct_count = 0
        self.selected_answer = None
        self.answer_locked = False
        self.show_question_page()

    def _back_btn_style(self) -> ft.ButtonStyle:
        return ft.ButtonStyle(
            text_style=ft.TextStyle(
                size=self._get_text_size(22),
                weight=ft.FontWeight.W_800,
            ),
            color=self.color_text,
            bgcolor=self.color_info,
            padding=ft.Padding.symmetric(
                horizontal=self._get_pad(18),
                vertical=self._get_pad(14),
            ),
            shape=ft.RoundedRectangleBorder(radius=15),
        )

    def _next_btn_style(self) -> ft.ButtonStyle:
        return ft.ButtonStyle(
            text_style=ft.TextStyle(
                size=self._get_text_size(30),
                weight=ft.FontWeight.W_800,
            ),
            color=self.color_text,
            bgcolor=self.color_info,
            padding=ft.Padding.symmetric(
                horizontal=self._get_pad(14),
                vertical=self._get_text_size(17),
            ),
            shape=ft.RoundedRectangleBorder(radius=15),
        )

    def _on_resize(self, e) -> None:
        width = int(self.page.width or 600)
        height = int(self.page.height or 800)
        signature = (width // 16, height // 16, self._current_view)

        if signature == self._last_resize_signature:
            return

        self._last_resize_signature = signature
        self._render_current_view()

async def main(page: ft.Page):
    try:
        QuizApp(page)
    except Exception as ex:
        # Surface startup failures instead of leaving a black screen (e.g. on TestFlight).
        import traceback

        page.controls.clear()
        page.controls.append(
            ft.SafeArea(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Startup error", size=24, color="#DC2626"),
                            ft.Text(f"{type(ex).__name__}: {ex}", selectable=True),
                            ft.Text(traceback.format_exc(), size=10, selectable=True),
                        ],
                        scroll=ft.ScrollMode.ADAPTIVE,
                    ),
                    padding=20,
                    expand=True,
                ),
                expand=True,
            )
        )
        page.update()
        return

    if not page.web and page.platform is not None and not page.platform.is_mobile():
        try:
            await page.window.center()
            page.update()
        except Exception:
            pass


if __name__ == "__main__":
    ft.run(main)
