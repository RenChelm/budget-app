# Budget App (WIP)

A mobile-friendly personal finance tracker built with **Python** and the **Kivy Framework**. Manage daily expenses, categorize transactions, and track total spending through a clean interface designed for Android.

## Features

- **Transaction Management**: Add transactions to the week you're viewing, including past weeks you missed, and tap any transaction to edit or delete it. Amount fields open the number pad on Android.
- **Transaction Dates**: Pick the date a transaction happened with Android's date picker, or leave it blank to use the current time. Dates can be changed when editing.
- **Weekly Transactions View**: The main page shows the current week's transactions. Swipe sideways (or tap the arrows) to move between the weeks of the current budget period.
- **Custom Categories**: Group expenses by creating custom persistent categories with several color options. Custom Color opens a color wheel with a brightness slider for any other color, and colors saved from it stay beneath the defaults for every category to use. A search bar at the top of the list finds a category, and New Category at the bottom adds one, starting with whatever was typed in the search.
- **Custom Menu**: The Custom button on the main page opens a menu of Categories, Retailers/Platforms and Brands/Creators, each opening its list to add to, rename or remove from.
- **Custom Notes**: Further specify transactions by adding transaction specific notes.
- **Retailers/Platforms and Brands/Creators**: Tap Advanced at the bottom of the add or edit popup to optionally pick where a purchase was made (e.g. Walmart or Steam) and its brand or creator (e.g. Lay's). Each has its own list that works like the category list: a search bar at the top finds a saved name, and a New button at the bottom adds one, starting with whatever was typed in the search. Adding or editing a name uses the same popup as a category, so it can be given a color (optional) from the defaults, saved colors or Custom Color. A name's color fills its button in the list and its button under Advanced once picked. There are no built-in names. Names can be renamed (which updates past transactions), recolored (which shows everywhere at once) or removed from the list (past transactions keep them). The lists can also be managed from Custom on the main page, where adding a name keeps the list open for more and tapping a name renames it. Editing a transaction that has a retailer/platform or brand/creator opens with Advanced already showing.
- **Sorting**: Sort transactions by date or amount, in ascending or descending order.
- **Weekly Budgeting**: Set a weekly spending max and pick a budget period:
  - **Monthly**: Your budget starts on a day of the month (e.g. the 15th to line up with a bill). Each period is split into 4 weeks, with the last week absorbing the leftover days. That longer last week can have its own, bigger max.
  - **Weekly**: Every week is exactly 7 days, starting on the weekday you pick. Weeks are grouped by the month they start in, so a month has 4 or 5 weeks.
  - Changing the max only affects the current period onward, so past results stay as they were.
- **Leftovers and Overspending**: When a week (weekly budgeting) or month (monthly budgeting) ends under budget, the app offers to add what you didn't spend to the next one. If it ends over budget, it offers to subtract the overspend from the next one instead. A month's amount is split evenly over the next month's weeks. With weekly budgeting, adding or subtracting never changes a month's total at the top of Spending History, since the amount already counts in the week it came from. With monthly budgeting, adding last month's leftover (or subtracting its overspend) does change this month's total, and a line under the total says so. You're asked once, and you can change your answer later from Spending History. These amounts update if you add a missed transaction to a finished week. Each budget period mode remembers its own answers, so switching modes and back brings them back.
- **Spending History**: Swipe through current and past budget periods. Each week shows total spent, amount left or over, purchase count, and the category spent on most, with the row colored to match that category. A week or month that ended over or under budget has a button to add its leftover to (or subtract its overspend from) the next one, such as "Add to next week", which reads "Added to next week" once it's on. Tap a week to see its transactions. Below the weeks, circle graphs break the period's spending down by category, by retailer/platform and by brand/creator, each with a legend listing every slice's amount and share. Past six slices, the smallest are grouped into "Other". The retailer/platform and brand/creator graphs only count transactions that have one and note how much didn't. Each slice takes its retailer's or brand's color; ones without a color are colored biggest first, so their colors can change from one period to the next. The page scrolls when it doesn't all fit on the screen.
- **Real-time Statistics**: See how much you've spent, how much is left under your weekly max (including anything added or subtracted from the week before), and how many transactions you've made in the week being viewed.
- **Persistent Storage**: Data is saved locally to the device using Kivy's `user_data_dir`, ensuring records persist between sessions.
- **Density-Independent Layout**: UI scales correctly across screen sizes and densities using Kivy's `dp()`/`sp()` units.
- **Edge-to-Edge Display**: On Android 11 and newer, the app's colors run behind the status bar, camera and gesture bar, while its buttons and text stay clear of them. The gesture handle sits on a thin light gray bar, like the dividers, across the bottom.
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
2. Install Cython 0.29.37 for the system Python, which p4a uses to generate C code for pyjnius and Kivy. Ubuntu's own `cython3` package is too old for the app's Python 3.11:
   ```bash
   python3 -m pip install --user Cython==0.29.37
   ```
3. Run:
   ```bash
   buildozer android debug
   ```
4. The resulting APK will be located in the `bin/` directory.

Key build configuration:
- **Target API**: 34
- **Min API**: 21
- **NDK**: r25b
- **python-for-android**: v2024.01.21 (Python 3.11)
- **Kivy**: 2.3.1
- **Cython**: 3.0.10 (via local recipe in `p4a_recipes/` to fix clang-14 compatibility)

## Project Structure

- `main.py`: Entry point and core application logic.
- `budget_periods.py`: Self contained functions that handle budget period/week boundaries, weekly max history, and week summaries (no Kivy, so it's easy to test).
- `android_src/org/ren/budgetapp/BackSwipeFilter.java`: Java class (added to the build with `android.add_src`) that keeps Android's edge back swipe from also counting as a tap on whatever it starts on.
- `ui/add_transaction_popup.py`: Self contained class that handles transactions.
- `ui/advanced_section.py`: Self contained classes for the Advanced section of the add and edit popups, which slides open to show the optional retailer and brand.
- `ui/back_screen.py`: Self contained base class for screens with a titled top bar and back button.
- `ui/back_swipe.py`: Self contained function that turns on `BackSwipeFilter` on Android.
- `ui/budget_popup.py`: Self contained class that handles the budget period type, weekly max, long week max, and budget start day/weekday settings.
- `ui/carry_over_button.py`: Self contained class for the Add/Subtract pill button on the history screen that moves a week's or month's leftover or overspend onto the next one.
- `ui/carry_over_popup.py`: Self contained class for the popup that offers to add what was left (or subtract what was overspent) in the week or month that just ended.
- `ui/chevron_button.py`: Self contained class for the chevron icon button (back button and week arrows).
- `ui/choice_row.py`: Self contained class for a row of buttons where exactly one option is selected (budget period type and week start day).
- `ui/category_edit_popup.py`: Self contained class for adding or editing a category, retailer or brand: its name, the color choices and the colors saved from the color wheel.
- `ui/category_select_popup.py`: Self contained class that handles category selection, with a search bar to filter the list.
- `ui/color_utils.py`: Self contained function that handles luminance-based font color for categories to improve text visibility, plus the shared green Save/Add button color.
- `ui/color_wheel_popup.py`: Self contained classes for the Custom Color popup: a color wheel (hue around it, saturation out from the center), a brightness slider and a preview of the picked color.
- `ui/custom_popup.py`: Self contained class for the Custom menu on the main page, which opens the category, retailer or brand list.
- `ui/edge_to_edge.py`: Self contained function that lets the app draw behind Android's status bar, camera and gesture bar (Android 11+), plus the strips that keep the screens clear of them and the safe area that tracks how big those bars are.
- `ui/edit_transaction_popup.py`: Self contained class that handles transaction editing.
- `ui/entry_row.py`: Self contained class that handles transaction entry rows (tap to edit).
- `ui/expanding_popup.py`: Self contained base class for popups that fit their content and grow downward (top edge stays put) when a section opens.
- `ui/history_screen.py`: Self contained classes that handle the swipeable budget history screen and its period pages. Pages are built as they come into view and kept between visits, so only periods whose numbers changed are rebuilt.
- `ui/menu_button.py`: Self contained class for the three-bar menu icon button (WIP).
- `ui/name_select_popup.py`: Self contained class for the searchable retailer and brand lists (pick, add, rename, remove; opened from Custom it only manages the list), plus the functions that keep those lists (names with optional colors) sorted and matched ignoring case, and the search bar shared with the category list.
- `ui/number_input.py`: Self contained class for numeric text inputs that open the number pad on Android.
- `ui/page_carousel.py`: Self contained class for swipeable pages, so the main page, history and week screens all share the same swipe settings. A quick flick turns the page even when it's short, and the page finishes sliding at the speed it was flicked.
- `ui/rounded_button.py`: Self contained class for buttons with rounded corners (rounded as much as the entry rows) that darken while pressed, used for the four buttons at the bottom of the main page.
- `ui/sort_controls.py`: Self contained classes that handle the transaction sorting menu and sort order toggle.
- `ui/spending_chart.py`: Self contained classes for the history screen's circle graphs (spending by category, retailer and brand) and their legends.
- `ui/week_carousel.py`: Self contained classes that handle the swipeable weekly transaction lists of a budget period.
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
