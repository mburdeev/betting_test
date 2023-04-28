FROM python:3.10

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

# install requirements
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /code/

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]