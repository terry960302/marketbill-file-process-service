FROM public.ecr.aws/docker/library/python:3.9.16-slim

COPY . /app
WORKDIR app

RUN pip install -r requirements.txt

# profile
ENV PROFILE=prod
# database
ENV DB_USER=marketbill \
    DB_PW=marketbill1234! \
    DB_NET=tcp \
    DB_HOST=marketbill-db.ciegftzvpg1l.ap-northeast-2.rds.amazonaws.com \
    DB_PORT=5432 \
    DB_NAME=prod-db

EXPOSE 8000

CMD ["uvicorn" ,"main:app", "--host", "0.0.0.0", "--port", "8000"]


