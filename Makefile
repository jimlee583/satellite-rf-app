.PHONY: install dev-backend dev-frontend dev test build-backend deploy-backend build-frontend deploy-frontend deploy

# GCP / Firebase defaults — override on the command line if needed.
# Example: make build-backend TAG=v2 PROJECT_ID=my-project
PROJECT_ID ?= satellite-rf-app
REGION ?= us-west4
REPO ?= satellite-rf-backend
IMAGE ?= satellite-rf-backend
SERVICE ?= satellite-rf-backend
TAG ?= latest
REGISTRY := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPO)/$(IMAGE)

install:
	cd backend && uv sync
	cd frontend && npm install

dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8123

dev-frontend:
	cd frontend && npm run dev

dev:
	./dev.sh

test:
	cd backend && uv run pytest

build-backend:
	docker buildx build --platform linux/amd64 \
		-f backend/Dockerfile backend \
		-t $(REGISTRY):$(TAG) \
		--push

deploy-backend:
	gcloud run deploy $(SERVICE) \
		--image $(REGISTRY):$(TAG) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--project $(PROJECT_ID)

build-frontend:
	cd frontend && npm run build

deploy-frontend:
	cd frontend && npm run deploy

deploy: build-backend deploy-backend deploy-frontend
