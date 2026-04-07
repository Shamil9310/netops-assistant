FROM python:3.14-slim

WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN pip install --upgrade pip && pip install -e .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
