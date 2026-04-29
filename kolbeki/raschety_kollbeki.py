from dash.dependencies import Input, Output, State, ALL

from sluzhby.raschety import run_calculations
from interfejs.komponenty import generate_series_data


def register_calculation_callbacks(app, base_dir):
    # Генерация серий и запуск расчёта.
    @app.callback(
        Output("series-data", "data"),
        Input("generate-series-btn", "n_clicks"),
        State({"type": "param-range", "key": ALL}, "value"),
        State({"type": "param-steps-input", "key": ALL}, "value"),
        State({"type": "param-step-size-input", "key": ALL}, "value"),
        State({"type": "param-range", "key": ALL}, "id"),
        State("param-constants", "data"),
        prevent_initial_call=True,
    )
    def generate_series(_n_clicks, range_values, steps_values, step_size_values, param_ids, constants_data):
        # Список серий из сеток параметров + константы.
        if not param_ids or not range_values:
            return []

        series_data = generate_series_data(range_values, steps_values, param_ids, step_size_values)
        if not series_data:
            return []

        # Сначала константы, потом строка серии (имена могут перекрыться).
        const = constants_data if isinstance(constants_data, dict) else {}
        series_data = [{**const, **row} for row in series_data]

        return series_data

    # Кнопка «Запустить расчёты».
    @app.callback(
        Output("current-run-id", "data"),
        Output("is-running", "data"),
        Output("log-interval", "disabled"),
        Input("run-btn", "n_clicks"),
        State("series-data", "data"),
        State("series-data-table", "selected_rows"),
        prevent_initial_call=True,
    )
    def run_calculations_callback(_n_clicks, series_data, selected_rows):
        # Запуск в фоне; в Store — имена папок серий.
        if not series_data:
            return None, False, True

        if selected_rows:
            idx = sorted({int(i) for i in selected_rows if i is not None})
            to_run = [series_data[i] for i in idx if 0 <= i < len(series_data)]
        else:
            to_run = list(series_data)

        if not to_run:
            return None, False, True

        folder = run_calculations(to_run, base_dir)
        if not folder:
            return None, False, True
        return folder, True, False
