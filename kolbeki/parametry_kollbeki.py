import base64

from dash import html, no_update, callback_context
from dash.dependencies import Input, Output, State, ALL

from sluzhby.parametry import parse_parameters_file, generate_parameter_values, generate_slider_marks
from interfejs.komponenty import build_input_controls


def register_parameter_callbacks(app):
    # Загрузка файла параметров и слайдеры.
    @app.callback(
        Output("uploaded-parameters-info", "children"),
        Output("input-parameters-container", "children"),
        Output("param-constants", "data"),
        Input("upload-parameters", "contents"),
        State("upload-parameters", "filename"),
    )
    def load_parameters(contents, filename):
        # Файл с диска → контролы и константы.
        if contents is None:
            return "", html.Div("Загрузите файл параметров", className="empty-state"), None

        try:
            # Upload: base64 после запятой.
            content_str = contents.split(",")[1]
            decoded = base64.b64decode(content_str).decode("utf-8")
            current_config = parse_parameters_file(decoded)
            input_controls, params_count, constants_count = build_input_controls(current_config)
            info = f"Файл {filename} загружен. Переменных: {params_count}, констант: {constants_count}"
            constants_flat = {
                name: float(data["value"])
                for name, data in current_config.get("constants", {}).items()
            }
            return info, html.Div(input_controls), constants_flat
        except Exception as err:
            return f"Ошибка: {err}", html.Div("Не удалось загрузить файл параметров", className="text-error"), None

    # Поля min/max меняют шкалу слайдера.
    @app.callback(
        Output({"type": "param-range", "key": ALL}, "min"),
        Output({"type": "param-range", "key": ALL}, "max"),
        Output({"type": "param-range", "key": ALL}, "value"),
        Input({"type": "param-bound-min", "key": ALL}, "value"),
        Input({"type": "param-bound-max", "key": ALL}, "value"),
        State({"type": "param-range", "key": ALL}, "value"),
        prevent_initial_call=True,
    )
    def apply_scale_bounds(bmins, bmaxs, range_vals):
        # Для ALL нужен список no_update, не один раз.
        n = len(bmins) if bmins else 0
        nu = [no_update] * n
        if not bmins or not bmaxs or not range_vals or n == 0:
            return nu, nu, nu
        new_min, new_max, new_val = [], [], []
        for bmn, bmx, rv in zip(bmins, bmaxs, range_vals):
            try:
                lo = float(bmn)
                hi = float(bmx)
            except (TypeError, ValueError):
                return nu, nu, nu
            if lo > hi:
                lo, hi = hi, lo
            if rv is None or len(rv) < 2:
                v = [(lo + hi) / 2, (lo + hi) / 2]
            else:
                a, b = float(rv[0]), float(rv[1])
                a = max(lo, min(a, hi))
                b = max(lo, min(b, hi))
                if a > b:
                    c = (lo + hi) / 2
                    v = [c, c]
                else:
                    v = [a, b]
            new_min.append(lo)
            new_max.append(hi)
            new_val.append(v)
        return new_min, new_max, new_val

    # Если ползунок уперся в край шкалы, расширяем границы на 10.
    @app.callback(
        Output({"type": "param-bound-min", "key": ALL}, "value", allow_duplicate=True),
        Output({"type": "param-bound-max", "key": ALL}, "value", allow_duplicate=True),
        Output({"type": "param-range", "key": ALL}, "min", allow_duplicate=True),
        Output({"type": "param-range", "key": ALL}, "max", allow_duplicate=True),
        Input({"type": "param-range", "key": ALL}, "value"),
        State({"type": "param-range", "key": ALL}, "min"),
        State({"type": "param-range", "key": ALL}, "max"),
        prevent_initial_call=True,
    )
    def auto_expand_slider_bounds(range_vals, mins, maxs):
        n = len(range_vals) if range_vals else 0
        nu = [no_update] * n
        if not range_vals or mins is None or maxs is None or len(mins) != n or len(maxs) != n:
            return nu, nu, nu, nu

        new_bmins, new_bmaxs, new_mins, new_maxs = [], [], [], []
        changed = False
        eps = 1e-12

        for rv, mn, mx in zip(range_vals, mins, maxs):
            if rv is None or len(rv) < 2 or mn is None or mx is None:
                new_bmins.append(no_update)
                new_bmaxs.append(no_update)
                new_mins.append(no_update)
                new_maxs.append(no_update)
                continue

            lo = float(mn)
            hi = float(mx)
            a = float(rv[0])
            b = float(rv[1])

            new_lo = lo
            new_hi = hi
            if a <= lo + eps:
                new_lo = lo - 10.0
            if b >= hi - eps:
                new_hi = hi + 10.0

            if new_lo != lo or new_hi != hi:
                changed = True
                new_bmins.append(new_lo)
                new_bmaxs.append(new_hi)
                new_mins.append(new_lo)
                new_maxs.append(new_hi)
            else:
                new_bmins.append(no_update)
                new_bmaxs.append(no_update)
                new_mins.append(no_update)
                new_maxs.append(no_update)

        if not changed:
            return nu, nu, nu, nu
        return new_bmins, new_bmaxs, new_mins, new_maxs

    # Интервалы и шаг связаны: changing one recalculates the other.
    @app.callback(
        Output({"type": "param-steps-input", "key": ALL}, "value"),
        Output({"type": "param-step-size-input", "key": ALL}, "value"),
        Input({"type": "param-range", "key": ALL}, "value"),
        Input({"type": "param-steps-input", "key": ALL}, "value"),
        Input({"type": "param-step-size-input", "key": ALL}, "value"),
        prevent_initial_call=True,
    )
    def sync_steps_and_step_size(range_vals, steps_vals, step_size_vals):
        if not range_vals:
            return [], []

        n = len(range_vals)
        if steps_vals is None or len(steps_vals) != n:
            steps_vals = [0] * n
        if step_size_vals is None or len(step_size_vals) != n:
            step_size_vals = [0] * n

        trigger_prop = callback_context.triggered[0]["prop_id"] if callback_context.triggered else ""
        from_step_size = "param-step-size-input" in trigger_prop

        out_steps = []
        out_step_sizes = []
        for rv, st, step_size in zip(range_vals, steps_vals, step_size_vals):
            if rv is None or len(rv) < 2:
                out_steps.append(no_update)
                out_step_sizes.append(no_update)
                continue

            lo, hi = float(rv[0]), float(rv[1])
            span = max(0.0, hi - lo)
            collapsed = span < 1e-12
            if collapsed:
                out_steps.append(0)
                out_step_sizes.append(0)
                continue

            if from_step_size:
                try:
                    user_step = float(step_size)
                except (TypeError, ValueError):
                    user_step = 0.0
                if user_step <= 0:
                    try:
                        prev_steps = int(st) if st is not None else 1
                    except (TypeError, ValueError):
                        prev_steps = 1
                    prev_steps = max(1, prev_steps)
                    out_steps.append(prev_steps)
                    out_step_sizes.append(span / prev_steps)
                else:
                    intervals = max(1, int(round(span / user_step)))
                    out_steps.append(intervals)
                    out_step_sizes.append(span / intervals)
                continue

            try:
                intervals = int(st) if st is not None else 0
            except (TypeError, ValueError):
                intervals = 0
            intervals = max(1, intervals)
            out_steps.append(intervals)
            out_step_sizes.append(span / intervals)

        return out_steps, out_step_sizes

    # Метки на слайдере при смене диапазона или шагов.
    @app.callback(
        Output({"type": "param-range", "key": ALL}, "marks"),
        Input({"type": "param-range", "key": ALL}, "value"),
        Input({"type": "param-steps-input", "key": ALL}, "value"),
        State({"type": "param-range", "key": ALL}, "id"),
        State({"type": "param-default", "key": ALL}, "data"),
        prevent_initial_call=True,
    )
    def update_slider_marks(range_values, steps_values, _ids, default_values):
        n = len(range_values) if range_values else 0
        if not range_values or not steps_values or n == 0:
            return [no_update] * n
        if default_values is None:
            default_values = [None] * n
        if (
            len(steps_values) != n
            or (_ids is not None and len(_ids) != n)
            or (default_values is not None and len(default_values) != n)
        ):
            return [no_update] * n

        new_marks = []
        for range_val, steps, _, default_val in zip(range_values, steps_values, _ids, default_values):
            if range_val is None or len(range_val) < 2 or steps is None:
                new_marks.append({})
                continue

            st = int(steps) if steps is not None else 0
            if st < 1:
                st = 0
            # Метки по выбранному отрезку.
            marks = generate_slider_marks(range_val[0], range_val[1], st)
            if default_val is not None:
                marks[float(default_val)] = {
                    "label": "|",
                    "style": {
                        "color": "#d93025",
                        "fontWeight": "700",
                        "fontSize": "20px",
                        "transform": "translateY(-28px)",
                    },
                }
            new_marks.append(marks)

        return new_marks

    # Текст: какие значения попадут в серии.
    @app.callback(
        Output({"type": "param-preview", "key": ALL}, "children"),
        Input({"type": "param-range", "key": ALL}, "value"),
        Input({"type": "param-steps-input", "key": ALL}, "value"),
        State({"type": "param-range", "key": ALL}, "id"),
        prevent_initial_call=False,
    )
    def update_param_preview(range_values, steps_values, _ids):
        n = len(range_values) if range_values else 0
        if not range_values or not steps_values or n == 0:
            return [no_update] * n
        if len(steps_values) != n or (_ids is not None and len(_ids) != n):
            return [no_update] * n

        previews = []
        for range_val, steps, _ in zip(range_values, steps_values, _ids):
            if range_val is None or len(range_val) < 2 or steps is None:
                previews.append("Некорректные значения")
                continue

            min_val = range_val[0]
            max_val = range_val[1]
            if min_val > max_val:
                previews.append("Минимум не может быть больше максимума")
                continue
            if abs(float(min_val) - float(max_val)) < 1e-15:
                previews.append(f"Одно значение (интервалов 0): {min_val:.4f}")
                continue
            st = int(steps) if steps is not None else 1
            if st < 1:
                previews.append("Разведите ползунки — число интервалов станет 1")
                continue

            values = generate_parameter_values(min_val, max_val, st)
            if len(values) > 6:
                # Длинный список — сокращённо.
                values_str = f"{values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f}, ..., {values[-1]:.2f}"
            else:
                values_str = ", ".join([f"{v:.2f}" for v in values])

            previews.append(f"Значения в выбранном поддиапазоне: {values_str} (всего {len(values)})")

        return previews
