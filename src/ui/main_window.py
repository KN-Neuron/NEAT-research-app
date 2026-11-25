from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget

from src.controller import SessionController, SessionState
from src.ui.screens import (
    BreakScreen,
    EndScreen,
    FixationCrossScreen,
    ReadingTextScreen,
    SeriesInstructionScreen,
    StartScreen,
    UserInputScreen,
)
from src.ui.sound import BeepPlayer

APP_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: "Segoe UI", "Inter", Arial, sans-serif;
}
QFrame#StartCard, QFrame#InputCard {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 16px;
}
QLineEdit, QComboBox {
    background-color: #0f172a;
    color: #f8fafc;
    border: 2px solid #334155;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 16px;
}
QLineEdit:focus, QComboBox:focus {
    border: 2px solid #38bdf8;
}
QComboBox QAbstractItemView {
    background-color: #1e293b;
    color: #f8fafc;
    selection-background-color: #0284c7;
}
QPushButton {
    background-color: #334155;
    color: #f8fafc;
    border: 1px solid #475569;
    border-radius: 10px;
    padding: 10px 20px;
    font-size: 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #475569;
}
QPushButton#PrimaryButton {
    background-color: #0284c7;
    border: 1px solid #38bdf8;
    color: #ffffff;
}
QPushButton#PrimaryButton:hover {
    background-color: #0369a1;
}
QPushButton#SecondaryButton {
    background-color: #1e293b;
    border: 1px solid #475569;
    color: #cbd5e1;
}
QPushButton#SecondaryButton:hover {
    background-color: #334155;
}
"""


class MainWindow(QMainWindow):
    """
    Główne okno pełnoekranowe zarządzające przełączaniem ekranów (`QStackedWidget`)
    na podstawie sygnałów z `SessionController`.
    """

    def __init__(
        self,
        controller: SessionController,
        beep_player: BeepPlayer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller: SessionController = controller
        self.beep_player: BeepPlayer = beep_player or BeepPlayer()

        self.setWindowTitle("Aplikacja Badawcza NEAT")
        self.setStyleSheet(APP_STYLESHEET)

        self.stack: QStackedWidget = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.start_screen = StartScreen(self)
        self.instruction_screen = SeriesInstructionScreen(self)
        self.fixation_screen = FixationCrossScreen(self)
        self.reading_screen = ReadingTextScreen(self)
        self.user_input_screen = UserInputScreen(self)
        self.break_screen = BreakScreen(self)
        self.end_screen = EndScreen(self)

        self._screens_by_state: dict[SessionState, QWidget] = {
            SessionState.START_SCREEN: self.start_screen,
            SessionState.SERIES_INSTRUCTION: self.instruction_screen,
            SessionState.FIXATION_CROSS: self.fixation_screen,
            SessionState.READING_TEXT: self.reading_screen,
            SessionState.USER_INPUT: self.user_input_screen,
            SessionState.BREAK: self.break_screen,
            SessionState.END_SCREEN: self.end_screen,
        }

        for screen in self._screens_by_state.values():
            self.stack.addWidget(screen)

        self._connect_signals()
        self.stack.setCurrentWidget(self.start_screen)

    def _connect_signals(self) -> None:
        # Sygnały z widoków do kontrolera
        self.start_screen.start_requested.connect(self.controller.start_session)
        self.instruction_screen.continue_requested.connect(
            self.controller.confirm_series_instruction
        )
        self.user_input_screen.answer_submitted.connect(self.controller.submit_answer)
        self.user_input_screen.dont_know_clicked.connect(self.controller.submit_dont_know)
        self.user_input_screen.draft_changed.connect(self.controller.set_draft_answer)
        self.break_screen.pause_toggled.connect(self.controller.toggle_break_pause)
        self.end_screen.restart_requested.connect(self._on_restart_requested)

        # Sygnały z kontrolera do widoków
        self.controller.state_changed.connect(self._on_state_changed)
        self.controller.instruction_ready.connect(self._on_instruction_ready)
        self.controller.text_ready.connect(self._on_text_ready)
        self.controller.user_input_started.connect(self._on_user_input_started)
        self.controller.break_tick.connect(self._on_break_tick)
        self.controller.beep_requested.connect(self._on_beep_requested)
        self.controller.session_finished.connect(self._on_session_finished)

    def _on_state_changed(self, state: SessionState) -> None:
        target_widget = self._screens_by_state.get(state)
        if target_widget is not None:
            self.stack.setCurrentWidget(target_widget)

        if state == SessionState.SERIES_INSTRUCTION:
            self.instruction_screen.setFocus(Qt.FocusReason.OtherFocusReason)
        elif state == SessionState.USER_INPUT:
            self.user_input_screen.prepare_for_input()

    def _on_instruction_ready(
        self, series_idx: int, total_series: int, instruction: str
    ) -> None:
        self.instruction_screen.set_instruction(series_idx, total_series, instruction)

    def _on_text_ready(self, _series_idx: int, _iteration_idx: int, html_text: str) -> None:
        self.reading_screen.set_reading_text(html_text)

    def _on_user_input_started(
        self, _series_idx: int, _iteration_idx: int, _duration_s: float
    ) -> None:
        self.user_input_screen.prepare_for_input()

    def _on_break_tick(
        self, remaining_s: int, total_s: int, is_paused: bool
    ) -> None:
        self.break_screen.update_timer(remaining_s, total_s, is_paused)

    def _on_beep_requested(self, remaining_s: int) -> None:
        # Wyższy ton dla ostatniej sekundy przerwy, standardowy dla 15s i 10..2s
        freq = 1046.5 if remaining_s == 1 else 880.0
        self.beep_player.play_beep(frequency_hz=freq, duration_ms=140)

    def _on_session_finished(self, user_id: str, answers_path: str) -> None:
        self.end_screen.set_summary(user_id, answers_path)

    def _on_restart_requested(self) -> None:
        self.controller.state = SessionState.START_SCREEN
        self.start_screen.generate_new_uuid()
        self.stack.setCurrentWidget(self.start_screen)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event is not None:
            if (
                self.controller.state == SessionState.SERIES_INSTRUCTION
                and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            ):
                event.accept()
                self.controller.confirm_series_instruction()
                return
            if event.key() == Qt.Key.Key_Escape:
                event.accept()
                self.close()
                return
        super().keyPressEvent(event)
