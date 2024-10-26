FROM python:3.10-slim-bookworm

WORKDIR /app

# Disable Poetry's virtual environment creation inside Docker
ENV POETRY_VIRTUALENVS_CREATE=false 

COPY ./pyproject.toml /app
COPY ./poetry.lock /app 

	
RUN pip install poetry
RUN poetry install


COPY . /app

CMD ["poetry", "run", "uvicorn", "views.main:app", "--host", "0.0.0.0", "--port", "8012", "--reload"]
