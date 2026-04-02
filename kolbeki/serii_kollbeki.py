from dash import Input, Output, State, no_update

from interfejs.komponenty import build_series_table, coerce_series_rows


def register_series_table_callbacks(app):
    # Таблица серий и синхронизация с Store.
    @app.callback(
        Output("series-table-container", "children"),
        Input("series-data", "data"),
    )
    def render_series_table(series_data):
        # Показать таблицу по данным из Store.
        return build_series_table(series_data or [])

    @app.callback(
        Output("series-data", "data", allow_duplicate=True),
        Input("series-data-table", "data"),
        State("series-data", "data"),
        prevent_initial_call=True,
    )
    def sync_series_store_from_table(table_data, _prev):
        # Записать правки из таблицы в Store.
        if table_data is None:
            return no_update
        return coerce_series_rows(table_data)

    @app.callback(
        Output("series-data", "data", allow_duplicate=True),
        Input("series-add-row", "n_clicks"),
        State("series-data", "data"),
        State("param-constants", "data"),
        prevent_initial_call=True,
    )
    def add_series_row(_n, data, constants_data):
        # Добавить строку по образцу последней или констант.
        const = constants_data if isinstance(constants_data, dict) else {}
        if data and len(data) > 0:
            template = {k: float(v) for k, v in data[-1].items()}
        elif const:
            template = {k: float(v) for k, v in const.items()}
        else:
            template = {"m": 1.0, "g": 9.81, "h": 1.0, "V": 1.0, "T": 20.0, "C": 4200.0}
        return (data or []) + [template]
