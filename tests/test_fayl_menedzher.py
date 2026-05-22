"""Модульные тесты для sluzhby.fayl_menedzher."""

from datetime import datetime, timezone

import pandas as pd

from sluzhby.fayl_menedzher import FileManager, SeriesPaths


def test_series_folder_name_at():
    """Проверка: имя папки серии форматируется из даты/времени и микросекунд.

    series_folder_name_at(instant) прибавляет offset_microseconds (0), затем
    strftime: год_месяц_день T часы минуты секунды _ микросекунды шестью цифрами.
    """
    t = datetime(2024, 3, 15, 14, 30, 45, 123456, tzinfo=timezone.utc)
    name = FileManager.series_folder_name_at(t)
    assert name.startswith("2024_03_15T143045_")
    assert "123456" in name


def test_series_folder_name_at_offset_microseconds():
    """Проверка: сдвиг времени меняет имя — папки для близких моментов не совпадают.

    У instant добавляется timedelta(microseconds=offset), поэтому две строки
    имени различаются при offset 0 и 1.
    """
    t = datetime(2024, 1, 1, 0, 0, 0, 0)
    name = FileManager.series_folder_name_at(t, offset_microseconds=1)
    assert name != FileManager.series_folder_name_at(t, offset_microseconds=0)


def test_ensure_series_paths(tmp_path):
    """Проверка: создаётся каталог серии и возвращаются пути к log.txt и results.csv.

    ensure_series_paths соединяет base_dir и folder_name через os.makedirs,
    затем собирает dataclass SeriesPaths с полными путями к файлам.
    """
    fm = FileManager(str(tmp_path))
    sp = fm.ensure_series_paths("run_1")
    assert isinstance(sp, SeriesPaths)
    assert sp.series_dir == str(tmp_path / "run_1")
    assert (tmp_path / "run_1").is_dir()
    assert sp.log_path.endswith("log.txt")
    assert sp.results_path.endswith("results.csv")


def test_read_log_empty_ref(tmp_path):
    """Проверка: если ссылку на прогон не передали или пустая строка — пустой ответ.

    read_log при falsy значении возвращает "" без обхода каталогов.
    """
    fm = FileManager(str(tmp_path))
    assert fm.read_log(None) == ""
    assert fm.read_log("") == ""


def test_read_log_list_concat(tmp_path):
    """Проверка: режим списка имён папок склеивает log.txt каждой папки по порядку.

    Для каждого имени читается base_dir/name/log.txt при существовании,
    результат соединяется через \\n\\n и в конце добавляется перевод строки если
    хоть что-то прочитали.
    """
    fm = FileManager(str(tmp_path))
    for name in ("a", "b"):
        d = tmp_path / name
        d.mkdir()
        (d / "log.txt").write_text(f"log_{name}", encoding="utf-8")
    text = fm.read_log(["a", "b"])
    assert "log_a" in text and "log_b" in text


def test_read_log_legacy_flat_log(tmp_path):
    """Проверка: строковый run_ref — только master log в корне run_id.

    Если run_dir существует, сначала читается run_dir/log.txt (если есть),
    без обхода подпапок, если не нужен «старый» формат с вложенностями.
    """
    fm = FileManager(str(tmp_path))
    run_dir = tmp_path / "run1"
    run_dir.mkdir()
    (run_dir / "log.txt").write_text("master", encoding="utf-8")
    assert "master" in fm.read_log("run1")


def test_read_log_nested_subdirs(tmp_path):
    """Проверка: для строкового run_ref подпапки с log.txt дописываются после master.

    Сортируется os.listdir; для каждой подпапки, если есть log.txt, текст
    добавляется к списку parts, затем join через \\n\\n.
    """
    fm = FileManager(str(tmp_path))
    run_dir = tmp_path / "nested_run"
    run_dir.mkdir()
    sub = run_dir / "sub1"
    sub.mkdir()
    (sub / "log.txt").write_text("sublog", encoding="utf-8")
    out = fm.read_log("nested_run")
    assert "sublog" in out


def test_load_history_df_missing_base():
    """Проверка: если base_dir не существует, таблица истории пустая.

    load_history_df сразу проверяет os.path.exists(self.base_dir) и возвращает
    пустой DataFrame без чтения.
    """
    fm = FileManager("/nonexistent/path/for/runs")
    df = fm.load_history_df()
    assert df.empty


def test_load_history_df_legacy_top_level_csv(tmp_path):
    """Проверка: «старый» формат — results.csv прямо в папке серии в base_dir.

    Для каждой подпапки base_dir сначала ищется legacy_csv; при успехе читается
    CSV, добавляется колонка run с именем папки, блок не ищет вложенные серии.
    """
    fm = FileManager(str(tmp_path))
    sdir = tmp_path / "series1"
    sdir.mkdir()
    pd.DataFrame([{"col": 1}]).to_csv(sdir / "results.csv", index=False)
    df = fm.load_history_df()
    assert not df.empty
    assert "run" in df.columns
    assert (df["run"] == "series1").any()


def test_load_history_df_nested_structure(tmp_path):
    """Проверка: новый формат — results.csv во вложенной подпапке внутри серии.

    Если в корне серии нет legacy results.csv, обходятся подкаталоги;
    run записывается как «папка_серии/подпапка».
    """
    fm = FileManager(str(tmp_path))
    outer = tmp_path / "outer"
    outer.mkdir()
    inner = outer / "inner"
    inner.mkdir()
    pd.DataFrame([{"x": 2}]).to_csv(inner / "results.csv", index=False)
    df = fm.load_history_df()
    assert not df.empty
    assert (df["run"] == "outer/inner").any()
