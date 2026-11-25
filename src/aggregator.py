from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class AnswerRecord:
    """Pojedynczy wpis odpowiedzi uczestnika wraz ze znacznikami czasu."""

    series_id: int
    iteration_id: int
    user_answer: str
    correct_answer: str
    is_correct: bool
    text_appear_timestamp: float
    text_disappear_timestamp: float
    answer_submit_timestamp: float
    text_id: str = ""


class DataAggregator:
    """
    Moduł agregujący wyniki badania i zapisujący je do katalogu `output/<user_ID>/answers.json`.
    """

    def __init__(
        self,
        output_base_dir: Path | str = "output",
        user_id: str | None = None,
    ) -> None:
        self.output_base_dir: Path = Path(output_base_dir)
        self.user_id: str | None = None
        self.session_dir: Path | None = None
        self.mode: str = "Eksperyment"
        self.records: list[AnswerRecord] = []

        if user_id is not None:
            self.initialize_session(user_id=user_id)

    def initialize_session(self, user_id: str, mode: str = "Eksperyment") -> Path:
        """
        Tworzy katalog `output/<user_ID>/` i inicjalizuje pusty plik `answers.json`.
        """
        cleaned_id = user_id.strip()
        if not cleaned_id:
            raise ValueError("Identyfikator badanego (user_ID) nie może być pusty.")

        self.user_id = cleaned_id
        self.mode = mode
        self.records.clear()
        self.session_dir = self.output_base_dir / cleaned_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._write_to_disk()
        return self.session_dir

    @staticmethod
    def evaluate_answer(user_answer: str, correct_answer: str) -> bool:
        """Sprawdza poprawność odpowiedzi (ignorując wielkość liter i białe znaki)."""
        normalized_user = user_answer.strip().lower()
        normalized_correct = correct_answer.strip().lower()
        if not normalized_user or normalized_user == "nie wiem":
            return False
        return normalized_user == normalized_correct

    def record_answer(
        self,
        series_id: int,
        iteration_id: int,
        user_answer: str,
        correct_answer: str,
        text_appear_timestamp: float,
        text_disappear_timestamp: float,
        answer_submit_timestamp: float,
        text_id: str = "",
    ) -> AnswerRecord:
        """Dodaje odpowiedź do kolekcji i zapisuje zaktualizowany plik `answers.json`."""
        if self.session_dir is None:
            raise RuntimeError("Sesja w DataAggregator nie została zainicjalizowana.")

        is_correct = self.evaluate_answer(user_answer, correct_answer)
        record = AnswerRecord(
            series_id=series_id,
            iteration_id=iteration_id,
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            text_appear_timestamp=round(text_appear_timestamp, 6),
            text_disappear_timestamp=round(text_disappear_timestamp, 6),
            answer_submit_timestamp=round(answer_submit_timestamp, 6),
            text_id=text_id,
        )
        self.records.append(record)
        self._write_to_disk()
        return record

    def finalize(self) -> Path:
        """Finalizuje zapis pliku `answers.json` na koniec badania i zwraca ścieżkę pliku."""
        if self.session_dir is None:
            raise RuntimeError("Sesja w DataAggregator nie została zainicjalizowana.")
        return self._write_to_disk()

    def _write_to_disk(self) -> Path:
        assert self.session_dir is not None
        answers_path = self.session_dir / "answers.json"
        payload = [asdict(record) for record in self.records]
        answers_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return answers_path
