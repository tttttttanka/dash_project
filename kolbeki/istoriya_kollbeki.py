import os
import time

from dash import dcc, no_update
from dash.dependencies import Input, Output, State

from sluzhby.fayl_menedzher import FileManager
from sluzhby.vvod_vyvod import export_history_to_dataframe
from interfejs.komponenty import format_log, create_history_table


def _runs_fs_signature(base_dir: str):
    # Строка-снимок папки runs, чтобы заметить изменения на диске.
    if not os.path.isdir(base_dir):
        return ""
    parts: list[str] = []
    for root, _, files in os.walk(base_dir):
        for fn in sorted(files):
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, base_dir)
            try:
                st = os.stat(fp)
                parts.append(f"{rel}:{st.st_mtime_ns}:{st.st_size}")
            except OSError:
                parts.append(f"{rel}:missing")
    return "\n".join(parts)


def register_history_callbacks(app, base_dir):
    # Колбэки: лог, таблица истории, экспорт, синхронизация с папкой runs.
    file_manager = FileManager(base_dir)

    # Читать лог по таймеру, пока идёт расчёт.
    @app.callback(
        Output("log-container", "children"),
        Output("is-running", "data", allow_duplicate=True),
        Output("log-interval", "disabled", allow_duplicate=True),
        Input("log-interval", "n_intervals"),
        State("current-run-id", "data"),
        State("is-running", "data"),
        prevent_initial_call=True,
    )
    def update_log(_n_intervals, run_id, is_running):
        # Обновить текст лога; в конце отключить опрос.
        if run_id is None:
            return "Нет активных расчетов", False, True

        log_content = file_manager.read_log(run_id)
        if log_content == "":
            return "Ожидание вычислений...", is_running, False

        formatted_log = format_log(log_content)
        # После строки «все расчёты завершены» таймер лога больше не нужен.
        if "ВСЕ РАСЧЕТЫ ЗАВЕРШЕНЫ" in log_content:
            return formatted_log, False, True

        return formatted_log, is_running, False

    # Обновить таблицу, когда расчёт закончился.
    @app.callback(
        Output("table-container", "children", allow_duplicate=True),
        Input("is-running", "data"),
        State("current-run-id", "data"),
        prevent_initial_call=True,
    )
    def auto_update_on_completion(is_running, run_id):
        # Перечитать историю после окончания расчёта.
        if not is_running and run_id:
            time.sleep(0.5)
            return create_history_table(base_dir)
        return no_update

    # Кнопка «Обновить историю».
    @app.callback(
        Output("table-container", "children"),
        Input("refresh-history-btn", "n_clicks"),
        State("is-running", "data"),
    )
    def update_table_and_plots(n_clicks, is_running):
        # Обновить таблицу вручную (графики — отдельно).
        if n_clicks and not is_running:
            return create_history_table(base_dir)
        return no_update

    # Сохранить историю в CSV.
    @app.callback(
        Output("download-dataframe-csv", "data"),
        Input("import-results-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def import_to_csv(n_clicks):
        # Скачать файл с таблицей.
        df = export_history_to_dataframe(file_manager)
        if df.empty:
            return no_update
        return dcc.send_data_frame(df.to_csv, "results_import.csv", index=False)

    # Если папки удалили вручную — подтянуть актуальное состояние.
    @app.callback(
        Output("table-container", "children", allow_duplicate=True),
        Output("current-run-id", "data", allow_duplicate=True),
        Output("log-container", "children", allow_duplicate=True),
        Output("runs-signature", "data"),
        Input("history-sync-interval", "n_intervals"),
        State("is-running", "data"),
        State("current-run-id", "data"),
        State("runs-signature", "data"),
        prevent_initial_call=True,
    )
    def sync_runs_view_from_disk(_n, is_running, run_id, prev_sig):
        # Сравнить с диском; при пропаже серий сбросить лог и текущий запуск.
        if is_running:
            return no_update, no_update, no_update, no_update

        sig = _runs_fs_signature(base_dir)

        stale_run = False
        if isinstance(run_id, list) and run_id:
            for name in run_id:
                if not os.path.exists(os.path.join(base_dir, name)):
                    stale_run = True
                    break

        if not stale_run and sig == prev_sig:
            return no_update, no_update, no_update, no_update

        table = create_history_table(base_dir)

        if stale_run:
            return (
                table,
                None,
                "Лог появится здесь после запуска",
                sig,
            )

        return table, no_update, no_update, sig
