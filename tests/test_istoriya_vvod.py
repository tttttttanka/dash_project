"""Тесты тонких обёрток istoriya и vvod_vyvod."""

import pandas as pd

from sluzhby import istoriya as ist
from sluzhby import vvod_vyvod as vv
from sluzhby.fayl_menedzher import FileManager


def test_load_history_via_istoriya(tmp_path):
    """Проверка: load_history_df(base_dir) делегирует в FileManager(base_dir).load_history_df.

    Внутри istoriya только конструируется FileManager и вызывается тот же метод
    загрузки всех results.csv под base_dir; тест создаёт одну серию с CSV и
    убеждается, что таблица не пустая.
    """
    sdir = tmp_path / "s1"
    sdir.mkdir()
    pd.DataFrame([{"k": 1}]).to_csv(sdir / "results.csv", index=False)
    df = ist.load_history_df(str(tmp_path))
    assert not df.empty


def test_read_log_via_istoriya(tmp_path):
    """Проверка: read_log(base_dir, run_ref) пробрасывает вызов в FileManager.read_log.

    Поведение совпадает с fayl_menedzher: строка run_ref читает log в
    base_dir/run_ref/log.txt (и при необходимости вложенные).
    """
    d = tmp_path / "r1"
    d.mkdir()
    (d / "log.txt").write_text("hello", encoding="utf-8")
    assert "hello" in ist.read_log(str(tmp_path), "r1")


def test_export_history_to_dataframe(tmp_path):
    """Проверка: export_history_to_dataframe(file_manager) возвращает тот же DataFrame, что load_history_df у менеджера.

    Обёртка не меняет данные: просто вызывает file_manager.load_history_df()
    для выгрузки истории в CSV из Dash; передаём готовый FileManager с temp base.
    """
    sdir = tmp_path / "s2"
    sdir.mkdir()
    pd.DataFrame([{"z": 3}]).to_csv(sdir / "results.csv", index=False)
    fm = FileManager(str(tmp_path))
    df = vv.export_history_to_dataframe(fm)
    assert not df.empty
