# pull official base image
FROM python:3.9.5-slim-buster

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
  PYTHON_VERSION=3.9.5 \
  POETRY_HOME=/opt/poetry \
  WORKDIR=/usr/src/app

# set working directory
WORKDIR $WORKDIR

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc curl postgresql libpq-dev wget xvfb \
  && apt-get clean

# chrome for chatgpt api 
RUN DEBIAN_FRONTEND=noninteractive && \
  wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub > /usr/share/keyrings/chrome.pub && \
  echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/chrome.pub] http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list && \
  apt update -y && \
  apt install -y google-chrome-stable

# -- install python dependencies

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
