.ONESHELL:
SHELL := /bin/bash
.SILENT:

all: build wait migrate test

info:
	kubectl get pods

start:
	minikube start --addons=ingress --memory=4g --cpus=2

build:
	eval $$(minikube docker-env); \
	docker build --no-cache -t default-web:latest .; \
	docker build --no-cache -f Dockerfile.worker -t default-worker:latest .; \
	$(MAKE) restart
	kubectl apply -R -f k8s/

restart:
	kubectl rollout restart deployment default-web
	kubectl rollout restart deployment default-worker

migrate:
	POD=$$(kubectl get pods -l app=default-web -o jsonpath='{.items[0].metadata.name}'); \
	kubectl exec -i $$POD -c default-web -- python manage.py makemigrations; \
	kubectl exec -i $$POD -c default-web -- python manage.py migrate

test:
	POD=$$(kubectl get pods -l app=default-web -o jsonpath='{.items[0].metadata.name}'); \
	kubectl exec -i $$POD -c default-web -- pytest -q -v

load:
	minikube image load default-web:latest
	minikube image load default-worker:latest

delete:
	minikube delete

wait:
	if ! kubectl rollout status deployment/default-web --timeout=60s; then
	  echo
	  echo "❌ Deployment default-web failed!"
	  echo "----- Describe pods for default-web -----"
	  kubectl describe pod -l app=default-web
	  echo
	  echo "----- Recent logs for default-web -----"
	  kubectl logs -l app=default-web --tail=50
	  exit 1
	fi

	if ! kubectl rollout status deployment/default-worker --timeout=60s; then
	  echo
	  echo "❌ Deployment default-worker failed!"
	  echo "----- Describe pods for default-worker -----"
	  kubectl describe pod -l app=default-worker
	  echo
	  echo "----- Recent logs for default-worker -----"
	  kubectl logs -l app=default-worker --tail=50
	  exit 1
	fi

.PHONY: all build restart wait migrate test delete info start
