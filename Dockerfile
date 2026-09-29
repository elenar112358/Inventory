FROM python:3.11-alpine

WORKDIR /abs

COPY . .

RUN chmod +x docker/entrypoint.sh

ENTRYPOINT ["docker/entrypoint.sh"]