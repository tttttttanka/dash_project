import itertools
from typing import List, Optional

import pandas as pd
import plotly.graph_objs as go
from dash import html, dcc, dash_table

from sluzhby.istoriya import load_history_df
from sluzhby.parametry import generate_slider_marks, generate_parameter_values


def _history_column_options(df: pd.DataFrame) -> List[dict]:
    # Варианты для осей графика (названия столбцов).
    if df.empty:
        return []
    return [{"label": c, "value": c} for c in df.columns]


def _figure_from_spec(df: pd.DataFrame, spec: dict) -> go.Figure:
    # График 2D или 3D по выбранным колонкам.
    mode = spec.get("mode", "2d")
    x = spec.get("x")
    y = spec.get("y")
    z = spec.get("z")
    if df.empty or not x or not y:
        fig = go.Figure()
        fig.update_layout(title="Нет данных", annotations=[dict(text="Загрузите расчёты в историю", showarrow=False)])
        return fig
    if mode == "3d":
        if not z or x not in df.columns or y not in df.columns or z not in df.columns:
            fig = go.Figure()
            fig.update_layout(title="3D", annotations=[dict(text="Выберите оси из списка столбцов", showarrow=False)])
            return fig
        fig = go.Figure(
            data=[
                go.Scatter3d(
                    x=df[x],
                    y=df[y],
                    z=df[z],
                    mode="markers",
                    marker=dict(size=8, color=df[z], colorscale="Viridis"),
                )
            ]
        )
        fig.update_layout(
            title=f"{z} от {x} и {y}",
            scene=dict(xaxis_title=x, yaxis_title=y, zaxis_title=z),
        )
        return fig
    if x not in df.columns or y not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="2D", annotations=[dict(text="Выберите оси из списка столбцов", showarrow=False)])
        return fig
    sorted_df = df.sort_values(x)
    fig = go.Figure(data=[go.Scatter(x=sorted_df[x], y=sorted_df[y], mode="markers+lines")])
    fig.update_layout(title=f"{y} от {x}", xaxis_title=x, yaxis_title=y)
    return fig


def build_plots_panel(base_dir: str, plot_specs: Optional[List[dict]]):
    # Блок с кнопками и графиками (2D / 3D).
    df = load_history_df(base_dir)
    options = _history_column_options(df)
    specs = plot_specs if plot_specs is not None else []
    if not specs:
        specs = []

    toolbar = html.Div(
        [
            html.Button("Добавить 2D график", id="add-plot-2d", n_clicks=0, className="btn btn-blue"),
            html.Button("Добавить 3D график", id="add-plot-3d", n_clicks=0, className="btn btn-orange"),
        ],
        className="button-row",
    )

    if df.empty:
        return html.Div(
            [
                toolbar,
                html.Div("Нет данных в истории — выполните расчёты или обновите историю.", className="empty-state"),
            ],
            className="plots-wrap",
        )

    if not options:
        return html.Div([toolbar, html.Div("Нет столбцов для осей.", className="empty-state")], className="plots-wrap")

    cards = []
    for i, spec in enumerate(specs):
        mode = spec.get("mode", "2d")
        xv, yv, zv = spec.get("x"), spec.get("y"), spec.get("z")
        if xv not in df.columns and options:
            xv = options[0]["value"]
        if yv not in df.columns and len(options) > 1:
            yv = options[1]["value"]
        elif yv not in df.columns:
            yv = options[0]["value"]
        if mode == "3d":
            if zv not in df.columns and len(options) > 2:
                zv = options[2]["value"]
            elif zv not in df.columns:
                zv = options[-1]["value"]
            ctrls = html.Div(
                [
                    html.Span("Ось X:", className="axis-label"),
                    dcc.Dropdown(id={"type": "plot-axis", "idx": i, "axis": "x"}, options=options, value=xv, clearable=False, className="plot-dropdown"),
                    html.Span("Ось Y:", className="axis-label"),
                    dcc.Dropdown(id={"type": "plot-axis", "idx": i, "axis": "y"}, options=options, value=yv, clearable=False, className="plot-dropdown"),
                    html.Span("Ось Z:", className="axis-label"),
                    dcc.Dropdown(id={"type": "plot-axis", "idx": i, "axis": "z"}, options=options, value=zv, clearable=False, className="plot-dropdown"),
                ],
                className="plot-controls",
            )
        else:
            zv = None
            ctrls = html.Div(
                [
                    html.Span("Ось X:", className="axis-label"),
                    dcc.Dropdown(id={"type": "plot-axis", "idx": i, "axis": "x"}, options=options, value=xv, clearable=False, className="plot-dropdown"),
                    html.Span("Ось Y:", className="axis-label"),
                    dcc.Dropdown(id={"type": "plot-axis", "idx": i, "axis": "y"}, options=options, value=yv, clearable=False, className="plot-dropdown"),
                ],
                className="plot-controls",
            )

        fig = _figure_from_spec(df, {**spec, "x": xv, "y": yv, "z": zv})
        label = "3D" if mode == "3d" else "2D"
        cards.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(f"График {label}", className="plot-card-title"),
                            html.Button("Удалить", id={"type": "remove-plot", "idx": i}, n_clicks=0, className="btn btn-small btn-outline"),
                        ],
                        className="plot-card-head",
                    ),
                    ctrls,
                    dcc.Graph(figure=fig, config={"displayModeBar": True}, className="plot-graph"),
                ],
                className="plot-card",
            )
        )

    body = cards if cards else [html.Div("Нет графиков — нажмите «Добавить 2D» или «Добавить 3D».", className="empty-state")]
    return html.Div([toolbar, html.Div(body, className="plot-cards")], className="plots-wrap")


