# pull official base image
FROM python:3.10.8-slim-buster

# set environment variables
ENV YOUR_ENV="dev" \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  DEBIAN_FRONTEND=noninteractive \ 
  PYTHON_VERSION=3.10.8 \
  POETRY_HOME=/opt/poetry \
  WORKDIR=/usr/src/app

# set working directory
WORKDIR $WORKDIR

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat git gcc curl build-essential pkg-config cmake postgresql libpq-dev wget xvfb \
  && apt-get clean

# -- install python dependencies
RUN pip install --upgrade pip
# install poetry
ENV PATH $POETRY_HOME/bin:$PATH
RUN curl -sSL https://install.python-poetry.org | POETRY_PREVIEW=1 python3 -

# # cache python requirements in docker layer
COPY pyproject.toml poetry.lock*  ./
# install libraries and create lock file
RUN poetry install $(test "$YOUR_ENV" == production && echo "--no-dev") --no-interaction --no-ansi
RUN poetry lock
# apply jupyter themes for notebook aesthetics
RUN poetry run jt -t chesterish -cellw 95%
RUN poetry run jupyter contrib nbextension install --user

# add local code
COPY . .

# install pre-commit hooks
RUN apt install -y git
#RUN poetry run pre-commit install
#RUN poetry run pre-commit install-hooks

CMD ["tail", "-f", "/dev/null"]
