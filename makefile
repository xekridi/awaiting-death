.SILENT:

restart:
	docker compose restart

build:
	docker compose up -d --build

test:
	docker compose exec web pytest -q

migrate:
	docker compose run --rm web python manage.py makemigrations
	docker compose run --rm web python manage.py migrate