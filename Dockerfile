FROM python:3.11-slim

ARG DIR_SERVICE=/usr/services

LABEL owner="pfplay-backend"
LABEL description="PFPlay-Streaming Python"

WORKDIR ${DIR_SERVICE}

RUN pip install --upgrade pip

RUN pip install -U poetry==1.4.2

COPY . ${DIR_SERVICE}/

RUN poetry --version

RUN cd ${DIR_SERVICE}/

RUN poetry install 

EXPOSE 9000

CMD ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9000"]