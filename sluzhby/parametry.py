import re
# Для variable: min/max = center ± ratio×|center| 

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
