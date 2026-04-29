from dash import html, dcc

from interfejs.komponenty import build_plots_panel, create_history_table, series_data_table


def build_layout(base_dir):
    # Разметка страницы: параметры, серии, лог, история, графики.
    return html.Div(
        className="app-shell",
        children=[
            html.H1("Расчёт параметров", className="page-title"),
            html.Div(
                [
                    dcc.Upload(
                        id="upload-parameters",
                        multiple=False,
                        className="upload-box",
                        children=html.Div(["Перетащите файл или ", html.A("выберите", className="upload-link")]),
                    ),
                    html.Div(id="uploaded-parameters-info", className="upload-info"),
                ],
                className="section-block",
            ),
            html.Div(id="input-parameters-container", className="section-block"),
            html.Div(
                [html.Button("Сгенерировать серии", id="generate-series-btn", n_clicks=0, className="btn btn-orange")],
                className="button-row center",
            ),
            html.H3("Сгенерированные серии", className="section-title"),
            html.Div("Сгенерировано серий: 0", id="generated-series-info", className="status-text"),
            html.Div(
                [
                    html.Button("Добавить строку", id="series-add-row", n_clicks=0, className="btn btn-blue"),
                    html.Button("Выбрать все", id="series-select-all", n_clicks=0, className="btn btn-blue"),
                    html.Button("Отменить выбор", id="series-clear-selection", n_clicks=0, className="btn btn-outline"),
                    html.Button("Удалить выбранные", id="series-delete-selected", n_clicks=0, className="btn btn-outline"),
                    html.Button("Удалить все серии", id="series-delete-all", n_clicks=0, className="btn btn-outline"),
                ],
                className="button-row",
            ),
            html.Div(series_data_table(), className="section-block"),
            html.Div(
                [html.Button("Запустить расчеты", id="run-btn", n_clicks=0, className="btn btn-green")],
                className="button-row center",
            ),
            html.H3("Лог вычислений", className="section-title"),
            html.Div("Лог появится здесь после запуска", id="log-container", className="log-box"),
            dcc.Store(id="current-run-id", data=None),
            dcc.Store(id="is-running", data=False),
            # Константы из файла — в каждую серию.
            dcc.Store(id="param-constants", data=None),
            dcc.Store(id="series-data", data=[]),
            dcc.Store(id="plot-specs", data=[]),
            dcc.Store(id="plots-scroll-sink", data=0),
            dcc.Interval(id="log-interval", interval=1000, disabled=True, n_intervals=0),
            # Периодически проверять папку runs (удаление вручную).
            dcc.Interval(id="history-sync-interval", interval=4000, n_intervals=0),
            dcc.Store(id="runs-signature", data=None),
            html.H3("История расчетов", className="section-title"),
            html.Div(id="table-container", children=create_history_table(base_dir), className="section-block"),
            html.H3("Графики результатов", className="section-title"),
            html.Div(id="plots-container", children=build_plots_panel(base_dir, [])),
        ],
    )
