-include .env
-include vendors/deps-pipelines/shared/Makefile
-include Makefile.local

CURRENT_UID := $(shell id -u):$(shell id -g)
HASH := $(shell git rev-parse HEAD)
DATE := $(shell date)
TAG = $(shell git describe || echo "latest")
commit_short_sha := "$(CI_COMMIT_SHORT_SHA)"

APP_NAME=image-preprocess
NO_DEV_DOCKER_IMAGE = $(APP_NAME)
DEV_DOCKER_IMAGE = image-preprocess-dev

.PHONY: config
## Show current docker compose config
config:
	docker compose -f docker-compose.yml config

.PHONY: config-test
## Show docker compose test config
config-test:
	docker compose -f docker-compose.yml -f docker-compose.test.yml config

.PHONY: install
## Install default environment settings
install:
	cp .env.example .env

.PHONY: login
## Login in docker registry
login:
	docker login $(repository)

.PHONY: prereq
prereq:
	test -f .env || echo >> .env
	docker network create deps-network || true

.PHONY: prereq-tests
prereq-tests: | prereq
	docker compose -f docker-compose.yml -f docker-compose.test.yml down -v

.PHONY: run
## Run service
run: | prereq
	docker compose up -d

.PHONY: logs
## Open service logs
logs:
	docker compose logs -f

.PHONY: status
## Get running status information
status:
	docker compose ps

.PHONY: stop
## Stop runned services
stop:
	docker compose stop

.PHONY: build
## Build containers
build:
	docker compose build \
	--build-arg BUILD_HASH=$(HASH) \
	--build-arg BUILD_TAG=$(TAG) \
	--build-arg BUILD_DATE="$(DATE)"

.PHONY: migrate
## Apply database migrations
migrate:
	docker compose run --rm migrator update

.PHONY: shell-app
## Open shell in container
shell-app:
	docker compose exec -u "$(CURRENT_UID)" $(APP_NAME) /bin/sh


.PHONY: format
## Apply black & isort code formatting
format:
	docker compose run --rm --no-deps -u "$(CURRENT_UID)" $(APP_NAME) black --config pyproject.toml .
	docker compose run --rm --no-deps -u "$(CURRENT_UID)" $(APP_NAME) isort --settings-path /app/setup.cfg .

.PHONY: format-check
## Check for correct code format
format-check:
	docker compose run --rm --no-deps -u "$(CURRENT_UID)" $(APP_NAME) black --config pyproject.toml --check .
	docker compose run --rm --no-deps -u "$(CURRENT_UID)" $(APP_NAME) isort --settings-path /app/setup.cfg --check-only .

.PHONY: lint
## Check code using linters
lint:
	docker compose run --rm --no-deps $(APP_NAME) flake8 .

.PHONY: mypy
## Check code using mypy
mypy:
	docker compose run --rm --no-deps $(APP_NAME) mypy .

.PHONY: tests-unit
## Run unit tests
tests-unit:
	docker compose -f docker-compose.yml -f docker-compose.test.yml run --user="root" --rm --no-deps $(APP_NAME) coverage run -a -m pytest -vv -x tests/unit

.PHONY: tests-integration
## Run integration tests
tests-integration:
	docker compose -f docker-compose.yml -f docker-compose.test.yml rm -f
	docker compose -f docker-compose.yml -f docker-compose.test.yml run --user="root" --rm $(APP_NAME) coverage run -a -m pytest -vv -x tests/integration
	docker compose -f docker-compose.yml -f docker-compose.test.yml rm -f

.PHONY: tests
## Run unit & integration tests
tests: | tests-unit tests-integration
	docker compose -f docker-compose.yml -f docker-compose.test.yml rm -f
	docker compose -f docker-compose.yml -f docker-compose.test.yml run --user="root" --rm $(APP_NAME) coverage run -a -m pytest -vv -x --junitxml=junit-report.xml tests
	docker compose -f docker-compose.yml -f docker-compose.test.yml rm -f

.PHONY: coverage
## Get code coverage report
coverage:
	docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm $(APP_NAME) coverage report -i --rcfile=/app/setup.cfg

coverage-xml:
	docker compose -f docker-compose.yml -f docker-compose.test.yml run --user="root" --rm $(APP_NAME) coverage xml -i --rcfile=/app/setup.cfg -o /app/tests/coverage.xml

.PHONY: ci
## Run CI checks
ci: | prereq-tests format-check lint mypy tests coverage prereq-tests
	@if [ "$(version)" = "ci" ]; then \
		make coverage-xml;\
	else \
	  	make requirements-lock; \
	fi

.PHONY: build-prod
## Build images for production
build-prod:
	# database build if required
	$(call build_service,$(DEV_DOCKER_IMAGE),./etc/deps-image-preprocess/Dockerfile,,develop)
	$(call build_service,$(NO_DEV_DOCKER_IMAGE),./etc/deps-image-preprocess/Dockerfile,,,$(DEV_DOCKER_IMAGE))

.PHONY: push
## Push images to registry
push:
	$(call push_service,$(DEV_DOCKER_IMAGE))
	$(call push_service,$(NO_DEV_DOCKER_IMAGE))

.PHONY: deliver
## Build prod images and push to registry
deliver: | build-prod push

.PHONY: tag
## Retag built services
tag:
	$(call tag_service,$(DEV_DOCKER_IMAGE))
	$(call tag_service,$(NO_DEV_DOCKER_IMAGE))

.PHONY: pull
## Pull service images from docker registry
pull:
	$(call pull_service,$(DEV_DOCKER_IMAGE))
	$(call pull_service,$(NO_DEV_DOCKER_IMAGE))

.PHONY: helm-upgrade-service
helm-upgrade-service:
	helm upgrade --install $(CI_PROJECT_NAME) .helm/services \
        --values .helm/services/values.yaml $(ADDITIONAL_VALUES) \
        --set registry=$(REPOSITORY_URL) \
        --set image_preprocess.image.tag=$(commit_short_sha) \
        --set image_preprocess_consumer.image.tag=$(commit_short_sha) \
        --set vault_settings.enabled=$(VAULT_ENABLE) \
        --timeout 300s \
        --atomic \
        --wait \
        --debug \
        --namespace $(NAMESPACE)

.PHONY: helm-upgrade
helm-upgrade:
	make helm-upgrade-service

.PHONY: helm-deployment-rollback
helm-deployment-rollback:
	helm rollback --namespace $(NAMESPACE) $(CI_PROJECT_NAME) 0

.PHONY: helm-rollback
helm-rollback:
	make helm-deployment-rollback

.PHONY: build-no-dev
build-no-dev:
	$(call build_service,$(NO_DEV_DOCKER_IMAGE),./etc/deps-image-preprocess/Dockerfile,,build-image-preprocess,$(DEV_DOCKER_IMAGE))
