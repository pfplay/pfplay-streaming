FROM python:3.11-slim as build-stage

WORKDIR /tmp

RUN pip install poetry poetry-plugin-export
COPY ./pyproject.toml ./poetry.lock* /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# 
FROM python:3.11-slim

ARG DIR_SERVICE=/opt/service

LABEL owner="pfplay-backend"
LABEL description="PFPlay-Streaming Python"
ENV ROLE pfplay-streaming

WORKDIR ${DIR_SERVICE}

COPY --from=build-stage /tmp/requirements.txt ${DIR_SERVICE}/requirements.txt
RUN pip install --no-cache-dir --upgrade -r ${DIR_SERVICE}/requirements.txt

COPY . ${DIR_SERVICE}

EXPOSE 9000

# Not leveraging bash script at the moment until we have useful booting logics
# ENTRYPOINT ["sh", "/opt/service/run.sh"]
CMD uvicorn app:app --host 0.0.0.0 --port 9000
