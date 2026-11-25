from __future__ import annotations

import threading
from typing import Final

import numpy as np

try:
    import sounddevice as sd

    _HAS_SOUNDDEVICE: Final[bool] = True
except Exception:  # pragma: no cover
    sd = None  # type: ignore[assignment]
    _HAS_SOUNDDEVICE = False

try:
    import winsound

    _HAS_WINSOUND: Final[bool] = True
except Exception:  # pragma: no cover
    winsound = None  # type: ignore[assignment]
    _HAS_WINSOUND = False

from PyQt6.QtWidgets import QApplication


class BeepPlayer:
    """
    Generator sygnałów dźwiękowych (piknięć) wywoływanych programowo
    bez wykorzystania zewnętrznych plików `.wav`.
    """

    def __init__(self, sample_rate: int = 44100) -> None:
        self.sample_rate: int = sample_rate

    def _synthesize_tone(self, frequency_hz: float, duration_s: float) -> np.ndarray:
        """Generuje falę sinusoidalną z krótkim wygładzeniem obwiedni (fade-in / fade-out)."""
        num_samples = max(1, int(self.sample_rate * duration_s))
        t = np.linspace(0.0, duration_s, num_samples, endpoint=False, dtype=np.float32)
        wave = 0.35 * np.sin(2.0 * np.pi * frequency_hz * t)

        fade_samples = min(int(self.sample_rate * 0.01), num_samples // 4)
        if fade_samples > 0:
            fade_in = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
            fade_out = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)
            wave[:fade_samples] *= fade_in
            wave[-fade_samples:] *= fade_out

        return wave.astype(np.float32)

    def play_beep(self, frequency_hz: float = 880.0, duration_ms: int = 150) -> None:
        """
        Odtwarza krótkie piknięcie w sposób nieblokujący wątku interfejsu użytkownika.
        """
        duration_s = duration_ms / 1000.0

        if _HAS_SOUNDDEVICE and sd is not None:
            try:
                tone = self._synthesize_tone(frequency_hz=frequency_hz, duration_s=duration_s)
                sd.play(tone, samplerate=self.sample_rate, blocking=False)
                return
            except Exception:
                pass

        if _HAS_WINSOUND and winsound is not None:
            threading.Thread(
                target=self._winsound_beep,
                args=(int(frequency_hz), duration_ms),
                daemon=True,
            ).start()
            return

        QApplication.beep()

    @staticmethod
    def _winsound_beep(freq: int, duration_ms: int) -> None:
        try:
            if winsound is not None:
                winsound.Beep(max(37, min(32767, freq)), max(50, duration_ms))
        except Exception:
            pass
