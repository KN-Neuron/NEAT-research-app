from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TextItem:
    """Pojedynczy element tekstowy wraz z poprawną odpowiedzią."""

    id: str
    text: str
    correct_answer: str


@dataclass(frozen=True)
class SeriesData:
    """Dane pojedynczej serii badawczej (polecenie oraz pula tekstów)."""

    series_id: int
    instruction: str
    texts: list[TextItem]


class TextGenerator:
    """Moduł odpowiedzialny za wczytywanie bazy tekstów i losowanie niepowtarzających się pozycji."""

    def __init__(self, texts_path: Path | str, seed: int | None = None) -> None:
        self.texts_path: Path = Path(texts_path)
        self._rng: random.Random = random.Random(seed)
        self._series_list: list[SeriesData] = self._load_texts(self.texts_path)
        self._used_ids_by_series: dict[int, set[str]] = {}

    @staticmethod
    def _load_texts(path: Path) -> list[SeriesData]:
        if not path.exists():
            raise FileNotFoundError(f"Nie znaleziono pliku bazy tekstów: {path}")

        raw_data = json.loads(path.read_text(encoding="utf-8"))
        series_raw = raw_data.get("series", [])
        if not series_raw:
            raise ValueError(f"Plik '{path}' nie zawiera żadnych zdefiniowanych serii.")

        series_list: list[SeriesData] = []
        for idx, item in enumerate(series_raw, start=1):
            series_id = int(item.get("series_id", idx))
            instruction = str(item.get("instruction", ""))
            texts_raw = item.get("texts", [])
            texts: list[TextItem] = []
            for t_idx, t_item in enumerate(texts_raw, start=1):
                text_id = str(t_item.get("id", f"s{series_id}_t{t_idx}"))
                text_content = str(t_item.get("text", ""))
                correct_answer = str(t_item.get("correct_answer", ""))
                texts.append(
                    TextItem(
                        id=text_id,
                        text=text_content,
                        correct_answer=correct_answer,
                    )
                )
            if not texts:
                raise ValueError(f"Seria {series_id} nie zawiera żadnych tekstów.")
            series_list.append(
                SeriesData(
                    series_id=series_id,
                    instruction=instruction,
                    texts=texts,
                )
            )
        return series_list

    def reset(self) -> None:
        """Czyści historię wylosowanych tekstów we wszystkich seriach."""
        self._used_ids_by_series.clear()

    def reset_series(self, series_index: int) -> None:
        """Czyści historię wylosowanych tekstów dla wskazanej serii (indeks 0-based lub 1-based)."""
        self._used_ids_by_series.pop(series_index, None)

    def _resolve_series(self, series_index: int) -> SeriesData:
        """Zwraca dane serii dla podanego indeksu (1-based)."""
        if series_index < 1:
            raise ValueError(f"Indeks serii musi być >= 1 (otrzymano: {series_index}).")
        idx = (series_index - 1) % len(self._series_list)
        return self._series_list[idx]

    def get_instruction(self, series_index: int) -> str:
        """Zwraca treść polecenia dla danej serii (numerowanej od 1)."""
        return self._resolve_series(series_index).instruction

    def get_random_text(self, series_index: int) -> TextItem:
        """
        Losuje nieużyty jeszcze w danej serii tekst.

        :param series_index: Numer serii (1-based).
        :return: Obiekt TextItem.
        :raises ValueError: Gdy wszystkie dostępne teksty w danej serii zostały już wykorzystane.
        """
        series_data = self._resolve_series(series_index)
        used_ids = self._used_ids_by_series.setdefault(series_index, set())

        available_texts = [t for t in series_data.texts if t.id not in used_ids]
        if not available_texts:
            raise ValueError(
                f"Wyczerpano pulę niepowtarzających się tekstów dla serii {series_index} "
                f"(dostępnych: {len(series_data.texts)})."
            )

        chosen = self._rng.choice(available_texts)
        used_ids.add(chosen.id)
        return chosen
