import json

from dash import Input, Output, State, callback_context, no_update
from dash.dependencies import ALL

from interfejs.komponenty import build_plots_panel
from sluzhby.istoriya import load_history_df


def register_plot_callbacks(app, base_dir):
    # Графики: список, оси, добавление/удаление.
    @app.callback(
        Output("plots-container", "children"),
        Input("plot-specs", "data"),
        Input("runs-signature", "data"),
        Input("is-running", "data"),
        Input("refresh-history-btn", "n_clicks"),
    )
    def render_plots_panel(plot_specs, _sig, _running, _refresh):
        # Перерисовать панель (настройки, история, кнопка).
        specs = plot_specs if plot_specs is not None else []
        return build_plots_panel(base_dir, specs)

    @app.callback(
        Output("plot-specs", "data", allow_duplicate=True),
        Input("add-plot-2d", "n_clicks"),
        Input("add-plot-3d", "n_clicks"),
        State("plot-specs", "data"),
        prevent_initial_call=True,
    )
    def add_plot_panel(n2d, n3d, specs):
        # Новый график 2D или 3D с осями по умолчанию.
        if not callback_context.triggered:
            return no_update
        trig = callback_context.triggered[0]["prop_id"].split(".")[0]
        # После перерисовки панели кнопки создаются заново, n_clicks снова 0 — это не клик.
        t0 = callback_context.triggered[0]
        click_val = t0.get("value")
        if trig == "add-plot-2d":
            if not (click_val if click_val is not None else n2d):
                return no_update
        elif trig == "add-plot-3d":
            if not (click_val if click_val is not None else n3d):
                return no_update
        else:
            return no_update
        df = load_history_df(base_dir)
        cols = list(df.columns) if not df.empty else ["m", "g", "h", "V", "T", "C", "E_total", "E_kin", "Q"]
        cur = list(specs) if specs else []
        if trig == "add-plot-2d":
            cur.append(
                {
                    "mode": "2d",
                    "x": cols[0],
                    "y": cols[min(1, len(cols) - 1)],
                    "z": None,
                }
            )
        elif trig == "add-plot-3d":
            cur.append(
                {
                    "mode": "3d",
                    "x": cols[0],
                    "y": cols[min(1, len(cols) - 1)],
                    "z": cols[min(2, len(cols) - 1)],
                }
            )
        else:
            return no_update
        return cur

    @app.callback(
        Output("plot-specs", "data", allow_duplicate=True),
        Input({"type": "remove-plot", "idx": ALL}, "n_clicks"),
        State("plot-specs", "data"),
        prevent_initial_call=True,
    )
    def remove_plot_panel(_clicks, specs):
        # Удалить график по кнопке.
        if not specs or not callback_context.triggered:
            return no_update
        prop = callback_context.triggered[0]["prop_id"]
        if "remove-plot" not in prop:
            return no_update
        t0 = callback_context.triggered[0]
        if not t0.get("value"):
            return no_update
        id_json = prop.split(".")[0]
        btn_id = json.loads(id_json)
        idx = btn_id["idx"]
        new_specs = [s for i, s in enumerate(specs) if i != idx]
        return new_specs

    @app.callback(
        Output("plot-specs", "data", allow_duplicate=True),
        Input({"type": "plot-axis", "idx": ALL, "axis": ALL}, "value"),
        State({"type": "plot-axis", "idx": ALL, "axis": ALL}, "id"),
        State("plot-specs", "data"),
        prevent_initial_call=True,
    )
    def update_plot_axes(values, axis_ids, specs):
        # Записать выбранные оси в Store.
        if not specs or not axis_ids:
            return no_update
        by_idx = {}
        for v, aid in zip(values or [], axis_ids or []):
            i = aid["idx"]
            axis = aid["axis"]
            if i not in by_idx:
                by_idx[i] = {}
            if v is not None:
                by_idx[i][axis] = v
        new_specs = []
        for i, s in enumerate(specs):
            d = dict(s)
            if i in by_idx:
                upd = by_idx[i]
                if d.get("mode") == "3d":
                    if "x" in upd:
                        d["x"] = upd["x"]
                    if "y" in upd:
                        d["y"] = upd["y"]
                    if "z" in upd:
                        d["z"] = upd["z"]
                else:
                    if "x" in upd:
                        d["x"] = upd["x"]
                    if "y" in upd:
                        d["y"] = upd["y"]
            new_specs.append(d)
        return new_specs
