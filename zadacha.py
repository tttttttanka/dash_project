import os
import time
import pandas as pd


# Один расчёт серии: лог и таблица результатов в своей папке.
class Task:

    def __init__(self, params: dict, index: int, log_path: str, results_path: str):
        # Пути к log.txt и results.csv для этой серии.
        self.params = params
        self.index = index
        self.log_path = log_path
        self.results_path = results_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log(self, text: str):
        # Добавить строку в лог.
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(text + "\n")


    def param(self, key: str, default=None):
        # Число по имени; если нет ключа — ошибка в лог (или default).
        if key not in self.params:
            if default is not None:
                return default
            self.log(f"[ОШИБКА] Параметр '{key}' не найден.")
            raise ValueError(f"Missing parameter: {key}")
        return float(self.params[key])

    def step(self, name: str, value):
        # Записать промежуточное значение в лог.
        self.log(f"   {name}: {value:.4f}")
        time.sleep(0.4)


    def solve(self):
        # Считает серию и пишет одну строку в results.csv.
        self.log(f"\nСерия {self.index + 1} ")

        try:
            # Основные параметры
            m = self.param("m")
            g = self.param("g")
            h = self.param("h")
            V = self.param("V")
            T = self.param("T")
            
            # Константы
            C = self.param("C")

        except Exception as e:
            self.log(f"[ОШИБКА] Невозможно вычислить серию: {str(e)}")
            return

        self.log(f"Параметры: m={m}, g={g}, h={h}, V={V}, T={T}")

        # --- Потенциальная энергия ---
        E_pot = m * g * h
        self.step("E_pot (потенциальная)", E_pot)

        # --- Кинетическая энергия ---
        E_kin = 0.5 * m * V ** 2
        self.step("E_kin (кинетическая)", E_kin)

        # --- Полная энергия ---
        E_total = E_pot + E_kin
        self.step("E_total (полная)", E_total)

        Q = m * C * (T - 20)
        self.step("E_heat (тепловая)", Q)

        row = {
            "series": self.index + 1,

            "m": m,
            "g": g,
            "h": h,
            "V": V,
            "T": T,

            "C": C,

            "E_pot": E_pot,
            "E_kin": E_kin,
            "E_total": E_total,
            "Q": Q,

        }

        pd.DataFrame([row]).to_csv(self.results_path, index=False)

        self.log("Серия завершена.\n")
