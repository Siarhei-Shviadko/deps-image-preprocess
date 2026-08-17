ARG REPOSITORY_URL=""
FROM ${REPOSITORY_URL:+$REPOSITORY_URL/base/}jitesoft/tesseract-ocr:5.5.2 AS tesseract-python-base

ENTRYPOINT []

ENV PIP_NO_CACHE_DIR=off \
    PYTHONUNBUFFERED=1 \
    LC_ALL=C \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_PATH=/opt/poetry \
    VENV_PATH=/app/.venv \
    PYTHONPATH="$PYTHONPATH:/app" \
    LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/lib" \
    TESSDATA_PREFIX="/usr/local/share/tessdata"
ENV PATH="$VENV_PATH/bin:$POETRY_PATH/bin:$PATH"

FROM tesseract-python-base AS base

USER root
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    wget \
    curl \
    build-essential \
    libcurl4-openssl-dev libssl-dev \
    libtesseract-dev \
    libleptonica-dev \
    software-properties-common gnupg && \
    ( python3.12 --version 2>/dev/null || ( \
        add-apt-repository -y ppa:deadsnakes/ppa && \
        apt-get update && \
        apt-get install --no-install-recommends -y python3.12 python3.12-venv python3.12-dev \
    ) ) && \
    python3.12 -m ensurepip --upgrade && \
    python3.12 -m pip install pip==21.2.4 && \
    curl -sSL https://install.python-poetry.org | POETRY_HOME=$POETRY_PATH POETRY_VERSION=1.8.3 python3.12 - && \
    poetry --version && \
    poetry config virtualenvs.in-project true && \
    rm -rf /var/lib/apt/lists/*

FROM base AS build-image-preprocess

WORKDIR /app/

# Get trained tessdata
RUN wget -O /usr/local/share/tessdata/eng.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata \
    && wget -O /usr/local/share/tessdata/osd.traineddata https://github.com/tesseract-ocr/tessdata_best/raw/main/osd.traineddata

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./src/pyproject.toml ./src/poetry.lock* /app/

# Allow installing dev dependencies to run tests
COPY ./vendors /vendors

RUN poetry env use python3.12 && \
    poetry install --no-interaction --no-ansi --no-root --only main && rm -rf ~/.cache/pypoetry/

FROM build-image-preprocess AS develop

RUN poetry install --no-interaction --no-ansi --no-root && rm -rf ~/.cache/pypoetry/

COPY ./src /app

ARG BUILD_HASH=
ARG BUILD_TAG=
ARG BUILD_DATE=

ENV SERVICE_INFO_HASH=$BUILD_HASH
ENV SERVICE_INFO_TAG=$BUILD_TAG
ENV SERVICE_INFO_DATE=$BUILD_DATE

CMD ["python", "deps_image_preprocess", "serve"]

FROM tesseract-python-base AS runtime

WORKDIR /app

USER root
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install --no-install-recommends -y software-properties-common gnupg && \
    ( python3.12 --version 2>/dev/null || ( \
        add-apt-repository -y ppa:deadsnakes/ppa && \
        apt-get update && \
        apt-get install --no-install-recommends -y python3.12 python3.12-venv \
    ) ) && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build-image-preprocess $VENV_PATH $VENV_PATH
COPY --from=build-image-preprocess /usr/local/share/tessdata /usr/local/share/tessdata

COPY ./vendors /vendors
COPY ./src /app

ARG BUILD_HASH=
ARG BUILD_TAG=
ARG BUILD_DATE=

ENV SERVICE_INFO_HASH=$BUILD_HASH
ENV SERVICE_INFO_TAG=$BUILD_TAG
ENV SERVICE_INFO_DATE=$BUILD_DATE

USER root
RUN useradd -Ms /bin/bash deps
USER deps

CMD ["python", "deps_image_preprocess", "serve"]
