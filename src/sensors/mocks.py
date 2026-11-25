from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from src.sensors.base import EEGModule, EyetrackerModule


@dataclass(frozen=True)
class SensorMarker:
    """Reprezentacja pojedynczego markera zdarzenia zarejestrowanego przez sensor."""

    event_name: str
    timestamp: float


class MockEEGModule(EEGModule):
    """Zaślepka (mock) modułu EEG symulująca rejestrację sygnału i markerów."""

    def __init__(self, sampling_rate_hz: int = 256) -> None:
        self.sampling_rate_hz: int = sampling_rate_hz
        self.is_connected: bool = False
        self.is_recording: bool = False
        self.session_dir: Path | None = None
        self.start_timestamp: float | None = None
        self.stop_timestamp: float | None = None
        self.markers: list[SensorMarker] = []

    def connect(self) -> bool:
        ts = time.perf_counter()
        self.is_connected = True
        print(f"[EEG MOCK][{ts:.6f}s] Połączono z symulatorem EEG ({self.sampling_rate_hz} Hz).")
        return True

    def start_recording(self, session_dir: Path | str) -> None:
        if not self.is_connected:
            self.connect()
        ts = time.perf_counter()
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.is_recording = True
        self.start_timestamp = ts
        self.stop_timestamp = None
        self.markers.clear()
        print(f"[EEG MOCK][{ts:.6f}s] Rozpoczęto nagrywanie EEG w katalogu: {self.session_dir}")

    def stop_recording(self) -> None:
        ts = time.perf_counter()
        if not self.is_recording:
            print(f"[EEG MOCK][{ts:.6f}s] Nagrywanie EEG było już zatrzymane.")
            return

        self.is_recording = False
        self.stop_timestamp = ts
        duration = (ts - self.start_timestamp) if self.start_timestamp is not None else 0.0
        simulated_samples = int(duration * self.sampling_rate_hz)

        if self.session_dir is not None:
            log_path = self.session_dir / "eeg_mock_log.json"
            payload = {
                "sensor": "MockEEGModule",
                "sampling_rate_hz": self.sampling_rate_hz,
                "start_timestamp": self.start_timestamp,
                "stop_timestamp": self.stop_timestamp,
                "duration_s": round(duration, 6),
                "simulated_samples_count": simulated_samples,
                "markers": [asdict(m) for m in self.markers],
            }
            log_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        print(
            f"[EEG MOCK][{ts:.6f}s] Zatrzymano nagrywanie EEG "
            f"(czas: {duration:.3f}s, symulowane próbki: {simulated_samples}, "
            f"markery: {len(self.markers)})."
        )

    def send_marker(self, event_name: str, timestamp: float | None = None) -> None:
        ts = timestamp if timestamp is not None else time.perf_counter()
        marker = SensorMarker(event_name=event_name, timestamp=ts)
        self.markers.append(marker)
        print(f"[EEG MOCK][{ts:.6f}s] Marker: {event_name}")


class MockEyetrackerModule(EyetrackerModule):
    """Zaślepka (mock) modułu Eyetrackera symulująca rejestrację fiksacji i markerów."""

    def __init__(self, sampling_rate_hz: int = 120) -> None:
        self.sampling_rate_hz: int = sampling_rate_hz
        self.is_connected: bool = False
        self.is_recording: bool = False
        self.session_dir: Path | None = None
        self.start_timestamp: float | None = None
        self.stop_timestamp: float | None = None
        self.markers: list[SensorMarker] = []

    def connect(self) -> bool:
        ts = time.perf_counter()
        self.is_connected = True
        print(
            f"[EYETRACKER MOCK][{ts:.6f}s] Połączono z symulatorem Eyetrackera "
            f"({self.sampling_rate_hz} Hz)."
        )
        return True

    def start_recording(self, session_dir: Path | str) -> None:
        if not self.is_connected:
            self.connect()
        ts = time.perf_counter()
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.is_recording = True
        self.start_timestamp = ts
        self.stop_timestamp = None
        self.markers.clear()
        print(
            f"[EYETRACKER MOCK][{ts:.6f}s] Rozpoczęto nagrywanie Eyetrackera w katalogu: "
            f"{self.session_dir}"
        )

    def stop_recording(self) -> None:
        ts = time.perf_counter()
        if not self.is_recording:
            print(f"[EYETRACKER MOCK][{ts:.6f}s] Nagrywanie Eyetrackera było już zatrzymane.")
            return

        self.is_recording = False
        self.stop_timestamp = ts
        duration = (ts - self.start_timestamp) if self.start_timestamp is not None else 0.0
        simulated_gaze_points = int(duration * self.sampling_rate_hz)

        if self.session_dir is not None:
            log_path = self.session_dir / "eyetracker_mock_log.json"
            payload = {
                "sensor": "MockEyetrackerModule",
                "sampling_rate_hz": self.sampling_rate_hz,
                "start_timestamp": self.start_timestamp,
                "stop_timestamp": self.stop_timestamp,
                "duration_s": round(duration, 6),
                "simulated_gaze_points_count": simulated_gaze_points,
                "markers": [asdict(m) for m in self.markers],
            }
            log_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        print(
            f"[EYETRACKER MOCK][{ts:.6f}s] Zatrzymano nagrywanie Eyetrackera "
            f"(czas: {duration:.3f}s, symulowane punkty: {simulated_gaze_points}, "
            f"markery: {len(self.markers)})."
        )

    def send_marker(self, event_name: str, timestamp: float | None = None) -> None:
        ts = timestamp if timestamp is not None else time.perf_counter()
        marker = SensorMarker(event_name=event_name, timestamp=ts)
        self.markers.append(marker)
        print(f"[EYETRACKER MOCK][{ts:.6f}s] Marker: {event_name}")
