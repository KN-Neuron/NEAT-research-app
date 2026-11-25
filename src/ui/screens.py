from __future__ import annotations

import uuid

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
     QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class StartScreen(QWidget):
    """Ekran startowy badania: wybór trybu, Subject ID (UUID) oraz start sesji."""

    start_requested = pyqtSignal(str, str)  # user_id, mode

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self.generate_new_uuid()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame(self)
        card.setObjectName("StartCard")
        card.setFixedWidth(620)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 48, 48, 48)
        card_layout.setSpacing(22)

        title = QLabel("Aplikacja Badawcza NEAT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: 700; color: #f8fafc;")
        card_layout.addWidget(title)

        subtitle = QLabel("Protokół rejestracji EEG / Eyetracker")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #94a3b8; margin-bottom: 12px;")
        card_layout.addWidget(subtitle)

        mode_label = QLabel("Tryb uruchomienia:")
        mode_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #e2e8f0;")
        card_layout.addWidget(mode_label)

        self.mode_combo = QComboBox(self)
        self.mode_combo.addItems(["Eksperyment", "Demo"])
        self.mode_combo.setMinimumHeight(46)
        card_layout.addWidget(self.mode_combo)

        uuid_label = QLabel("Subject ID (UUID):")
        uuid_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #e2e8f0;")
        card_layout.addWidget(uuid_label)

        uuid_row = QHBoxLayout()
        uuid_row.setSpacing(12)

        self.uuid_input = QLineEdit(self)
        self.uuid_input.setPlaceholderText("Wprowadź lub wygeneruj UUID uczestnika...")
        self.uuid_input.setMinimumHeight(46)
        uuid_row.addWidget(self.uuid_input, stretch=1)

        self.generate_uuid_btn = QPushButton("Generuj UUID", self)
        self.generate_uuid_btn.setMinimumHeight(46)
        self.generate_uuid_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_uuid_btn.clicked.connect(self.generate_new_uuid)
        uuid_row.addWidget(self.generate_uuid_btn)

        card_layout.addLayout(uuid_row)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("font-size: 14px; color: #f87171;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)

        self.start_btn = QPushButton("Start badania", self)
        self.start_btn.setObjectName("PrimaryButton")
        self.start_btn.setMinimumHeight(54)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self._on_start_clicked)
        card_layout.addWidget(self.start_btn)

        self.exit_btn = QPushButton("Zamknij aplikację (Esc)", self)
        self.exit_btn.setObjectName("SecondaryButton")
        self.exit_btn.setMinimumHeight(42)
        self.exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exit_btn.clicked.connect(self._on_exit_clicked)
        card_layout.addWidget(self.exit_btn)

        outer_layout.addWidget(card)

    def generate_new_uuid(self) -> None:
        """Generuje nowy identyfikator UUID v4 i wpisuje go w pole tekstowe."""
        self.uuid_input.setText(str(uuid.uuid4()))
        self.error_label.hide()

    def _on_start_clicked(self) -> None:
        subject_id = self.uuid_input.text().strip()
        if not subject_id:
            self.error_label.setText("Pole Subject ID (UUID) nie może być puste.")
            self.error_label.show()
            return

        self.error_label.hide()
        mode = self.mode_combo.currentText()
        self.start_requested.emit(subject_id, mode)

    @staticmethod
    def _on_exit_clicked() -> None:
        app = QApplication.instance()
        if app is not None:
            app.quit()


