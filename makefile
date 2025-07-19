.SILENT:

restart:
	docker compose restart

build:
	docker compose up -d --build

test:
	docker compose exec web pytest -q
