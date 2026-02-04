.PHONY: help install sync test coverage run clean

help:
	@echo "Доступные команды:"
	@echo "  make install    - Установить uv (если не установлен)"
	@echo "  make sync       - Синхронизировать зависимости"
	@echo "  make test       - Запустить тесты"
	@echo "  make coverage   - Запустить тесты с покрытием"
	@echo "  make run        - Запустить конвертер (требуется INPUT и OUTPUT)"
	@echo "  make clean      - Очистить временные файлы"

install:
	@echo "Установка uv..."
	@powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

sync:
	cd src && uv sync --extra dev

test:
	cd src && uv run pytest tests/ -v

coverage:
	cd src && uv run pytest --cov=tbank_converter tests/

run:
	@if [ -z "$(INPUT)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "Использование: make run INPUT=input.csv OUTPUT=output.xlsx"; \
		exit 1; \
	fi
	cd src && uv run tbank-convert -i $(INPUT) -o $(OUTPUT)

clean:
	cd src && rm -rf .pytest_cache/ .coverage htmlcov/ *.xlsx
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
