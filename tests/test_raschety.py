"""Модульные тесты для sluzhby.raschety (mock Task и ускоренный sleep)."""

import time
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from sluzhby import raschety as r


def test_run_calculations_no_data():
    """Проверка: без данных серий функция сразу выходит и возвращает None.

    Первые проверки в run_calculations: not series_data и пустой DataFrame после
    pd.DataFrame(series_data) — до создания FileManager и потока не доходим.
    Второй аргумент (base_dir) здесь не используется из-за раннего return.
    """
    assert r.run_calculations(None, str(Path("/"))) is None
    assert r.run_calculations([], str(Path("/"))) is None


def test_run_calculations_empty_frame():
    """Проверка: пустой список записей после to_dict('records') — тот же ранний выход.

    Строится пустой DataFrame, iterrows ничего не даёт, parameter_series.empty
    истинно — возвращается None.
    """
    df = pd.DataFrame()
    raw = df.to_dict("records")
    assert raw == []
    assert r.run_calculations(raw, ".") is None


def _wait_for_marker(log_path: Path, marker: str, timeout: float = 5.0) -> bool:
    """Ожидает появления строки marker в log_path (фоновый поток пишет асинхронно)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if log_path.is_file():
            text = log_path.read_text(encoding="utf-8", errors="replace")
            if marker in text:
                return True
        time.sleep(0.02)
    return False


def test_run_calculations_with_mock_task(tmp_path):
    """Проверка: поток вызывает Task(...).solve() по строкам, в конце пишет «ВСЕ РАСЧЕТЫ ЗАВЕРШЕНЫ».

    run_calculations строит DataFrame, создаёт FileManager, имена папок через
    series_folder_name_at с микросекундным сдвигом, ensure_series_paths для
    каждой строки. Реальный Task заменён на FakeTask: solve пишет в log.
    time.sleep обнулён, чтобы тест не ждал. Проверяем список имён папок,
    что фоновой поток дописал финальную строку в лог последней серии.
    """
    captured = []

    class FakeTask:
        def __init__(self, params, index, log_path, results_path):
            captured.append((index, params, log_path, results_path))
            self._log_path = log_path

        def solve(self):
            Path(self._log_path).parent.mkdir(parents=True, exist_ok=True)
            Path(self._log_path).write_text("series_done\n", encoding="utf-8")

    row = {"m": 1.0, "g": 9.81, "h": 2.0, "V": 0.5, "T": 20.0, "C": 100.0}

    with patch("sluzhby.raschety.Task", FakeTask), patch("sluzhby.raschety.time.sleep", lambda *_args, **_kw: None):
        names = r.run_calculations([row], str(tmp_path))

    assert names is not None and len(names) == 1
    log_path = tmp_path / names[0] / "log.txt"
    assert _wait_for_marker(log_path, "ВСЕ РАСЧЕТЫ ЗАВЕРШЕНЫ"), "Фоновый поток не завершил лог за отведённое время"
    assert len(captured) == 1
    assert captured[0][0] == 0
    content = log_path.read_text(encoding="utf-8")
    assert "series_done" in content


def test_run_calculations_mock_task_logs_error(tmp_path):
    """Проверка: исключение в solve ловится, текст ошибки дописывается в log серии.

    Цикл по сериям в потоке оборачивает Task.solve в try/except; при ошибке
    открывается append в log_path этой серии. После успешной/ошибочной серии к
    последнему логу всё равно может добавиться «ВСЕ РАСЧЕТЫ...» если series_paths не пустой.
    """
    class FailingTask:
        def __init__(self, params, index, log_path, results_path):
            self.log_path = log_path

        def solve(self):
            raise RuntimeError("boom")

    row = {"m": 1.0, "g": 9.81, "h": 2.0, "V": 0.5, "T": 20.0, "C": 100.0}

    with patch("sluzhby.raschety.Task", FailingTask), patch("sluzhby.raschety.time.sleep", lambda *_a, **_k: None):
        names = r.run_calculations([row], str(tmp_path))

    assert names
    log_path = tmp_path / names[0] / "log.txt"
    assert _wait_for_marker(log_path, "boom")
