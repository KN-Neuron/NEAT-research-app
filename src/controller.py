from __future__ import annotations

import json
import time
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.aggregator import DataAggregator
from src.generator import TextGenerator, TextItem
from src.sensors.base import EEGModule, EyetrackerModule


class SessionState(Enum):
    """Stany maszyny stanów badania."""

    START_SCREEN = auto()
    SERIES_INSTRUCTION = auto()
    FIXATION_CROSS = auto()
    READING_TEXT = auto()
    USER_INPUT = auto()
    BREAK = auto()
    END_SCREEN = auto()


@dataclass(frozen=True)
class SessionConfig:
    """Parametry czasowe i strukturalne pojedynczego badania."""

    num_series: int = 3
    iterations_per_series: int = 3
    fixation_cross_duration: float = 3.0
    reading_duration: float = 10.0
    input_duration: float = 10.0
    break_duration: float = 30.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionConfig:
        """Tworzy obiekt SessionConfig ze słownika (obsługuje pełne i skrócone nazwy kluczy)."""
        return cls(
            num_series=int(data.get("num_series", 3)),
            iterations_per_series=int(data.get("iterations_per_series", 3)),
            fixation_cross_duration=float(
                data.get("fixation_cross_duration", data.get("fixation_cross", 3.0))
            ),
            reading_duration=float(
                data.get("reading_duration", data.get("reading", 10.0))
            ),
            input_duration=float(
                data.get("input_duration", data.get("input", 10.0))
            ),
            break_duration=float(
                data.get("break_duration", data.get("break", 30.0))
            ),
        )


