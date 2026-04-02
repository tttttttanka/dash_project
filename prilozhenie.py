import os

from dash import Dash
from interfejs.maket import build_layout
from kolbeki.registrator import register_callbacks

# Папка проекта и каталог runs для расчётов.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(PROJECT_DIR, "runs")
os.makedirs(BASE_DIR, exist_ok=True)

# Приложение Dash.
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    assets_folder=os.path.join(PROJECT_DIR, "assets"),
)
app.title = "Расчёт"

# Страница и колбэки.
app.layout = build_layout(BASE_DIR)
register_callbacks(app, BASE_DIR)

# Локальный запуск: python prilozhenie.py
if __name__ == "__main__":
    app.run(debug=True)