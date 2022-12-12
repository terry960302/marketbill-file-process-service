FROM ubuntu:latest
MAINTAINER Taewan Kim "terry960302@gmail.com"

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
  apt-get install -y --no-install-recommends tzdata g++ curl

# set language
RUN apt-get install -y apt-utils locales
RUN locale-gen ko_KR.UTF-8
ENV LC_ALL ko_KR.UTF-8

# install java
# : openjdk-8 은 jre 환경을 셋업할 뿐 jpype 라이브러리를 컴파일 할 수 없는 상태라 11로 다운받아야함
RUN apt-get install -y openjdk-11-jdk
RUN echo "JDK 11 install completed"

# install python
RUN apt-get install -y python3-pip python3-dev
RUN cd /usr/local/bin && \
  ln -s /usr/bin/python3 python && \
  ln -s /usr/bin/pip3 pip && \
  pip install --upgrade pip
RUN echo "Python3 install completed, and set python environment completed."

# apt clean
RUN apt-get clean && \
  rm -rf /var/lib/apt/lists/*

COPY . .

# install python package
RUN pip install -r requirements.txt
RUN echo "Python library installed"

# profile
ENV PROFILE=dev
# database
ENV DB_USER=marketbill
ENV DB_PW=marketbill1234!
ENV DB_NET=tcp
ENV DB_HOST=marketbill-db.ciegftzvpg1l.ap-northeast-2.rds.amazonaws.com
ENV DB_PORT=5432
ENV DB_NAME=dev-db

EXPOSE 8000

CMD ["uvicorn" ,"main:app", "--host", "0.0.0.0", "--port", "8000"]


