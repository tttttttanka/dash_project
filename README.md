# Dash App

Веб-приложение для автоматизации параметрических расчетов с визуализацией результатов и хранением истории запусков.

Приложение позволяет:
- загружать файл параметров;
- настраивать диапазоны значений через слайдеры;
- генерировать серии расчетов;
- запускать вычисления в несколько потоков;
- смотреть лог выполнения в реальном времени;
- анализировать результаты в таблицах и графиках (2D/3D);
- экспортировать данные в CSV.

## Структура проекта

```text
dash_project/
├── prilozhenie.py         # основной файл Dash-приложения
├── zadacha.py             # логика расчета
├── requirements.txt       # Python-зависимости
├── param_config.txt       # пример входного файла параметров
├── runs/                  # сохраненные результаты расчетов
├── assets/                # статические файлы (CSS, изображения)
│  └── stili_tablic.css    # стили таблиц (CSS)
└── electron-app/          # Electron-обертка (desktop-версия)
   ├── main.js
   └── package.json
```

## Требования

- Python 3.8+
- pip
- Node.js 14+ (только для Electron-версии)

## Пошаговый запуск (Windows, PowerShell)

### 1) Перейти в папку приложения

```powershell
cd "C:\Users\tanya\Desktop\3 курс\dash_project"
```

### 2) Создать виртуальное окружение

```powershell
python -m venv .venv
```

### 3) Активировать виртуальное окружение

```powershell
.\.venv\Scripts\Activate.ps1
```

Если видишь ошибку про `running scripts is disabled`, выполни для текущего окна PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 4) Установить зависимости

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5) Запустить веб-приложение

```powershell
python prilozhenie.py
```

После запуска открой в браузере:

- http://127.0.0.1:8050

## Пошаговый запуск (Linux/macOS)

```bash
cd /path/to/dash_project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python prilozhenie.py
```

## Запуск desktop-версии (Electron)

Запускается после того, как Python-часть проекта настроена.

```powershell
cd "C:\Users\tanya\Desktop\3 курс\dash_project\electron-app"
npm install
npm start
```

## Формат файла параметров

Пример:

```text
m = 10
h = 5
V = 20
T = 25
g = 9.81
C = 4200

```

## Как пользоваться приложением

1. Загрузить файл параметров (например, `param_config.txt`).
2. Настроить диапазоны и число интервалов.
3. Нажать `Сгенерировать серии`.
4. Нажать `Запустить расчеты`.
5. Смотреть лог выполнения, таблицу истории и графики.
6. При необходимости нажать `Сохранить результаты` для экспорта CSV.

## Технологии

- Backend: Python, Dash
- Frontend/графики: Plotly
- Desktop: Electron.js
- Хранение результатов: CSV

## Контакты

Лопатина Татьяна: `tanya.lopatina.05@list.ru`