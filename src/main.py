from __future__ import annotations

import sys
from pathlib import Path

# Umożliwia uruchomienie zarówno przez `python -m src.main`, jak i `python src/main.py`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication

from src.aggregator import DataAggregator
from src.controller import SessionController
from src.generator import TextGenerator
from src.sensors.mocks import MockEEGModule, MockEyetrackerModule
from src.ui.main_window import MainWindow


def resolve_config_path(root: Path) -> Path:
    """Wyszukuje plik `config.json` w katalogu głównym projektu lub w `data/config.json`."""
    primary = root / "config.json"
    if primary.exists():
        return primary
    fallback = root / "data" / "config.json"
    if fallback.exists():
        return fallback
    return primary


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Aplikacja Badawcza NEAT")

    config_path = resolve_config_path(PROJECT_ROOT)
    texts_path = PROJECT_ROOT / "data" / "texts.json"
    output_dir = PROJECT_ROOT / "output"

    eeg_module = MockEEGModule()
    eyetracker_module = MockEyetrackerModule()
    text_generator = TextGenerator(texts_path=texts_path)
    data_aggregator = DataAggregator(output_base_dir=output_dir)

    controller = SessionController(
        config_path=config_path,
        eeg_module=eeg_module,
        eyetracker_module=eyetracker_module,
        text_generator=text_generator,
        data_aggregator=data_aggregator,
    )

    window = MainWindow(controller=controller)
    window.showFullScreen()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
