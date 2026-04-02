import pandas as pd

from sluzhby.fayl_menedzher import FileManager


def load_history_df(base_dir: str) -> pd.DataFrame:
    # Одна таблица по всем сериям.
    return FileManager(base_dir).load_history_df()


def read_log(base_dir: str, run_ref):
    # Текст лога по списку папок или старому имени прогона.
    return FileManager(base_dir).read_log(run_ref)
