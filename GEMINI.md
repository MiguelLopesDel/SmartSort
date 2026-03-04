# 🤖 SmartSort - Project Context

SmartSort is an intelligent file automation and organization service for Linux. it monitors directories in real-time, extracts text from various file formats (PDFs, images via OCR, text files), classifies them using Artificial Intelligence (Zero-Shot or Local ML), and moves them to organized destination folders.

## 🏗️ Architecture Overview

The project is structured as a modular Python package:

- **`src/smartsort/core/engine.py`**: The heart of the system. Handles the `FileProcessor` which manages file classification logic, model loading, and file movement.
- **`src/smartsort/cli/`**:
    - `config.py`: Typer-based CLI for managing configurations and hardware acceleration.
    - `tui.py`: Interactive Rich-based Terminal User Interface for easy management.
- **`src/smartsort/utils/`**:
    - `logger.py`: Structured logging using Rich.
    - `power.py`: `PowerManager` to detect battery status and adjust AI intensity.
    - `recommender.py`: `HardwareRecommender` to suggest the best acceleration (CPU, OpenVINO, CUDA).
    - `cleaner.py`: Utility to remove comments from Python and Shell files (see Development Mandates).
- **`src/smartsort/__main__.py`**: Entry point for the background daemon using `watchdog`.

## 🛠️ Key Technologies

- **Monitoring**: `watchdog`
- **AI Classification**: `transformers` (mDeBERTa for Zero-Shot), `scikit-learn` (Local ML).
- **Text Extraction**: `pytesseract` (OCR), `pypdf`, `Pillow`.
- **Hardware Acceleration**: `optimum` (OpenVINO), `onnxruntime`.
- **UI/UX**: `typer`, `rich`.
- **System Integration**: `systemd` (via `deploy/smartsort.service`).

## 🚀 Commands & Development

### Building and Running
- **Installation**: `./scripts/install.sh` (Configures venv, dependencies, and systemd service).
- **Run TUI**: `smartsort` (or `python3 -m smartsort.cli.config tui`).
- **Run Daemon**: `python3 -m smartsort`.
- **CLI Wrapper**: `smartsort-cli.sh` resolves absolute paths and activates the virtual environment.

### Testing
- **Run all tests**: `pytest`
- **Smoke tests**: `pytest tests/test_smoke.py`
- **Hardware tests**: `pytest tests/test_hardware_logic.py`

### Development Conventions
- **Formatting**: `black` (120 char limit) and `isort` are enforced.
- **Paths**: ALWAYS use absolute paths relative to the project root for configuration, logs, and models to ensure the tool works from any working directory.
- **Logging**: Use the central `logger` from `smartsort.utils.logger`.

## ⚠️ Critical Development Mandates

1.  **NO COMMENTS**: According to global project rules, code comments must NOT be preserved.
2.  **CLEANER SCRIPT**: Always run `python3 -m smartsort.utils.cleaner <path>` before finalizing tasks or committing to ensure compliance with the "no comments" rule.
3.  **NO AUTO PUSH**: Never perform `git push` autonomously; always wait for explicit user request.
4.  **Surgical Updates**: Use absolute paths for all internal resources (config, data, models) resolved at runtime relative to the file's location.
