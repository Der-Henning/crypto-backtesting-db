FROM python:3.10

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./src .

CMD [ "python","-u","runner.py" ]
