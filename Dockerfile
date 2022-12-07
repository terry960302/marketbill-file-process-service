FROM public.ecr.aws/lambda/python:3.8
MAINTAINER Taewan Kim "terry960302@gmail.com"

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

# profile
ENV PROFILE=prod
# database
ENV DB_USER=marketbill
ENV DB_PW=marketbill1234!
ENV DB_NET=tcp
ENV DB_HOST=marketbill-db.ciegftzvpg1l.ap-northeast-2.rds.amazonaws.com
ENV DB_PORT=5432
ENV DB_NAME=prod-db

CMD ["main.lambda_handler"]

