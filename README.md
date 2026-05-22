# Budget App (WIP)

(README.md and buildozer.spec are WIP)

A mobile-friendly personal finance tracker built with **Python** and the **Kivy Framework**. This application allows users to manage their daily expenses, categorize transactions, and track their total spending through a clean, responsive interface designed for Android.

## Features

- **Transaction Management**: Easily add, edit, and delete transactions.
- **Categorization**: Group expenses into categories such as Food, Bills, Entertainment, Rent, Savings, and more.
- **Real-time Statistics**: View "Total Spent" and "Total Transactions" at a glance.
- **Persistent Storage**: All data is saved locally in `transactions.json`, ensuring your records remain available between sessions.
- **Mobile-First Design**: Optimized for a 360x800 resolution, perfect for modern smartphones.
- **Smooth Navigation**: Uses Kivy's `RecycleView` for efficient handling of long transaction histories.

## Tech Stack

- **Language**: Python 3
- **GUI Framework**: [Kivy](https://kivy.org/)
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

## Docker (WIP)

(WIP)

## Building for Android

This project is configured for **Buildozer**. To generate an APK:

1. Ensure you have the necessary dependencies for Buildozer installed on your system (Linux/macOS recommended).
2. Run the build command:
   ```bash
   buildozer -v android debug
   ```
3. The resulting APK will be located in the `bin/` directory.

The `buildozer.spec` file is already configured with the required permissions and requirements (`python3`, `kivy`, `android`, etc.).

## Project Structure

- `main.py`: The entry point and core logic of the application.
- `transactions.json`: Local storage for your transactions (REWORKING).
- `buildozer.spec`: Configuration for Android deployment (DEBUGGING).
- `assets/icon.png`: Application icon (WIP).
- `README.md`: Project documentation.

## Fonts

This project uses the **Noverich** font (previously **Ovelion**), both personal-use-only demo fonts by [Syauqi Studio](https://www.myfonts.com/collections/syauqi-studio-foundry). Due to their licenses, the font files are not included in this repository.

To restore custom typography when building locally, obtain the font and place it at:
```
assets/fonts/noverich/ttf/Noverich-KVRol.ttf
```
Alternatively, swap in any TTF font of your choice and update the path in `main.py`.

## License

[MIT](LICENSE)