def coerce_series_rows(rows: list | None) -> list:
    # Ячейки таблицы → числа, где получается.
    if not rows:
        return []
    keys = list(rows[0].keys())
    out = []
    for r in rows:
        row = {}
        for k in keys:
            v = r.get(k)
            if v is None or v == "":
                row[k] = 0.0
            else:
                try:
                    row[k] = float(v)
                except (TypeError, ValueError):
                    row[k] = v
        out.append(row)
    return out


def create_history_table(base_dir):
    # Таблица истории и кнопки «сохранить» / «обновить».
    df = load_history_df(base_dir)
    if df.empty:
        return html.Div("Нет данных", className="empty-state")

    # Колонки для DataTable.
    columns = [{"name": col, "id": col} for col in df.columns]
    return html.Div(
        [
            html.Div(
                [
                    html.Button("Сохранить результаты", id="import-results-btn", n_clicks=0, className="btn btn-blue"),
                    html.Button("Обновить историю", id="refresh-history-btn", n_clicks=0, className="btn btn-green"),
                    dcc.Download(id="download-dataframe-csv"),
                ],
                className="button-row",
            ),
            dash_table.DataTable(
                id="history-data-table",
                data=df.to_dict("records"),
                columns=columns,
                page_size=10,
                page_action="native",
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
            ),
        ]
    )


def format_log(log_text):
    # Текст лога → разметка с классами (ошибка, серия и т.д.).
    if not log_text:
        return "Лог пуст"

    html_lines = []
    for line in log_text.split("\n"):
        # Пропуск пустых строк.
        line = line.strip()
        if not line:
            continue
        if "ВСЕ РАСЧЕТЫ ЗАВЕРШЕНЫ" in line:
            html_lines.append(html.Div(line, className="log-success"))
        elif "Ошибка" in line:
            html_lines.append(html.Div(line, className="log-error"))
        elif line.startswith("Серия"):
            html_lines.append(html.Div(line, className="log-series"))
        else:
            html_lines.append(html.Div(line))

    return html.Div(html_lines)


