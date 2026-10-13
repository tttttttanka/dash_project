import os

from dash import Dash
from frontend.callbacks.registrator import register_callbacks
from frontend.maket import build_layout

# Папка проекта и каталог runs для расчётов.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(PROJECT_DIR, "runs")
os.makedirs(BASE_DIR, exist_ok=True)

# Приложение Dash.
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    assets_folder=os.path.join(PROJECT_DIR, "frontend", "assets"),
)
app.title = "Расчёт"

# Страница и колбэки.
app.layout = build_layout(BASE_DIR)
register_callbacks(app, BASE_DIR)

if __name__ == "__main__":
    app.run(debug=True)