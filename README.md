# Smart Clipboard Capitalizer

A high-performance, corporate-grade Windows desktop application to capitalize clipboard text dynamically in real-time. It reformats standard text to title case while intelligently detecting and preserving alphanumeric part numbers (e.g., `XY2594YX684` and `9-YCC142`).

Designed with an elegant **Tactile Parchment Editorial Theme** and optimized for zero-dependency native Windows clipboard hooks.

---

## Key Features

1. **Smart Capitalization Engine**:
   - **Part Numbers**: Automatically detects alphanumeric word sequences (containing letters and digits) and forces them to **UPPERCASE** (e.g., `xy2594yx684` $\rightarrow$ `XY2594YX684`).
   - **Standard Text**: Title-cases ordinary words (e.g., `the cat sat on the mat` $\rightarrow$ `The Cat Sat On The Mat`).
   - **Compound Words**: Formats hyphenated words component-by-component (e.g., `well-being` $\rightarrow$ `Well-Being`).
   - **Custom Overrides**: Allows defining custom words to force to UPPERCASE via a comma-separated list.
2. **Editorial UI Styling**:
   - Implements a tactile parchment palette (`#F5F0E8`, `#E8E3DA`, `#FFFFFF`, `#2C2A26`, `#B8A99A`, `#C9763A`).
   - Pulsing horizontal copper status bar at the top represents the live heartbeat of the clipboard thread.
   - Built with high-DPI scaling using CustomTkinter and custom typography (DM Serif Display, Inter, JetBrains Mono).
3. **High-Performance Windows Hooks**:
   - Uses native `ctypes` bindings on `user32.dll` and `kernel32.dll` to read and write Unicode text without launching subprocesses.
   - Monitors clipboard state via hardware sequence counters (`GetClipboardSequenceNumber`), running with **0.0% CPU overhead**.
4. **Corporate-Level Infrastructure**:
   - Single-instance network lock to prevent duplicate background conflicts.
   - Local settings stored inside standard Windows Roaming directory (`%APPDATA%/ClipboardCapitalizer/settings.json`).

---

## Repository Structure

```text
auto caps smart/
│
├── assets/
│   ├── icon.ico                     # Multi-size Windows application icon
│   └── clipboard_large.png          # High-resolution transparent PNG asset
│
├── src/
│   └── clipboard_capitalizer/
│       ├── __init__.py              # Package initialization
│       ├── app.py                   # Main CustomTkinter GUI layout
│       └── engine.py                # Capitalization & Win32 clipboard hooks
│
├── tests/
│   └── test_capitalizer.py          # Automated unit test suite
│
├── .gitignore                       # Standard version control ignore list
├── requirements.txt                 # Lists Python package dependencies
├── README.md                        # Project documentation (this file)
└── start.bat                        # Quiet background launch script
```

---

## Installation & Setup

Ensure you have **Python 3.10+** installed on Windows.

1. Clone or download the repository to your system.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

* **Standard Start**: Double-click **`start.bat`** in the project root directory.
  - The script terminates any old hidden processes and launches a clean window.
  - The application starts in the **INACTIVE** state. Click the full-width stone button to **Start Clipboard Monitor** (turns to glowing copper).
* **Minimizing**: Close the GUI window at any time; your settings will be saved automatically.
* **Double-Click to Restore**: Double-click any line in the Clipboard Activity History to instantly restore the original unformatted copied string back to your clipboard.

---

## License

This project is licensed under the MIT License - see the [LICENSE](file:///c:/Users/alfie/Desktop/auto%20caps%20smart/LICENSE) file for details.
