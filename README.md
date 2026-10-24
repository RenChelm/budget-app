# Budget App (WIP)

A mobile-friendly personal finance tracker built with **Python** and the **Kivy Framework**. Manage daily expenses, categorize transactions, and track total spending through a clean interface designed for Android.

## Features

- **Transaction Management**: Add transactions to the week you're viewing, including past weeks you missed, and tap any transaction to edit or delete it. Amount fields open the number pad on Android.
- **Transaction Dates**: Pick the date a transaction happened with Android's date picker, or leave it blank to use the current time. Dates can be changed when editing.
- **Weekly Transactions View**: The main page shows the current week's transactions. Swipe sideways (or tap the arrows) to move between the 4 weeks of the current budget period.
- **Custom Categories**: Group expenses by creating custom persistent categories with several color options.
- **Custom Notes**: Further specify transactions by adding transaction specific notes.
- **Sorting**: Sort transactions by date or amount, in ascending or descending order.
- **Weekly Budgeting**: Set a weekly spending max and the day of the month your budget starts (e.g. the 15th to line up with a bill). Each monthly budget period is split into 4 weeks, with the last week absorbing the leftover days. Changing the max only affects the current period onward, so past results stay as they were.
- **Budget History**: Swipe through current and past budget periods. Each week shows total spent, amount left or over, purchase count, and the category spent on most, with the row colored to match that category. Tap a week to see its transactions.
- **Real-time Statistics**: See how much you've spent, how much is left under your weekly max, and how many transactions you've made in the week being viewed.
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
- `budget_periods.py`: Self contained functions that handle budget period/week boundaries, weekly max history, and week summaries (no Kivy, so it's easy to test).
- `ui/add_transaction_popup.py`: Self contained class that handles transactions.
- `ui/back_screen.py`: Self contained base class for screens with a titled top bar and back button.
- `ui/budget_popup.py`: Self contained class that handles weekly max and budget start day settings.
- `ui/chevron_button.py`: Self contained class for the chevron icon button (back button and week arrows).
- `ui/category_edit_popup.py`: Self contained class that handles category edits.
- `ui/category_select_popup.py`: Self contained class that handles category selection.
- `ui/colors_utils.py`: Self contained function that handles luminance-based font color for categories to improve text visibility.
- `ui/edit_transaction_popup.py`: Self contained class that handles transaction editing.
- `ui/entry_row.py`: Self contained class that handles transaction entry rows (tap to edit).
- `ui/history_screen.py`: Self contained classes that handle the swipeable budget history screen and its period pages.
- `ui/menu_button.py`: Self contained class for the three-bar menu icon button (WIP).
- `ui/number_input.py`: Self contained class for numeric text inputs that open the number pad on Android.
- `ui/sort_controls.py`: Self contained classes that handle the transaction sorting menu and sort order toggle.
- `ui/week_carousel.py`: Self contained classes that handle the swipeable 4-week transaction lists.
- `ui/week_row.py`: Self contained class that handles week rows on the history screen.
- `ui/week_screen.py`: Self contained class for the screen that shows a week opened from history.
- `tests/`: `pytest` test suite covering `main.py` and `ui/`.
- `buildozer.spec`: Buildozer configuration for Android deployment.
- `p4a_recipes/cython/`: Local p4a recipe overriding Cython to 3.0.10 for NDK r25b compatibility.
- `assets/images/icon.png`: Application icon (WIP).
- `DEVELOPMENT.md`: Personal development reference documentation.
- `README.md`: Project documentation.

## License

Copyright (C) 2026 James (Ren) Hyde

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the [GNU General Public License](LICENSE) for more
details.
