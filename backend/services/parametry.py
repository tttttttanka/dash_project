import itertools
import math
import re
# Для variable: min/max = center ± ratio×|center| 

# Предел точек сетки при вводе шага вручную (защита от зависания UI).
MAX_GRID_POINTS = 2000
# Максимальное общее число серий из всех комбинаций параметров.
MAX_SERIES_COUNT = 10000


class SeriesLimitExceeded(ValueError):
    pass

DEFAULT_INTERVALS = 0
DEFAULT_RATIO = 1.0

PARAM_DEFINITIONS = {
    "m": {
        "label": "Масса",
        "unit": "кг",
        "kind": "variable",
        "ratio": DEFAULT_RATIO,
    },
    "h": {
        "label": "Высота",
        "unit": "м",
        "kind": "variable",
        "ratio": DEFAULT_RATIO,
    },
    "V": {
        "label": "Скорость",
        "unit": "м/с",
        "kind": "variable",
        "ratio": DEFAULT_RATIO,
    },
    "T": {
        "label": "Температура",
        "unit": "°C",
        "kind": "variable",
        "ratio": DEFAULT_RATIO,
    },
    "g": {
        "label": "Ускорение свободного падения",
        "unit": "м/с²",
        "kind": "constant",
    },
    "C": {
        "label": "Удельная теплоёмкость",
        "unit": "Дж/(кг·°C)",
        "kind": "constant",
    },
}


def parse_parameters_file(content):
    # Строки вида имя = число; смысл имён — в PARAM_DEFINITIONS.
    params = {}
    constants = {}

    for line in content.split("\n"):
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue

        m = re.match(r"^(\w+)\s*=\s*([\d.eE+-]+)\s*$", raw)
        if not m:
            continue

        name, val_s = m.group(1), m.group(2)
        if name not in PARAM_DEFINITIONS:
            continue

        meta = PARAM_DEFINITIONS[name]
        center = float(val_s)
        info = {
            "name": meta["label"],
            "default": center,
            "unit": meta.get("unit", ""),
        }

        if meta["kind"] == "constant":
            info["value"] = center
            constants[name] = info
            continue

        ratio = float(meta["ratio"])
        mn = center - ratio * abs(center)
        mx = center + ratio * abs(center)
        if mn >= mx:
            eps = max(1e-9, abs(center) * 1e-9 + 1e-9)
            mn, mx = center - eps, center + eps

        info["min"] = mn
        info["max"] = mx
        info["steps"] = DEFAULT_INTERVALS
        params[name] = info

    return {"parameters": params, "constants": constants}


def is_equal_subdivision(span, steps_int, step_sz):
    # Шаг в поле совпадает с равномерным span/steps — считаем режим «по числу интервалов».
    if span <= 0 or steps_int < 1:
        return True
    try:
        u = float(step_sz)
    except (TypeError, ValueError):
        return True
    if u <= 0 or not math.isfinite(u):
        return True
    eq = float(span) / float(steps_int)
    if not math.isfinite(eq):
        return True
    tol = max(1e-9, 1e-7 * max(abs(eq), abs(span), 1.0))
    return abs(u - eq) <= tol


def generate_parameter_values_by_user_step(min_val, max_val, step):
    # От min идём с шагом s: min, min+s, … пока не выйдем за max; если max не попал — добавляем max (остаток).
    mn, mx = float(min_val), float(max_val)
    try:
        s = float(step)
    except (TypeError, ValueError):
        return [mn]
    if not (math.isfinite(mn) and math.isfinite(mx) and math.isfinite(s)) or s <= 0:
        return [mn]
    if abs(mx - mn) < 1e-15:
        return [mn]
    lo, hi = (mn, mx) if mn <= mx else (mx, mn)
    eps = max(1e-12 * max(abs(hi), abs(lo), 1.0), 1e-14)
    vals = [lo]
    k = 1
    while len(vals) < MAX_GRID_POINTS:
        x = lo + k * s
        if x > hi - eps:
            break
        vals.append(x)
        k += 1
    if vals[-1] < hi - eps:
        vals.append(hi)
    return vals


