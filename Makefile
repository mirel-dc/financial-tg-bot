.PHONY: help install sync test coverage run clean bot docker-build docker-run docker-stop docker-up docker-down docker-logs

test:
	cd src && uv run pytest tests/ -v

run:
	@if [ -z "$(INPUT)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "Использование: make run INPUT=input.csv OUTPUT=output.xlsx"; \
		exit 1; \
	fi
	cd src && uv run tbank-convert -i $(INPUT) -o $(OUTPUT)

bot:
	cd src && uv run python tg_bot/main.py

all:
	make down
	make up

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

clean:
	cd src && rm -rf .pytest_cache/ .coverage htmlcov/ *.xlsx
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
