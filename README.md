# Budget App (WIP)

A mobile-friendly personal finance tracker built with **Python** and the **Kivy Framework**. Manage daily expenses, categorize transactions, and track total spending through a clean interface designed for Android.

## Features

- **Transaction Management**: Add, edit, and delete transactions.
- **Custom Categories**: Group expenses by creating custom persistent categories with several color options.
- **Custom Notes**: Further specify transactions by adding transaction specific notes.
- **Real-time Statistics**: View "Total Spent" and "Total Transactions" at a glance.
- **Persistent Storage**: Data is saved locally to the device using Kivy's `user_data_dir`, ensuring records persist between sessions.
- **Density-Independent Layout**: UI scales correctly across screen sizes and densities using Kivy's `dp()`/`sp()` units.
- **Smooth Navigation**: Uses Kivy's `RecycleView` for efficient handling of long transaction histories.
- **Dynamic Font Coloring**: Automatically applies contrasting font colors to categories depending on background luminance, improving text visibility.

## Tech Stack

- **Language**: Python 3
- **GUI Framework**: [Kivy 2.3.1](https://kivy.org/)
- **Deployment**: [Buildozer](https://github.com/kivy/buildozer) (for Android APK generation)
- **Data Format**: JSON

## Installation

### Prerequisites

Ensure you have Python 3.8+ installed. It is recommended to use a virtual environment.

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd budget-app
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv kivyenv
   source kivyenv/bin/activate  # On Windows: kivyenv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install kivy==2.3.1
   ```

## Usage

To run the application locally on your desktop:

```bash
python3 main.py
```

The app will open in a window sized to simulate a mobile screen (360x800).

## Running Tests

The test suite uses `pytest` and drives real Kivy widgets (touch simulation, widget construction), so it needs a display/GL context available (works out of the box on desktop Linux, macOS, Windows, and WSLg).

```bash
pip install pytest
pytest
```

## Building for Android

This project is configured for **Buildozer** with a custom local p4a recipe to ensure compatibility with NDK r25b. To generate an APK:

1. Ensure Buildozer and its system dependencies are installed (Linux or WSL recommended).
2. Run:
   ```bash
   buildozer android debug
   ```
3. The resulting APK will be located in the `bin/` directory.

Key build configuration:
- **Target API**: 34
- **Min API**: 21
- **NDK**: r25b
- **Kivy**: 2.3.1
- **Cython**: 3.0.10 (via local recipe in `p4a_recipes/` to fix clang-14 compatibility)

## Project Structure

- `main.py`: Entry point and core application logic.
- `ui/add_transaction_popup.py`: Self contained class that handles transactions.
- `ui/category_edit_popup.py`: Self contained class that handles category edits.
- `ui/category_select_popup.py`: Self contained class that handles category selection.
- `ui/colors_utils.py`: Self contained function that handles luminance-based font color for categories to improve text visibility.
- `ui/edit_transaction_popup.py`: Self contained class that handles transaction editing.
- `ui/entry_row.py`: Self contained class that handles transaction entry rows.
- `tests/`: `pytest` test suite covering `main.py` and `ui/`.
- `buildozer.spec`: Buildozer configuration for Android deployment.
- `p4a_recipes/cython/`: Local p4a recipe overriding Cython to 3.0.10 for NDK r25b compatibility.
- `assets/images/icon.png`: Application icon (WIP).
- `DEVELOPMENT.md`: Personal development reference documentation.
- `README.md`: Project documentation.

## License

[MIT](LICENSE)
