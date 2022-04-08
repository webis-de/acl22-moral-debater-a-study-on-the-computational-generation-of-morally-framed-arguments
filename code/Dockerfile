ARG CUDA=nocuda
ARG PORT=8080
FROM anibali/pytorch:1.10.2-${CUDA}-ubuntu20.04

ADD debater_python_api /app/debater_python_api
ADD moral_debater_code /app/moral_debater_code
ADD moral_debater_server /app/moral_debater_server

USER root
RUN apt-get update -y && apt-get upgrade -y && apt-get install -y build-essential  && apt-get install -y gcc
RUN pip install --upgrade pip
RUN pip install /app/debater_python_api/.
RUN pip install /app/moral_debater_code/.
RUN pip install /app/moral_debater_server/.
RUN python3 -m spacy download en

USER ${uid}:${gid}
CMD waitress-serve --listen=0.0.0.0:$PORT --call 'moral_debater_api:create_app'
