FROM ubuntu:latest
MAINTAINER Taewan Kim "terry960302@gmail.com"

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
  apt-get install -y --no-install-recommends tzdata g++ curl

# set language
# : PDF 글자 깨짐 현상 방지 및 파일 export시 명칭 보존을 위함
RUN apt-get install -y apt-utils locales
RUN sed -i '/ko_KR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG=ko_KR.UTF-8 \
    LANGUAGE=ko_KR:ko \
    LC_ALL=ko_KR.UTF-8

# set fonts
# : aspose.cells API 에서 엑셀에서 사용하는 폰트를 찾으려하기 때문에 미리 셋업이 필요(폰트가 없으면 글자깨짐)
RUN apt-get install -y fonts-nanum

RUN apt-get --no-install-recommends install libreoffice -y
RUN apt-get install -y libreoffice-java-common
# install java
# : openjdk-8 은 jre 환경을 셋업할 뿐 jpype 라이브러리를 컴파일 할 수 없는 상태라 11로 다운받아야함
RUN apt-get install -y openjdk-11-jdk
RUN echo "JDK 11 install completed"

# install python
# : uvicorn과 같은 명령어 interpret 및 실행용
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
RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt
RUN echo "Python library installed"

# profile
ENV PROFILE=dev
# database
ENV DB_USER=marketbill \
    DB_PW=marketbill1234! \
    DB_NET=tcp \
    DB_HOST=marketbill-db.ciegftzvpg1l.ap-northeast-2.rds.amazonaws.com \
    DB_PORT=5432 \
    DB_NAME=dev-db

EXPOSE 8000

CMD ["uvicorn" ,"main:app", "--host", "0.0.0.0", "--port", "8000"]


