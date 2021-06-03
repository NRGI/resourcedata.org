from python:2.7

COPY requirements.txt /tmp/requirements.txt
WORKDIR /tmp
RUN pip install -r requirements.txt

COPY scripts /root/eiti_harvester

WORKDIR /root/eiti_harvester

CMD ./run_harvester.sh