class SessionController(QObject):
    """
    Czysta maszyna stanów zarządzająca przebiegiem badania, czasem ekspozycji
    oraz komunikacją z sensorami (EEG, Eyetracker) i agregatorem danych.
    """

    state_changed = pyqtSignal(object)  # SessionState
    instruction_ready = pyqtSignal(int, int, str)  # series_idx, total_series, instruction
    fixation_started = pyqtSignal(int, int)  # series_idx, iteration_idx
    text_ready = pyqtSignal(int, int, str)  # series_idx, iteration_idx, html_text
    user_input_started = pyqtSignal(int, int, float)  # series_idx, iteration_idx, duration_s
    break_tick = pyqtSignal(int, int, bool)  # remaining_s, total_s, is_paused
    beep_requested = pyqtSignal(int)  # remaining_s
    session_finished = pyqtSignal(str, str)  # user_id, answers_file_path

    def __init__(
        self,
        config_path: Path | str,
        eeg_module: EEGModule,
        eyetracker_module: EyetrackerModule,
        text_generator: TextGenerator,
        data_aggregator: DataAggregator,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.config_path: Path = Path(config_path)
        self.raw_config: dict[str, Any] = self._load_raw_config(self.config_path)
        self.experiment_config: SessionConfig = SessionConfig.from_dict(self.raw_config)
        demo_dict = {**self.raw_config, **self.raw_config.get("demo", {})}
        self.demo_config: SessionConfig = SessionConfig.from_dict(demo_dict)
        self.active_config: SessionConfig = self.experiment_config

        self.eeg: EEGModule = eeg_module
        self.eyetracker: EyetrackerModule = eyetracker_module
        self.generator: TextGenerator = text_generator
        self.aggregator: DataAggregator = data_aggregator

        self.state: SessionState = SessionState.START_SCREEN
        self.mode: str = "Eksperyment"
        self.user_id: str = ""
        self.current_series: int = 1
        self.current_iteration: int = 1

        self.current_text_item: TextItem | None = None
        self.text_appear_timestamp: float = 0.0
        self.text_disappear_timestamp: float = 0.0
        self._draft_answer: str = ""

        self.break_total_seconds: int = int(round(self.experiment_config.break_duration))
        self.break_remaining_seconds: int = self.break_total_seconds
        self.is_break_paused: bool = False

        self._phase_timer: QTimer = QTimer(self)
        self._phase_timer.setSingleShot(True)
        self._phase_timer.timeout.connect(self._on_phase_timer_timeout)

        self._break_timer: QTimer = QTimer(self)
        self._break_timer.setInterval(1000)
        self._break_timer.timeout.connect(self._on_break_timer_tick)

    @staticmethod
    def _load_raw_config(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Nie znaleziono pliku konfiguracyjnego: {path}")
        return dict(json.loads(path.read_text(encoding="utf-8")))

    def _send_marker_to_sensors(self, event_name: str, timestamp: float | None = None) -> float:
        """Wysyła ten sam znacznik czasu `time.perf_counter()` do obu modułów sensorów."""
        ts = timestamp if timestamp is not None else time.perf_counter()
        self.eeg.send_marker(event_name, ts)
        self.eyetracker.send_marker(event_name, ts)
        return ts

    def set_draft_answer(self, text: str) -> None:
        """Aktualizuje roboczą treść odpowiedzi (wykorzystywaną w razie upływu czasu)."""
        self._draft_answer = text

    def start_session(self, user_id: str, mode: str = "Eksperyment") -> None:
        """
        Inicjalizuje sesję badawczą:
        - wybiera konfigurację dla trybu (Eksperyment / Demo),
        - tworzy katalog wynikowy UUID w `DataAggregator`,
        - łączy się z sensorami i rozpoczyna nagrywanie,
        - przechodzi do ekranu instrukcji pierwszej serii.
        """
        self._stop_all_timers()
        self.user_id = user_id.strip()
        self.mode = mode
        self.active_config = (
            self.demo_config if mode.strip().lower() == "demo" else self.experiment_config
        )

        self.generator.reset()
        session_dir = self.aggregator.initialize_session(user_id=self.user_id, mode=self.mode)

        self.eeg.connect()
        self.eyetracker.connect()
        self.eeg.start_recording(session_dir)
        self.eyetracker.start_recording(session_dir)

        self._send_marker_to_sensors("SESSION_START")

        self.current_series = 1
        self.current_iteration = 1
        self._enter_series_instruction()

    def confirm_series_instruction(self) -> None:
        """Wywoływane po wciśnięciu klawisza Enter na ekranie polecenia serii."""
        if self.state != SessionState.SERIES_INSTRUCTION:
            return
        self.current_iteration = 1
        self._enter_fixation_cross()

    def submit_answer(self, user_answer: str) -> None:
        """Natychmiastowo zatwierdza odpowiedź uczestnika i przechodzi do kolejnego kroku."""
        if self.state != SessionState.USER_INPUT:
            return

        self._phase_timer.stop()
        submit_ts = self._send_marker_to_sensors("ANSWER_SUBMITTED")

        correct_answer = (
            self.current_text_item.correct_answer if self.current_text_item is not None else ""
        )
        text_id = self.current_text_item.id if self.current_text_item is not None else ""

        self.aggregator.record_answer(
            series_id=self.current_series,
            iteration_id=self.current_iteration,
            user_answer=user_answer,
            correct_answer=correct_answer,
            text_appear_timestamp=self.text_appear_timestamp,
            text_disappear_timestamp=self.text_disappear_timestamp,
            answer_submit_timestamp=submit_ts,
            text_id=text_id,
        )
        self._draft_answer = ""
        self._advance_after_input()

    def submit_dont_know(self) -> None:
        """Zatwierdza odpowiedź 'Nie wiem'."""
        self.submit_answer("Nie wiem")

    def toggle_break_pause(self) -> bool:
        """Wstrzymuje lub wznawia odliczanie podczas przerwy między seriami."""
        if self.state != SessionState.BREAK:
            return False

        self.is_break_paused = not self.is_break_paused
        if self.is_break_paused:
            self._break_timer.stop()
            self._send_marker_to_sensors("BREAK_PAUSED")
        else:
            self._break_timer.start(1000)
            self._send_marker_to_sensors("BREAK_RESUMED")

        self.break_tick.emit(
            self.break_remaining_seconds,
            self.break_total_seconds,
            self.is_break_paused,
        )
        return self.is_break_paused

    def _enter_series_instruction(self) -> None:
        self.state = SessionState.SERIES_INSTRUCTION
        self._send_marker_to_sensors(f"SERIES_{self.current_series}_INSTRUCTION_START")
        instruction = self.generator.get_instruction(self.current_series)
        self.state_changed.emit(SessionState.SERIES_INSTRUCTION)
        self.instruction_ready.emit(
            self.current_series,
            self.active_config.num_series,
            instruction,
        )

    def _enter_fixation_cross(self) -> None:
        self.state = SessionState.FIXATION_CROSS
        self._send_marker_to_sensors("FIXATION_START")
        self.state_changed.emit(SessionState.FIXATION_CROSS)
        self.fixation_started.emit(self.current_series, self.current_iteration)

        duration_ms = max(1, int(round(self.active_config.fixation_cross_duration * 1000)))
        self._phase_timer.start(duration_ms)

    def _enter_reading_text(self) -> None:
        self.state = SessionState.READING_TEXT
        self.current_text_item = self.generator.get_random_text(self.current_series)
        self.text_appear_timestamp = self._send_marker_to_sensors("TEXT_DISPLAY_START")

        self.state_changed.emit(SessionState.READING_TEXT)
        self.text_ready.emit(
            self.current_series,
            self.current_iteration,
            self.current_text_item.text,
        )

        duration_ms = max(1, int(round(self.active_config.reading_duration * 1000)))
        self._phase_timer.start(duration_ms)

    def _enter_user_input(self) -> None:
        self.text_disappear_timestamp = time.perf_counter()
        self.state = SessionState.USER_INPUT
        self._draft_answer = ""
        self._send_marker_to_sensors("USER_INPUT_START", self.text_disappear_timestamp)

        self.state_changed.emit(SessionState.USER_INPUT)
        self.user_input_started.emit(
            self.current_series,
            self.current_iteration,
            self.active_config.input_duration,
        )

        duration_ms = max(1, int(round(self.active_config.input_duration * 1000)))
        self._phase_timer.start(duration_ms)

    def _advance_after_input(self) -> None:
        if self.current_iteration < self.active_config.iterations_per_series:
            self.current_iteration += 1
            self._enter_fixation_cross()
        elif self.current_series < self.active_config.num_series:
            self._enter_break()
        else:
            self._enter_end_screen()

    def _enter_break(self) -> None:
        self.state = SessionState.BREAK
        self.break_total_seconds = max(1, int(round(self.active_config.break_duration)))
        self.break_remaining_seconds = self.break_total_seconds
        self.is_break_paused = False

        self._send_marker_to_sensors("BREAK_START")
        self.state_changed.emit(SessionState.BREAK)
        self.break_tick.emit(
            self.break_remaining_seconds,
            self.break_total_seconds,
            self.is_break_paused,
        )
        self._break_timer.start(1000)

    def _on_break_timer_tick(self) -> None:
        if self.state != SessionState.BREAK or self.is_break_paused:
            return

        self.break_remaining_seconds -= 1

        if self.break_remaining_seconds > 0:
            self.break_tick.emit(
                self.break_remaining_seconds,
                self.break_total_seconds,
                self.is_break_paused,
            )
            halfway = self.break_total_seconds // 2
            if self.break_remaining_seconds == halfway or (
                1 <= self.break_remaining_seconds <= 10
            ):
                self._send_marker_to_sensors(f"BREAK_BEEP_{self.break_remaining_seconds}S")
                self.beep_requested.emit(self.break_remaining_seconds)
        else:
            self._break_timer.stop()
            self._send_marker_to_sensors("BREAK_END")
            self.current_series += 1
            self.current_iteration = 1
            self._enter_series_instruction()

    def _enter_end_screen(self) -> None:
        self._stop_all_timers()
        self.state = SessionState.END_SCREEN
        self._send_marker_to_sensors("SESSION_END")

        self.eeg.stop_recording()
        self.eyetracker.stop_recording()
        answers_path = self.aggregator.finalize()

        self.state_changed.emit(SessionState.END_SCREEN)
        self.session_finished.emit(self.user_id, str(answers_path))

    def _on_phase_timer_timeout(self) -> None:
        if self.state == SessionState.FIXATION_CROSS:
            self._enter_reading_text()
        elif self.state == SessionState.READING_TEXT:
            self._enter_user_input()
        elif self.state == SessionState.USER_INPUT:
            # Czas na odpowiedź minął – zatwierdzamy stan pola tekstowego (lub pusty ciąg)
            self.submit_answer(self._draft_answer)

    def _stop_all_timers(self) -> None:
        if self._phase_timer.isActive():
            self._phase_timer.stop()
        if self._break_timer.isActive():
            self._break_timer.stop()
