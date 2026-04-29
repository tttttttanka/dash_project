from dash import Input, Output, State, no_update

from interfejs.komponenty import coerce_series_rows, series_table_columns_and_data


def register_series_table_callbacks(app):
    # Таблица серий, выбор строк, массовое удаление.
    @app.callback(
        Output("series-data-table", "columns"),
        Output("series-data-table", "data"),
        Input("series-data", "data"),
    )
    def sync_table_from_store(series_data):
        cols, rows = series_table_columns_and_data(series_data)
        return cols, rows

    @app.callback(
        Output("generated-series-info", "children", allow_duplicate=True),
        Input("series-data", "data"),
        prevent_initial_call=True,
    )
    def sync_generated_count(series_data):
        return f"Сгенерировано серий: {len(series_data or [])}"

    @app.callback(
        Output("series-data", "data", allow_duplicate=True),
        Input("series-data-table", "data"),
        State("series-data", "data"),
        prevent_initial_call=True,
    )
    def sync_series_store_from_table(table_data, prev_store):
        if table_data is None:
            return no_update
        coerced = coerce_series_rows(table_data)
        if prev_store is not None and coerced == coerce_series_rows(list(prev_store)):
            return no_update
        return coerced

    @app.callback(
        Output("series-data", "data", allow_duplicate=True),
        Input("series-add-row", "n_clicks"),
        State("series-data", "data"),
        State("param-constants", "data"),
        prevent_initial_call=True,
    )
    def add_series_row(_n, data, constants_data):
        const = constants_data if isinstance(constants_data, dict) else {}
        if data and len(data) > 0:
            template = {k: float(v) for k, v in data[-1].items()}
        elif const:
            template = {k: float(v) for k, v in const.items()}
        else:
            template = {"m": 1.0, "g": 9.81, "h": 1.0, "V": 1.0, "T": 20.0, "C": 4200.0}
        return (data or []) + [template]

    @app.callback(
        Output("series-data-table", "selected_rows", allow_duplicate=True),
        Input("series-select-all", "n_clicks"),
        State("series-data", "data"),
        prevent_initial_call=True,
    )
    def select_all_series(_n, data):
        if not data:
            return []
        return list(range(len(data)))

    @app.callback(
        Output("series-data-table", "selected_rows", allow_duplicate=True),
        Input("series-clear-selection", "n_clicks"),
        prevent_initial_call=True,
    )
    def clear_series_selection(_n):
        return []

    @app.callback(
        Output("series-data", "data", allow_duplicate=True),
        Output("series-data-table", "selected_rows", allow_duplicate=True),
        Input("series-delete-selected", "n_clicks"),
        State("series-data-table", "selected_rows"),
        State("series-data", "data"),
        prevent_initial_call=True,
    )
    def delete_selected_series(_n, selected_rows, data):
        if not data or not selected_rows:
            return no_update, no_update
        drop = set(int(i) for i in selected_rows)
        new_data = [row for idx, row in enumerate(data) if idx not in drop]
        return new_data, []

    @app.callback(
        Output("series-data", "data", allow_duplicate=True),
        Output("series-data-table", "selected_rows", allow_duplicate=True),
        Input("series-delete-all", "n_clicks"),
        prevent_initial_call=True,
    )
    def delete_all_series(_n):
        return [], []
