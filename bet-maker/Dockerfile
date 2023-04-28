FROM python:3.10

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

# install system dependencies for postgres
RUN apt-get update \
    && apt-get -y install netcat gcc postgresql \
    && apt-get clean

# install requirements
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /code/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]