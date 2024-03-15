FROM python:3.8

RUN apt-get -y update \
    && apt-get -y install \
    postgresql

# Download and install dockerize.
ENV DOCKERIZE_VERSION v0.6.1
RUN wget --no-verbose https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

# Set PYTHONUNBUFFERED so output is displayed in the Docker log
ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.6.1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=200 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /usr/src/app

# Poetry commands reference https://python-poetry.org/docs/cli/#run
COPY pyproject.toml poetry.lock ./
RUN pip install --upgrade pip \
    && pip install poetry==$POETRY_VERSION \
    && poetry export --without-hashes -f requirements.txt -o requirements.txt \
    && poetry export --dev --without-hashes -f requirements.txt -o requirements-dev.txt \
    && pip install -r requirements-dev.txt

# install sentence-transformers model for similarity search
RUN python -c 'from sentence_transformers import SentenceTransformer; model = SentenceTransformer("paraphrase-MiniLM-L3-v2"); model.save(".models")'
