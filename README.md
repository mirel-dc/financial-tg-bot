# T-Bank CSV to XLSX Converter

CLI утилита для конвертации CSV выписок Т-Банка в XLSX формат с автоматической категоризацией.

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
# Показать доступные команды
make help

# Синхронизировать зависимости
make sync

# Запустить тесты
make test

# Запустить с покрытием
make coverage

# Конвертировать файл
make run INPUT=input.csv OUTPUT=output.xlsx
```

## Документация

Полная документация находится в [src/README.md](src/README.md).

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
- **uv** - быстрый менеджер пакетов и окружений
- **Click** - CLI интерфейс
- **OpenPyXL** - работа с XLSX
- **Pydantic** - валидация данных
- **PyYAML** - конфигурация

## Разработка

Проект полностью использует [uv](https://github.com/astral-sh/uv) для управления зависимостями и окружениями.

```bash
# Синхронизировать зависимости
cd src && uv sync --extra dev

# Запустить тесты
uv run pytest tests/ -v

# С покрытием
uv run pytest --cov=tbank_converter tests/

# Запустить CLI
uv run tbank-convert --help
```
