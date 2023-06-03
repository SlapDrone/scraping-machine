# pull official base image
FROM mcr.microsoft.com/playwright/python:v1.32.0-focal 

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
  PYTHON_VERSION=3.8.10 \
  POETRY_HOME=/opt/poetry \
  WORKDIR=/usr/src/app

# set working directory
WORKDIR $WORKDIR

# install system dependencies
RUN apt-get update \
  && apt-get -y --fix-missing install build-essential netcat gcc curl postgresql libpq-dev libssl-dev \
  && apt-get clean

# # -- install python dependencies

# install poetry
ENV PATH $POETRY_HOME/bin:$PATH
#CMD ["tail", "-f", "/dev/null"]
RUN curl -sSL https://install.python-poetry.org | POETRY_PREVIEW=1 python -

# # cache python requirements in docker layer
COPY pyproject.toml poetry.lock*  ./
# install libraries and create lock file
RUN poetry install $(test "$YOUR_ENV" == production && echo "--no-dev") --no-interaction --no-ansi
RUN poetry lock

# install playwright
#RUN apt-get update
RUN poetry run playwright install
# add local code
COPY . .


# add entrypoint.sh
COPY ./entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
