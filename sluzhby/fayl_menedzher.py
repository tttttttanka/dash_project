import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Union

import pandas as pd


@dataclass(frozen=True)
class SeriesPaths:
    # Папка серии: log.txt и results.csv.
    series_dir: str
    log_path: str
    results_path: str


class FileManager:
    def __init__(self, base_dir: str):
        # Корневая папка runs.
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    @staticmethod
    def series_folder_name_at(instant: datetime, offset_microseconds: int = 0) -> str:
        #  дата, время, микросекунды.
        t = instant + timedelta(microseconds=offset_microseconds)
        return t.strftime("%Y_%m_%dT%H%M%S_%f")

    def ensure_series_paths(self, folder_name: str) -> SeriesPaths:
        # Создать папку серии.
        series_dir = os.path.join(self.base_dir, folder_name)
        os.makedirs(series_dir, exist_ok=True)
        log_path = os.path.join(series_dir, "log.txt")
        results_path = os.path.join(series_dir, "results.csv")
        return SeriesPaths(
            series_dir=series_dir,
            log_path=log_path,
            results_path=results_path,
        )

    def read_log(self, run_ref: Union[str, list[str], None]) -> str:
        # Список папок — склеить логи; строка — старый вариант с вложенными папками.
        if not run_ref:
            return ""
        if isinstance(run_ref, list):
            parts: list[str] = []
            for name in run_ref:
                lp = os.path.join(self.base_dir, name, "log.txt")
                if os.path.exists(lp):
                    with open(lp, "r", encoding="utf-8") as f:
                        parts.append(f.read().rstrip())
            return "\n\n".join(parts) + ("\n" if parts else "")

        run_id = run_ref
        run_dir = os.path.join(self.base_dir, run_id)
        if not os.path.isdir(run_dir):
            return ""
        parts = []
        master = os.path.join(run_dir, "log.txt")
        if os.path.exists(master):
            with open(master, "r", encoding="utf-8") as f:
                parts.append(f.read().rstrip())
        for name in sorted(os.listdir(run_dir)):
            sub = os.path.join(run_dir, name)
            if not os.path.isdir(sub):
                continue
            s_log = os.path.join(sub, "log.txt")
            if os.path.exists(s_log):
                with open(s_log, "r", encoding="utf-8") as f:
                    parts.append(f.read().rstrip())
        return "\n\n".join(parts) + ("\n" if parts else "")

    def load_history_df(self) -> pd.DataFrame:
        # Собрать все results.csv (новый и старый формат папок).
        if not os.path.exists(self.base_dir):
            return pd.DataFrame()

        rows: list[pd.DataFrame] = []
        for folder in sorted(os.listdir(self.base_dir)):
            folder_path = os.path.join(self.base_dir, folder)
            if not os.path.isdir(folder_path):
                continue

            legacy_csv = os.path.join(folder_path, "results.csv")
            if os.path.exists(legacy_csv):
                try:
                    df_part = pd.read_csv(legacy_csv)
                    df_part["run"] = folder
                    rows.append(df_part)
                except Exception:
                    pass
                continue

            for sub in sorted(os.listdir(folder_path)):
                sub_path = os.path.join(folder_path, sub)
                if not os.path.isdir(sub_path):
                    continue
                csv_path = os.path.join(sub_path, "results.csv")
                if not os.path.exists(csv_path):
                    continue
                try:
                    df_part = pd.read_csv(csv_path)
                    df_part["run"] = f"{folder}/{sub}"
                    rows.append(df_part)
                except Exception:
                    continue

        if not rows:
            return pd.DataFrame()
        return pd.concat(rows, ignore_index=True)
