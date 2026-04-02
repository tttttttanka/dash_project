from dash import html
from dash.dependencies import Input, Output, State, ALL

from sluzhby.raschety import run_calculations
from interfejs.komponenty import generate_series_data


def register_calculation_callbacks(app, base_dir):
    # Генерация серий и запуск расчёта.
    @app.callback(
        Output("series-data", "data"),
        Output("generated-series-info", "children"),
        Input("generate-series-btn", "n_clicks"),
        State({"type": "param-range", "key": ALL}, "value"),
        State({"type": "param-steps-input", "key": ALL}, "value"),
        State({"type": "param-range", "key": ALL}, "id"),
        State("param-constants", "data"),
        prevent_initial_call=True,
    )
    def generate_series(n_clicks, range_values, steps_values, param_ids, constants_data):
        # Список серий из сеток параметров + константы.
        if not param_ids or not range_values:
            return [], "Нет параметров"

        series_data = generate_series_data(range_values, steps_values, param_ids)
        if not series_data:
            return [], "Ошибка генерации"

        # Сначала константы, потом строка серии (имена могут перекрыться).
        const = constants_data if isinstance(constants_data, dict) else {}
        series_data = [{**const, **row} for row in series_data]

        info = f"Сгенерировано серий: {len(series_data)}"
        return series_data, info

    # Кнопка «Запустить расчёты».
    @app.callback(
        Output("current-run-id", "data"),
        Output("is-running", "data"),
        Output("log-interval", "disabled"),
        Input("run-btn", "n_clicks"),
        State("series-data", "data"),
        prevent_initial_call=True,
    )
    def run_calculations_callback(n_clicks, series_data):
        # Запуск в фоне; в Store — имена папок серий.
        if not series_data:
            return None, False, True

        folder = run_calculations(series_data, base_dir)
        if not folder:
            return None, False, True
        return folder, True, False
