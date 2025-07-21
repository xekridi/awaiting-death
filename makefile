.SILENT:

all: migrate test

kube:
	minikube start --addons=ingress --memory=4g --cpus=2
	eval $$(minikube docker-env)
	docker build -f Dockerfile.worker  -t default-worker:latest .
	docker build -t default-web:latest .
	kubectl apply -f k8s/django-secret.yaml
	kubectl apply -f k8s/web-config.yaml
	kubectl apply -f k8s/redis.yaml
	kubectl apply -f k8s/ingress.yaml
	kubectl apply -f k8s/postgres.yaml
	kubectl apply -f k8s/web.yaml
	kubectl apply -f k8s/worker.yaml
	$(MAKE) restart
	kubectl get pods

restart:
	kubectl rollout restart deployment default-web
	kubectl rollout restart deployment default-worker
	kubectl get pods

migrate:
	kubectl rollout status deployment/default-web
	@POD=$$(kubectl get pods -l app=default-web -o jsonpath='{.items[0].metadata.name}')
	@echo "=== Running makemigrations/migrate in $$POD ==="
	kubectl exec -it $$POD -- python manage.py makemigrations
	kubectl exec -it $$POD -- python manage.py migrate

test:
	kubectl rollout status deployment/default-web
	@POD=$$(kubectl get pods -l app=default-web -o jsonpath='{.items[0].metadata.name}')
	kubectl exec -it $$POD -- pytest -q -v

.PHONY: all kube restart migrate test
