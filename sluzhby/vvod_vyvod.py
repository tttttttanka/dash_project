from sluzhby.fayl_menedzher import FileManager


def export_history_to_dataframe(file_manager: FileManager):
    # Таблица истории для выгрузки в CSV.
    return file_manager.load_history_df()