def values_for_parameter_range(min_val, max_val, steps_int, step_sz):
    # Сетка значений: либо равные доли по числу интервалов, либо арифметический шаг от min с хвостом до max.
    mn, mx = float(min_val), float(max_val)
    if abs(mx - mn) < 1e-15:
        return [mn]
    lo, hi = (mn, mx) if mn <= mx else (mx, mn)
    span = hi - lo
    try:
        st_i = int(steps_int) if steps_int is not None else 1
    except (TypeError, ValueError):
        st_i = 1
    st_i = max(1, st_i)
    try:
        us = float(step_sz) if step_sz is not None else 0.0
    except (TypeError, ValueError):
        us = 0.0
    if us > 0 and not is_equal_subdivision(span, st_i, us):
        return generate_parameter_values_by_user_step(lo, hi, us)
    return generate_parameter_values(lo, hi, st_i)


def build_marks_from_values(values):
    # Подписи слайдера по списку чисел (как generate_slider_marks, но без равномерной формулы).
    if not values:
        return {}
    if len(values) == 1:
        v = float(values[0])
        return {v: f"{v:.2f}"}
    mn_f, mx_f = float(values[0]), float(values[-1])
    if len(values) > 20:
        return {mn_f: f"{mn_f:.1f}", mx_f: f"{mx_f:.1f}"}
    marks = {}
    if len(values) <= 11:
        for v in values:
            vf = float(v)
            marks[vf] = f"{vf:.2f}"
    else:
        step_idx = max(1, len(values) // 5)
        for i in range(0, len(values), step_idx):
            vf = float(values[i])
            marks[vf] = f"{vf:.2f}"
        marks[float(values[-1])] = f"{float(values[-1]):.2f}"
    return marks


def generate_parameter_values(min_val, max_val, steps):
    # Значения от min до max с шагами; совпали границы — одно число.
    if abs(float(max_val) - float(min_val)) < 1e-15:
        return [float(min_val)]
    if steps is None or steps <= 0:
        return [float(min_val)]

    step_size = (float(max_val) - float(min_val)) / steps
    return [float(min_val) + i * step_size for i in range(steps + 1)]


def generate_slider_marks(min_val, max_val, steps):
    # Подписи на шкале (при 0 шагов — только края).
    if steps is None or steps <= 0:
        return {min_val: f"{min_val:.1f}", max_val: f"{max_val:.1f}"}

    if steps > 20:
        return {min_val: f"{min_val:.1f}", max_val: f"{max_val:.1f}"}

    marks = {}
    values = generate_parameter_values(min_val, max_val, steps)

    if len(values) <= 11:
        for val in values:
            marks[val] = f"{val:.2f}"
    else:
        step_idx = max(1, len(values) // 5)
        for i in range(0, len(values), step_idx):
            marks[values[i]] = f"{values[i]:.2f}"
        marks[values[-1]] = f"{values[-1]:.2f}"

    return marks


def generate_series_data(range_values, steps_values, param_ids, step_size_values=None):
    # Создать комбинации параметров и проверить их общее количество до генерации.
    if step_size_values is None:
        step_size_values = [None] * len(range_values)
    param_values_dict = {}
    for range_val, steps, id_dict, step_sz in zip(range_values, steps_values, param_ids, step_size_values):
        if range_val is None or len(range_val) < 2 or steps is None:
            continue
        min_val, max_val = range_val[0], range_val[1]
        if min_val > max_val:
            continue
        param_key = id_dict.get("key")
        if abs(float(min_val) - float(max_val)) < 1e-15:
            param_values_dict[param_key] = [float(min_val)]
            continue
        try:
            st = int(steps) if steps is not None else 1
        except (TypeError, ValueError):
            st = 1
        st = max(1, st)
        param_values_dict[param_key] = values_for_parameter_range(min_val, max_val, st, step_sz)

    if not param_values_dict:
        return []

    param_names = list(param_values_dict.keys())
    param_values = list(param_values_dict.values())
    # Проверяем общий размер декартова произведения до создания списка серий.
    series_count = math.prod(len(values) for values in param_values)
    if series_count > MAX_SERIES_COUNT:
        raise SeriesLimitExceeded(
            f"Получится {series_count:,} серий, а максимум — {MAX_SERIES_COUNT:,}. "
            "Уменьшите диапазон или число интервалов."
        )

    combinations = list(itertools.product(*param_values))
    return [dict(zip(param_names, combo)) for combo in combinations]
