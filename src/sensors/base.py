from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class EEGModule(ABC):
    """Abstrakcyjny interfejs dla modułu EEG."""

    @abstractmethod
    def connect(self) -> bool:
        """Inicjalizuje połączenie z urządzeniem EEG."""
        raise NotImplementedError

    @abstractmethod
    def start_recording(self, session_dir: Path | str) -> None:
        """Rozpoczyna nagrywanie sygnału EEG do wskazanego katalogu sesji."""
        raise NotImplementedError

    @abstractmethod
    def stop_recording(self) -> None:
        """Zatrzymuje nagrywanie sygnału EEG i finalizuje zapis danych."""
        raise NotImplementedError

    @abstractmethod
    def send_marker(self, event_name: str, timestamp: float) -> None:
        """Wysyła znacznik czasowy (marker zdarzenia) do strumienia EEG."""
        raise NotImplementedError


class EyetrackerModule(ABC):
    """Abstrakcyjny interfejs dla modułu okulografu (Eyetrackera)."""

    @abstractmethod
    def connect(self) -> bool:
        """Inicjalizuje połączenie z urządzeniem Eyetracker."""
        raise NotImplementedError

    @abstractmethod
    def start_recording(self, session_dir: Path | str) -> None:
        """Rozpoczyna nagrywanie danych okulograficznych do wskazanego katalogu sesji."""
        raise NotImplementedError

    @abstractmethod
    def stop_recording(self) -> None:
        """Zatrzymuje nagrywanie danych okulograficznych i finalizuje zapis."""
        raise NotImplementedError

    @abstractmethod
    def send_marker(self, event_name: str, timestamp: float) -> None:
        """Wysyła znacznik czasowy (marker zdarzenia) do strumienia Eyetrackera."""
        raise NotImplementedError
