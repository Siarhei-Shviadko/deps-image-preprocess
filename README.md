# DEPS Image Preprocess 

### Description
Service for image preprocessing (rotation, orientation, etc.)


## Requirements

* [Docker](https://www.docker.com/).
* [Docker Compose](https://docs.docker.com/compose/install/).
* [Poetry](https://python-poetry.org/) for Python package and environment management.


## Local development

### General workflow

By default, the dependencies are managed with [Poetry](https://python-poetry.org/), go there and install it.

You can install all the dependencies with:

```console
$ poetry install
```

Then you can start a shell session with the new environment with:

```console
$ poetry shell
```

Now you are ready to run project locally.

### Running tests

Before running tests, linters, etc. make sure that you've built docker image with dev dependencies.
For building it, run:
```console
docker-compose build image-preprocess
```
Then you can run commands from makefile

## Enabling/Disabling vault usage
You can enable or disable vault secret usage without modifying kubernetes yaml files. By default vault usage is set to false inside value.yaml file but we override this value with VAULT_ENABLE_DEV, VAULT_ENABLE_QA, VAULT_ENABLE_INS, VAULT_ENABLE_DEMO, VAULT_ENABLE_DS variables from Settings >> CI/CD for each environment. If you change variable value from Settings >> CI/CD you need to manually start new pipline from CI/CD >> Pipelines.