class SeriesInstructionScreen(QWidget):
    """Ekran polecenia dla danej serii (SERIES_INSTRUCTION). Czeka na klawisz Enter."""

    continue_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(120, 80, 120, 80)
        layout.setSpacing(36)

        self.series_header_label = QLabel("Seria 1")
        self.series_header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.series_header_label.setStyleSheet(
            "font-size: 24px; font-weight: 600; color: #38bdf8; letter-spacing: 1px;"
        )
        layout.addWidget(self.series_header_label)

        self.instruction_label = QLabel("")
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setWordWrap(True)
        self.instruction_label.setTextFormat(Qt.TextFormat.RichText)
        self.instruction_label.setMaximumWidth(1000)
        self.instruction_label.setStyleSheet(
            "font-size: 34px; font-weight: 600; color: #f8fafc; line-height: 1.4;"
        )
        layout.addWidget(self.instruction_label)

        prompt_label = QLabel("Naciśnij klawisz <b>ENTER</b>, aby rozpocząć serię")
        prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prompt_label.setTextFormat(Qt.TextFormat.RichText)
        prompt_label.setStyleSheet(
            "font-size: 20px; color: #94a3b8; margin-top: 32px; padding: 14px 28px; "
            "border: 1px solid #334155; border-radius: 10px; background-color: #1e293b;"
        )
        layout.addWidget(prompt_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_instruction(self, series_index: int, total_series: int, instruction: str) -> None:
        """Ustawia numer serii oraz treść polecenia."""
        self.series_header_label.setText(f"SERIA {series_index} Z {total_series}")
        self.instruction_label.setText(instruction)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event is not None and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.accept()
            self.continue_requested.emit()
            return
        super().keyPressEvent(event)


class FixationCrossScreen(QWidget):
    """Ekran z krzyżykiem fiksacji (+) idealnie na środku ekranu (FIXATION_CROSS)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cross_label = QLabel("+", self)
        self.cross_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cross_label.setStyleSheet(
            "font-size: 120px; font-weight: 400; color: #f8fafc;"
        )
        layout.addWidget(self.cross_label, alignment=Qt.AlignmentFlag.AlignCenter)


class ReadingTextScreen(QWidget):
    """Ekran ekspozycji tekstu badawczego z obsługą formatowania HTML/RichText (READING_TEXT)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(140, 100, 140, 100)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text_label = QLabel("", self)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setTextFormat(Qt.TextFormat.RichText)
        self.text_label.setMaximumWidth(1100)
        self.text_label.setStyleSheet(
            "font-size: 32px; color: #f8fafc; line-height: 1.6;"
        )
        layout.addWidget(self.text_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_reading_text(self, html_text: str) -> None:
        """Ustawia tekst (HTML/RichText) do wyświetlenia."""
        self.text_label.setText(html_text)


class UserInputScreen(QWidget):
    """
    Ekran wprowadzania odpowiedzi (USER_INPUT).
    Automatycznie ustawia focus na polu tekstowym i zatwierdza po wciśnięciu Enter.
    """

    answer_submitted = pyqtSignal(str)
    dont_know_clicked = pyqtSignal()
    draft_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container = QFrame(self)
        container.setObjectName("InputCard")
        container.setFixedWidth(640)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(24)

        prompt = QLabel("Wpisz swoją odpowiedź i naciśnij Enter:")
        prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prompt.setStyleSheet("font-size: 24px; font-weight: 600; color: #f8fafc;")
        layout.addWidget(prompt)

        self.answer_input = QLineEdit(self)
        self.answer_input.setPlaceholderText("Twoja odpowiedź...")
        self.answer_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.answer_input.setMinimumHeight(58)
        self.answer_input.setStyleSheet(
            "font-size: 26px; font-weight: 600; padding: 8px 16px;"
        )
        self.answer_input.textChanged.connect(self.draft_changed.emit)
        self.answer_input.returnPressed.connect(self._on_return_pressed)
        layout.addWidget(self.answer_input)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(16)

        self.submit_btn = QPushButton("Zatwierdź (Enter)", self)
        self.submit_btn.setObjectName("PrimaryButton")
        self.submit_btn.setMinimumHeight(48)
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.clicked.connect(self._on_return_pressed)
        buttons_row.addWidget(self.submit_btn)

        self.dont_know_btn = QPushButton("Nie wiem", self)
        self.dont_know_btn.setObjectName("SecondaryButton")
        self.dont_know_btn.setMinimumHeight(48)
        self.dont_know_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dont_know_btn.clicked.connect(self.dont_know_clicked.emit)
        buttons_row.addWidget(self.dont_know_btn)

        layout.addLayout(buttons_row)
        outer_layout.addWidget(container)

    def prepare_for_input(self) -> None:
        """Czyści pole odpowiedzi i wymusza natychmiastowy focus klawiatury (`setFocus()`)."""
        self.answer_input.clear()
        self.answer_input.setFocus(Qt.FocusReason.OtherFocusReason)
        QTimer.singleShot(0, self.answer_input.setFocus)

    def showEvent(self, event: object) -> None:
        super().showEvent(event)  # type: ignore[arg-type]
        self.answer_input.setFocus(Qt.FocusReason.OtherFocusReason)
        QTimer.singleShot(0, self.answer_input.setFocus)

    def _on_return_pressed(self) -> None:
        self.answer_submitted.emit(self.answer_input.text())


class BreakScreen(QWidget):
    """
    Ekran przerwy między seriami (BREAK).
    Wyświetla odliczanie czasu oraz przycisk „Wstrzymaj / Wznów badanie”.
    """

    pause_toggled = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(28)

        title = QLabel("Przerwa między seriami")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: 600; color: #94a3b8;")
        layout.addWidget(title)

        self.timer_label = QLabel("30 s")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet(
            "font-size: 96px; font-weight: 700; color: #38bdf8;"
        )
        layout.addWidget(self.timer_label)

        self.status_label = QLabel("Odpocznij chwilę przed następną serią.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 20px; color: #cbd5e1;")
        layout.addWidget(self.status_label)

        self.pause_btn = QPushButton("Wstrzymaj / Wznów badanie", self)
        self.pause_btn.setObjectName("SecondaryButton")
        self.pause_btn.setMinimumSize(320, 52)
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.clicked.connect(self.pause_toggled.emit)
        layout.addWidget(self.pause_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def update_timer(self, remaining_seconds: int, total_seconds: int, is_paused: bool) -> None:
        """Aktualizuje widoczny na środku licznik przerwy oraz stan wstrzymania."""
        self.timer_label.setText(f"{remaining_seconds} s")
        if is_paused:
            self.status_label.setText("Badanie wstrzymane (pauza).")
            self.timer_label.setStyleSheet(
                "font-size: 96px; font-weight: 700; color: #fbbf24;"
            )
        else:
            self.status_label.setText(
                f"Pozostało {remaining_seconds} z {total_seconds} sekund przerwy."
            )
            self.timer_label.setStyleSheet(
                "font-size: 96px; font-weight: 700; color: #38bdf8;"
            )


class EndScreen(QWidget):
    """Ekran końcowy badania (END_SCREEN) z podziękowaniem i informacją o zapisie."""

    restart_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)

        title = QLabel("Dziękujemy za udział w badaniu!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 42px; font-weight: 700; color: #4ade80;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Nagrywanie z sensorów zostało zatrzymane, a wyniki zapisano pomyślnie."
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 20px; color: #cbd5e1;")
        layout.addWidget(subtitle)

        self.details_label = QLabel("")
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_label.setStyleSheet(
            "font-size: 16px; color: #94a3b8; margin-top: 8px; margin-bottom: 16px;"
        )
        layout.addWidget(self.details_label)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(16)
        buttons_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.new_session_btn = QPushButton("Nowa sesja badawcza", self)
        self.new_session_btn.setObjectName("PrimaryButton")
        self.new_session_btn.setMinimumSize(240, 50)
        self.new_session_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_session_btn.clicked.connect(self.restart_requested.emit)
        buttons_row.addWidget(self.new_session_btn)

        self.close_btn = QPushButton("Zamknij aplikację", self)
        self.close_btn.setObjectName("SecondaryButton")
        self.close_btn.setMinimumSize(240, 50)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self._on_close_clicked)
        buttons_row.addWidget(self.close_btn)

        layout.addLayout(buttons_row)

    def set_summary(self, user_id: str, answers_path: str) -> None:
        """Wyświetla podsumowanie identyfikatora badanego i ścieżki zapisu pliku `answers.json`."""
        self.details_label.setText(
            f"Subject ID: {user_id}\nZapisano wyniki w: {answers_path}"
        )

    @staticmethod
    def _on_close_clicked() -> None:
        app = QApplication.instance()
        if app is not None:
            app.quit()
