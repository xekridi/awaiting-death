.SILENT:

all: build test

restart:
	docker compose restart

build:
	docker compose up -d --build

test:
	docker compose exec web pytest -q -v

migrate:
	docker compose run --rm web python manage.py makemigrations
	docker compose run --rm web python manage.py migrate

kube:
	minikube start --addons=ingress --memory=4g --cpus=2
	eval $(minikube docker-env)
	docker build -f Dockerfile.worker -t default-worker:latest .
	docker build -t default-web:latest .
	kubectl apply -f k8s/django-secret.yaml
	kubectl apply -f k8s/web-config.yaml
	kubectl apply -f k8s/redis.yaml
	kubectl apply -f k8s/ingress.yaml
	kubectl apply -f k8s/postgres.yaml
	kubectl apply -f k8s/web.yaml
	kubectl apply -f k8s/worker.yaml
	kubectl rollout restart deployment default-web
	kubectl rollout restart deployment default-worker
	kubectl get pods
