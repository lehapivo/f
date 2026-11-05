FROM python:3.12-slim
WORKDIR /code

# зеркало PyPI задается только при локальной сборке без доступа в интернет
ARG PIP_INDEX_URL
ARG PIP_TRUSTED_HOST
COPY ./requirements.txt /code/
RUN pip install --no-cache-dir -r /code/requirements.txt

COPY ./app /code/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
