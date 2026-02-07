# T-Bank CSV to XLSX Converter

CLI утилита для конвертации CSV выписок Т-Банка в XLSX формат с двойной записью для импорта в Google Sheets.

## Быстрый старт

```bash
# Установить uv (если еще не установлен)
curl -LsSf https://astral.sh/uv/install.sh | sh
# или на Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Клонировать репозиторий
cd FinancialBot

# Синхронизировать зависимости
cd src && uv sync --extra dev

# Запустить конвертер
uv run tbank-convert -i input.csv -o output.xlsx
```

## Использование с Makefile

```bash
make help       # Показать доступные команды
make sync       # Синхронизировать зависимости
make test       # Запустить тесты
make coverage   # Запустить с покрытием
make run INPUT=input.csv OUTPUT=output.xlsx  # Конвертировать файл
```

## Документация

Подробная документация — в [src/README.md](src/README.md).

## Структура проекта

```
FinancialBot/
├── src/
│   ├── tbank_converter/     # Основной пакет
│   ├── tests/               # Тесты
│   ├── configs/             # Конфигурация
│   ├── pyproject.toml       # Зависимости и настройки
│   └── README.md            # Подробная документация
├── Makefile                 # Команды для разработки
└── README.md                # Этот файл
```

## Технологии

- **Python 3.11+**
- **uv** — быстрый менеджер пакетов и окружений
- **Click** — CLI интерфейс
- **OpenPyXL** — работа с XLSX
- **Pydantic** — валидация конфигурации
- **PyYAML** — парсинг YAML конфигов

## Разработка

Проект полностью использует [uv](https://github.com/astral-sh/uv) для управления зависимостями и окружениями.

```bash
cd src && uv sync --extra dev   # Синхронизировать зависимости
uv run pytest tests/ -v          # Запустить тесты
uv run pytest --cov=tbank_converter tests/  # С покрытием
uv run tbank-convert --help      # Справка CLI
```

## Лицензия

MIT
