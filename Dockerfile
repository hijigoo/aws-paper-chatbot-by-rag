FROM python:3.9

WORKDIR /app

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN apt-get update
RUN apt-get install poppler-utils -y

COPY ./app /app

ENV PYTHONPATH "${PYTHONPATH}:/app"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]