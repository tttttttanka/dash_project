import time
import threading
from datetime import datetime

import pandas as pd

from zadacha import Task
from sluzhby.fayl_menedzher import FileManager


def run_calculations(series_data, base_dir):
    # Запуск серий в фоновом потоке.
    if not series_data:
        return None

    parameter_series = pd.DataFrame(series_data)
    if parameter_series.empty:
        return None

    file_manager = FileManager(base_dir)
    n = len(parameter_series)
    base_instant = datetime.now()
    # Уникальное имя папки на каждую серию.
    series_folder_names = [
        FileManager.series_folder_name_at(base_instant, offset_microseconds=i) for i in range(n)
    ]
    series_paths = [file_manager.ensure_series_paths(name) for name in series_folder_names]

    def run_tasks_thread():
        try:
            for j, (_, row) in enumerate(parameter_series.iterrows()):
                sp = series_paths[j]
                try:
                    Task(row.to_dict(), j, sp.log_path, sp.results_path).solve()
                    time.sleep(0.1)
                except Exception as err:
                    with open(sp.log_path, "a", encoding="utf-8") as f:
                        f.write(f"Ошибка в серии {j + 1}: {err}\n")

            if series_paths:
                with open(series_paths[-1].log_path, "a", encoding="utf-8") as f:
                    f.write("\nВСЕ РАСЧЕТЫ ЗАВЕРШЕНЫ\n")
        except Exception as err:
            if series_paths:
                with open(series_paths[0].log_path, "a", encoding="utf-8") as f:
                    f.write(f"Ошибка: {err}\n")

    threading.Thread(target=run_tasks_thread, daemon=True).start()
    return series_folder_names