def build_input_controls(config):
    # Слайдеры для переменных и строки для констант.
    constants = config.get("constants", {})
    params = config.get("parameters", {})
    controls = []

    for key, p in params.items():
        # Значения по умолчанию из конфига.
        min_val = p.get("min", 0)
        max_val = p.get("max", 100)
        default_val = float(p.get("default", (min_val + max_val) / 2))
        steps = p.get("steps", 2)
        unit = p.get("unit", "")
        name = p.get("name", key)
        # Слайдер: сначала обе точки в значении из файла.
        range_start = [default_val, default_val]

        controls.append(
            html.Div(
                [
                    html.Div(f"{name} ({key}) [{unit}]", className="param-title"),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span("Границы шкалы min / max", className="meta-label"),
                                    dcc.Input(
                                        id={"type": "param-bound-min", "key": key},
                                        type="number",
                                        value=min_val,
                                        step="any",
                                        className="steps-input bound-input",
                                    ),
                                    dcc.Input(
                                        id={"type": "param-bound-max", "key": key},
                                        type="number",
                                        value=max_val,
                                        step="any",
                                        className="steps-input bound-input",
                                    ),
                                ],
                                className="meta-row",
                            ),
                            html.Div(
                                [
                                    html.Label("Интервалов:", className="meta-label"),
                                    dcc.Input(
                                        id={"type": "param-steps-input", "key": key},
                                        type="number",
                                        min=0,
                                        max=100,
                                        step=1,
                                        value=steps,
                                        className="steps-input",
                                    ),
                                ],
                                className="meta-row",
                            ),
                        ],
                        className="meta-wrap",
                    ),
                    dcc.RangeSlider(
                        id={"type": "param-range", "key": key},
                        min=min_val,
                        max=max_val,
                        value=range_start,
                        # Много мелких шагов для удобного выбора диапазона.
                        step=(max_val - min_val) / 100 if max_val > min_val else 0.001,
                        marks=generate_slider_marks(min_val, max_val, steps),
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(id={"type": "param-preview", "key": key}, className="preview-box"),
                ],
                className="param-card",
            )
        )

    for key, c in constants.items():
        unit = c.get("unit", "")
        name = c.get("name", key)
        controls.append(
            html.Div(
                [
                    html.Div(f"{name} ({key}) [{unit}]: ", className="param-title"),
                    html.Div(str(c.get("value")), className="meta-value"),
                ],
                className="constant-card",
            )
        )

    return controls, len(params), len(constants)


def build_series_table(series_data):
    # Таблица серий: можно править и удалять строки.
    if not series_data:
        return html.Div("Нет строк — сгенерируйте серии».", className="empty-state")
    df = pd.DataFrame(series_data)
    return dash_table.DataTable(
        id="series-data-table",
        data=df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in df.columns],
        editable=True,
        row_deletable=True,
        page_size=15,
        page_action="native",
        sort_action="native",
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "center", "padding": "10px"},
        style_header={"backgroundColor": "#f0f0f0", "fontWeight": "bold"},
    )


def generate_series_data(range_values, steps_values, param_ids):
    # Все комбинации значений параметров (сетка по каждому).
    param_values_dict = {}
    for range_val, steps, id_dict in zip(range_values, steps_values, param_ids):
        if range_val is None or len(range_val) < 2 or steps is None:
            continue
        min_val, max_val = range_val[0], range_val[1]
        if min_val > max_val:
            continue
        param_key = id_dict.get("key")
        # Ползунки в одной точке — одно число.
        if abs(float(min_val) - float(max_val)) < 1e-15:
            param_values_dict[param_key] = [float(min_val)]
            continue
        st = int(steps) if steps is not None else 1
        if st < 1:
            st = 1
        param_values_dict[param_key] = generate_parameter_values(min_val, max_val, st)

    if not param_values_dict:
        return []

    param_names = list(param_values_dict.keys())
    param_values = list(param_values_dict.values())
    # Все пары/тройки/… из сеток параметров.
    combinations = list(itertools.product(*param_values))
    return [dict(zip(param_names, combo)) for combo in combinations]
