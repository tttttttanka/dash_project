"""Модульные тесты для sluzhby.parametry."""

import pytest

from sluzhby import parametry as p


def test_parse_parameters_file_empty():
    """Проверка: при пустом тексте файл параметров считается пустым.

    parse_parameters_file разбивает content по строкам; пустые и комментируемые
    строки пропускает; при отсутствии валидных присвоений возвращает пустые
    словари parameters и constants.
    """
    out = p.parse_parameters_file("")
    assert out == {"parameters": {}, "constants": {}}


def test_parse_parameters_file_skips_comments_and_unknown():
    """Проверка: строки-комментарии и переменные не из PARAM_DEFINITIONS игнорируются.

    Функция бежит по строкам, режет пробелы, пропускает #..., матчит только
    «имя = число». Имена, которых нет в описании параметров в PARAM_DEFINITIONS,
    не попадают в результат; известное «m» превращается в запись в parameters.
    """
    text = """
# comment
unknown = 1
m = 10
foo = 2
"""
    out = p.parse_parameters_file(text)
    assert "m" in out["parameters"]
    assert "unknown" not in out["parameters"] and "foo" not in out["parameters"]


def test_parse_parameters_file_constants_and_variables():
    """Проверка: константы попадают в constants с полем value, переменные — в parameters с min/max.

    По kind из PARAM_DEFINITIONS: для «constant» в constants кладётся value;
    для «variable» считаются границы center ± ratio×|center| и поля min, max,
    steps (по умолчанию для steps — DEFAULT_INTERVALS).
    """
    text = """
g = 9.81
C = 4200
m = 2.5
h = 1e2
V = 3.0
T = 25
"""
    out = p.parse_parameters_file(text)
    assert "g" in out["constants"] and out["constants"]["g"]["value"] == pytest.approx(9.81)
    assert "C" in out["constants"]
    for key in ("m", "h", "V", "T"):
        assert key in out["parameters"]
        assert "min" in out["parameters"][key]
        assert "max" in out["parameters"][key]


def test_parse_parameters_zero_center_expands_interval():
    """Проверка: если min и max совпали (центр 0), интервал искусственно расширяется на eps.

    Для переменной при mn >= mx код подставляет маленький eps вокруг center,
    чтобы шкала слайдера не была вырожденной.
    """
    text = "m = 0\n"
    out = p.parse_parameters_file(text)
    info = out["parameters"]["m"]
    assert info["min"] < info["max"]


def test_generate_parameter_values_equal_bounds():
    """Проверка: при равных min и max возвращается один элемент — сама граница.

    Функция сравнивает max_val и min_val по модулю разности с 1e-15 и тогда даёт
    список из одного float.
    """
    assert p.generate_parameter_values(5.0, 5.0, 10) == [5.0]


def test_generate_parameter_values_nonpositive_steps():
    """Проверка: при steps <= 0 или None сетка не строится — только левая граница.

    Ветка «без шагов» возвращает [min_val], не деля отрезок на части.
    """
    assert p.generate_parameter_values(0.0, 1.0, 0) == [0.0]
    assert p.generate_parameter_values(0.0, 1.0, None) == [0.0]


def test_generate_parameter_values_steps():
    """Проверка: равномерная сетка из steps+1 точек от min до max включительно.

    step_size = (max - min) / steps; значения i*step_size от i=0 до steps.
    """
    vals = p.generate_parameter_values(0.0, 10.0, 2)
    assert len(vals) == 3
    assert vals[0] == pytest.approx(0.0)
    assert vals[-1] == pytest.approx(10.0)


def test_generate_slider_marks_zero_steps():
    """Проверка: при нуле шагов на шкале только две подписи — min и max.

    generate_slider_marks при steps <= 0 строит словарь из двух ключей,
    форматируя числа с одним знаком после запятой.
    """
    m = p.generate_slider_marks(1.0, 5.0, 0)
    assert set(m.keys()) == {1.0, 5.0}


def test_generate_slider_marks_many_steps_only_ends():
    """Проверка: при steps > 20 подписи только на концах (не перегружать UI).

    Та же ветка, что и при нуле шагов — только min и max в словаре marks.
    """
    m = p.generate_slider_marks(0.0, 100.0, 25)
    assert set(m.keys()) == {0.0, 100.0}


def test_generate_slider_marks_few_marks_all_values():
    """Проверка: при небольшом числе точек (≤11) подпись на каждой точке сетки.

    Вызывается generate_parameter_values; если len(values) <= 11, каждому
    значению ставится подпись с двумя знаками после запятой.
    """
    m = p.generate_slider_marks(0.0, 10.0, 2)
    assert len(m) >= 2


def test_generate_slider_marks_more_than_eleven_values_subsamples():
    """Проверка: при длинной сетке (>11 точек) подписи прореживаются, конец сохраняется.

    Берётся шаг по индексам (примерно пять меток), последняя точка всегда в marks.
    """
    m = p.generate_slider_marks(0.0, 10.0, 12)
    assert 0.0 in m and 10.0 in m
