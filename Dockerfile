FROM python:3-slim

RUN mkdir /uwsgi/
WORKDIR /uwsgi/
COPY . /uwsgi/
RUN mkdir /uwsgi/data/

RUN apt-get update && apt-get install -y gcc && pip install -r /rate-shoot/requirements.txt

EXPOSE 8000

RUN useradd uwsgi && chown -R uwsgi /uwsgi
USER uwsgi

VOLUME ["/uwsgi/data/"]

CMD [ "uwsgi", "uwsgi.ini"]
