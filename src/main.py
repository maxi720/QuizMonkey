import csv
import os
import shutil

import flet as ft


class QuizApp:
    def __init__(self, page: ft.Page):
        self.page = page

        self.page.title = "Quiz App"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.padding = ft.Padding.only(top=30)

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

        os.makedirs(self.quiz_folder, exist_ok=True)

        self.fragen: list[list[str]] = []
        self.current_question = 0
        self.correct_answer = ""
        self.correct_count = 0
        self.wrong_questions: list[list[str]] = []
        self.quiz_buttons: list[ft.Control] = []
        self.answer_buttons: list[ft.Button] = []
        self.next_button: ft.Button | None = None

        self.page.on_resize = self._on_resize
        self._current_view = "start"

        self._question_text: ft.Text | None = None
        self._answer_texts: list[ft.Text] = []
        self._q_container: ft.Container | None = None
        self._ans_row_containers: list[ft.Container] = []
        self._next_container: ft.Container | None = None
        self._bottom_container: ft.Container | None = None
        self._back_button: ft.Button | None = None

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
        width = self.page.width or 600
        height = self.page.height or 800
        return max(0.5, min(1.5, min(width / 600, height / 750)))

    def _get_text_size(self, base: int) -> int:
        return max(10, int(base * self._get_scale()))

    def _get_pad(self, base: int) -> int:
        return max(2, int(base * self._get_scale()))

    def make_button_style(
        self,
        bgcolor,
        text_size=20,
        radius=12,
        padding=None,
        side=None,
    ) -> ft.ButtonStyle:
        return ft.ButtonStyle(
            text_style=ft.TextStyle(size=text_size, weight=ft.FontWeight.W_600),
            color=ft.Colors.WHITE,
            bgcolor=bgcolor,
            padding=padding,
            shape=ft.RoundedRectangleBorder(radius=radius),
            side=side,
        )

    def show_startpage(self) -> None:
        self._current_view = "start"
        self.page.controls.clear()
        self.next_button = None
        self.load_custom_quizzes()

        header = ft.Container(
            content=ft.Text(
                "Choose a Quiz",
                size=self._get_text_size(40),
                weight=ft.FontWeight.BOLD,
            ),
            padding=ft.Padding.only(top=self._get_pad(30), bottom=self._get_pad(10)),
            alignment=ft.Alignment.CENTER,
        )

        quiz_list = ft.Column(
            controls=self.quiz_buttons,
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True,
            spacing=0,
        )

        action_buttons = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Button(
                        content="DELETE",
                        on_click=self.remove_csv,
                        height=self._get_pad(45),
                        expand=True,
                        style=self.make_button_style(
                            ft.Colors.RED,
                            text_size=self._get_text_size(18),
                        ),
                    ),
                    ft.Button(
                        content="UPLOAD",
                        on_click=self.upload_csv,
                        height=self._get_pad(45),
                        expand=True,
                        style=self.make_button_style(
                            ft.Colors.GREEN,
                            text_size=self._get_text_size(18),
                        ),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding.only(
                left=self._get_pad(16),
                right=self._get_pad(16),
                top=self._get_pad(10),
                bottom=self._get_pad(20),
            ),
        )

        self.page.controls.append(
            ft.Column(
                controls=[header, quiz_list, action_buttons],
                expand=True,
                spacing=0,
            )
        )
        self.page.update()

    def load_custom_quizzes(self) -> None:
        self.quiz_buttons.clear()

        try:
            files = sorted(os.listdir(self.quiz_folder))
        except OSError:
            return

        for file_name in files:
            if file_name.lower().endswith(".csv"):
                filepath = os.path.join(self.quiz_folder, file_name)
                button_text = os.path.splitext(file_name)[0]

                quiz_button = ft.Button(
                    content=button_text,
                    data=filepath,
                    expand=True,
                    on_click=lambda e, f=filepath: self.start_quiz(f),
                    style=ft.ButtonStyle(
                        text_style=ft.TextStyle(
                            size=self._get_text_size(18), weight=ft.FontWeight.W_600
                        ),
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.PURPLE,
                        padding=ft.Padding.symmetric(
                            horizontal=self._get_pad(12),
                            vertical=self._get_pad(12),
                        ),
                        shape=ft.RoundedRectangleBorder(radius=12),
                    ),
                )

                self.quiz_buttons.append(
                    ft.Container(
                        content=ft.Row([quiz_button]),
                        padding=ft.Padding.symmetric(
                            horizontal=self._get_pad(16),
                            vertical=self._get_pad(4),
                        ),
                    )
                )

    async def upload_csv(self, e) -> None:
        try:
            picker = ft.FilePicker()
            files = await picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["csv"],
            )

            if not files:
                return

            selected_file = files[0]
            original_filename = selected_file.name or "upload.csv"

            if not original_filename.lower().endswith(".csv"):
                self.show_message("Fehler: Nur CSV-Dateien können hochgeladen werden!")
                return

            file_path = getattr(selected_file, "path", None)
            if not file_path:
                self.show_message("Fehler: Kein Zugriff auf Datei.")
                return

            destination = os.path.join(self.quiz_folder, original_filename)
            shutil.copy(file_path, destination)

            self.show_message(f"Quiz '{original_filename}' hochgeladen!")
            self.show_startpage()

        except Exception as ex:
            self.show_message(f"Fehler beim Hochladen: {ex}")

    def remove_csv(self, e) -> None:
        try:
            files = [
                file_name
                for file_name in os.listdir(self.quiz_folder)
                if file_name.lower().endswith(".csv")
            ]
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
        else:
            self.show_message("Keine Fragen in dieser Datei gefunden.")

    def show_question_page(self) -> None:
        self._current_view = "question"
        self.page.controls.clear()

        if self.current_question >= len(self.fragen):
            self.show_result()
            return

        frage_data = self.fragen[self.current_question]

        if len(frage_data) != 6:
            self.page.controls.append(
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        "FILE ERROR!",
                                        size=50,
                                        color=ft.Colors.RED,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Button(
                                        content="BACK",
                                        on_click=lambda e: self.show_startpage(),
                                        style=self.make_button_style(
                                            ft.Colors.BLUE,
                                            text_size=40,
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
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    expand=True,
                )
            )
            self.page.update()
            return

        self.correct_answer = frage_data[5]
        self.answer_buttons = []
        self._answer_texts = []
        self._ans_row_containers = []
        answer_containers: list[ft.Control] = []

        for i in range(1, 5):
            answer_text = frage_data[i]
            if answer_text:
                ans_text = ft.Text(
                    answer_text,
                    size=self._get_text_size(28),
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.LEFT,
                )
                self._answer_texts.append(ans_text)
                btn = ft.Button(
                    content=ft.Container(
                        content=ans_text,
                        alignment=ft.Alignment(-1, 0),
                        expand=True,
                    ),
                    data=answer_text,
                    expand=True,
                    on_click=self.create_answer_handler(answer_text),
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.LIGHT_BLUE,
                        padding=ft.Padding.all(10),
                        shape=ft.RoundedRectangleBorder(radius=12),
                        side=ft.BorderSide(3, ft.Colors.BLACK),
                    ),
                )
                self.answer_buttons.append(btn)
                ans_container = ft.Container(
                    content=ft.Row([btn]),
                    padding=ft.Padding.symmetric(
                        horizontal=16, vertical=self._get_pad(3)
                    ),
                )
                self._ans_row_containers.append(ans_container)
                answer_containers.append(ans_container)

        self.next_button = ft.Button(
            content="NEXT",
            on_click=self.next_question,
            disabled=True,
            style=self._next_btn_style(),
        )

        self._back_button = ft.Button(
            content="HOME",
            on_click=lambda e: self.show_startpage(),
            style=self._back_btn_style(),
        )
        back_button = self._back_button

        self._question_text = ft.Text(
            frage_data[0],
            style=ft.TextStyle(
                size=self._get_text_size(30),
                weight=ft.FontWeight.W_600,
                color=ft.Colors.WHITE,
            ),
        )

        self._q_container = ft.Container(
            content=self._question_text,
            alignment=ft.Alignment.TOP_LEFT,
            padding=ft.Padding.only(
                left=16,
                top=self._get_pad(25),
                bottom=self._get_pad(15),
            ),
        )

        self._next_container = ft.Container(
            content=self.next_button,
            padding=ft.Padding.only(top=self._get_pad(12), right=16),
            alignment=ft.Alignment.CENTER_RIGHT,
        )

        self._bottom_container = ft.Container(
            content=ft.Row(
                controls=[
                    back_button,
                    ft.Container(expand=True),
                    ft.Text(
                        f"{self.current_question + 1}/{len(self.fragen)}",
                        style=ft.TextStyle(
                            size=self._get_text_size(22),
                            weight=ft.FontWeight.W_500,
                            color=ft.Colors.GREY,
                        ),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.only(
                left=20, right=20, bottom=self._get_pad(20)
            ),
        )

        self.page.padding = ft.Padding.only(top=self._get_pad(20))

        self.page.controls.append(
            ft.Column(
                controls=[
                    self._q_container,
                    *answer_containers,
                    self._next_container,
                    ft.Container(expand=True),
                    self._bottom_container,
                ],
                expand=True,
                spacing=0,
            )
        )

        self.page.update()

    def load_questions(self, filename: str) -> None:
        self.fragen.clear()

        try:
            with open(filename, "r", encoding="utf-8") as data:
                reader = csv.reader(data, delimiter=";")
                for zeile in reader:
                    if any(cell.strip() for cell in zeile):
                        self.fragen.append(zeile)
        except FileNotFoundError:
            self.show_message(f"Datei '{filename}' nicht gefunden!")
        except UnicodeDecodeError:
            self.show_message(
                f"Datei '{filename}' hat eine ungültige Zeichenkodierung (kein UTF-8)."
            )
        except PermissionError:
            self.show_message(f"Keine Leseberechtigung für '{filename}'.")
        except Exception as ex:
            self.show_message(f"Fehler beim Laden der Datei: {ex}")

        self.current_question = 0
        self.correct_count = 0
        self.wrong_questions = []

    def check_answer(self, answer: str) -> None:
        is_correct = answer == self.correct_answer

        if is_correct:
            self.correct_count += 1
        else:
            self.wrong_questions.append(self.fragen[self.current_question])

        for button in self.answer_buttons:
            if button.data == answer:
                button.style.bgcolor = ft.Colors.GREEN if is_correct else ft.Colors.RED
            elif button.data == self.correct_answer:
                button.style.bgcolor = ft.Colors.GREEN
            button.disabled = True

        if self.next_button:
            self.next_button.disabled = False

        self.page.update()

    def next_question(self, e) -> None:
        self.current_question += 1
        self.show_question_page()

    def show_result(self) -> None:
        self._current_view = "result"
        total = len(self.fragen)
        correct = self.correct_count
        wrong = total - correct
        score = round(correct / total * 100, 1) if total > 0 else 0.0

        self.page.controls.clear()

        self.page.controls.append(
            ft.Container(
                content=ft.Text(
                    "RESULT",
                    size=self._get_text_size(36),
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding.only(
                    top=self._get_pad(20), bottom=self._get_pad(16)
                ),
            )
        )

        self.page.controls.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        "CORRECT",
                                        size=self._get_text_size(16),
                                        color=ft.Colors.WHITE,
                                    ),
                                    ft.Text(
                                        str(correct),
                                        size=self._get_text_size(48),
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.WHITE,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=self._get_pad(4),
                            ),
                            bgcolor=ft.Colors.GREEN,
                            border_radius=12,
                            padding=self._get_pad(20),
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        "FALSE",
                                        size=self._get_text_size(16),
                                        color=ft.Colors.WHITE,
                                    ),
                                    ft.Text(
                                        str(wrong),
                                        size=self._get_text_size(48),
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.WHITE,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=self._get_pad(4),
                            ),
                            bgcolor=ft.Colors.RED,
                            border_radius=12,
                            padding=self._get_pad(20),
                            expand=True,
                        ),
                    ],
                    spacing=self._get_pad(12),
                ),
                padding=ft.Padding.symmetric(horizontal=self._get_pad(16)),
            )
        )

        self.page.controls.append(
            ft.Container(
                content=ft.Text(
                    f"{score} %",
                    size=self._get_text_size(60),
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding.symmetric(vertical=self._get_pad(20)),
            )
        )

        btn_end = ft.Button(
            content="BACK HOME",
            on_click=lambda e: self.show_startpage(),
            height=self._get_pad(55),
            style=ft.ButtonStyle(
                text_style=ft.TextStyle(
                    size=self._get_text_size(20), weight=ft.FontWeight.W_600
                ),
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE,
                padding=ft.Padding.symmetric(vertical=self._get_pad(15)),
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
        )

        col_controls: list[ft.Control] = []

        if wrong > 0:
            col_controls.append(
                ft.Button(
                    content="REPEAT INCORRECT QUESTIONS",
                    on_click=self.restart_wrong_questions,
                    height=self._get_pad(55),
                    style=ft.ButtonStyle(
                        text_style=ft.TextStyle(
                            size=self._get_text_size(20), weight=ft.FontWeight.W_600
                        ),
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.ORANGE_500,
                        padding=ft.Padding.symmetric(vertical=self._get_pad(15)),
                        shape=ft.RoundedRectangleBorder(radius=12),
                    ),
                )
            )

        col_controls.append(btn_end)

        self.page.controls.append(
            ft.Column(
                controls=[
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Column(
                            controls=col_controls,
                            spacing=self._get_pad(12),
                            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                        ),
                        padding=ft.Padding.only(
                            left=self._get_pad(16),
                            right=self._get_pad(16),
                            bottom=self._get_pad(20),
                        ),
                    ),
                ],
                expand=True,
            )
        )

        self.page.update()

    def restart_wrong_questions(self, e) -> None:
        self.fragen = self.wrong_questions.copy()
        self.wrong_questions = []
        self.current_question = 0
        self.correct_count = 0
        self.show_question_page()

    def _back_btn_style(self) -> ft.ButtonStyle:
        return ft.ButtonStyle(
            text_style=ft.TextStyle(
                size=self._get_text_size(22),
                weight=ft.FontWeight.W_800,
            ),
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE,
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
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE,
            padding=ft.Padding.symmetric(
                horizontal=14,
                vertical=self._get_text_size(17),
            ),
            shape=ft.RoundedRectangleBorder(radius=15),
        )

    def _on_resize(self, e) -> None:
        if self._current_view == "start":
            self.show_startpage()
            return
        if self._current_view == "result":
            self.show_result()
            return

        changed = False
        if self.next_button:
            self.next_button.style = self._next_btn_style()
            changed = True
        if self._question_text:
            self._question_text.style.size = self._get_text_size(30)
            changed = True
        for ans_text in self._answer_texts:
            ans_text.size = self._get_text_size(28)
            changed = True
        if self._q_container:
            self._q_container.padding = ft.Padding.only(
                left=16,
                top=self._get_pad(25),
                bottom=self._get_pad(15),
            )
            changed = True
        for c in self._ans_row_containers:
            c.padding = ft.Padding.symmetric(
                horizontal=16, vertical=self._get_pad(3)
            )
            changed = True
        if self._next_container:
            self._next_container.padding = ft.Padding.only(
                top=self._get_pad(12), right=16
            )
            changed = True
        if self._bottom_container:
            self._bottom_container.padding = ft.Padding.only(
                left=20, right=20, bottom=self._get_pad(20)
            )
            changed = True
        if self._back_button:
            self._back_button.style = self._back_btn_style()
            changed = True
        if changed:
            self.page.padding = ft.Padding.only(top=self._get_pad(20))
            self.page.update()

    def create_answer_handler(self, answer: str):
        def handler(e):
            self.check_answer(answer)
        return handler


async def main(page: ft.Page):
    QuizApp(page)

    if not page.web and page.platform is not None and not page.platform.is_mobile():
        try:
            await page.window.center()
            page.update()
        except Exception:
            pass


if __name__ == "__main__":
    ft.run(main)