FROM alpine

RUN apk --no-cache add \
 curl \
 python

RUN curl -q https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
 && python get-pip.py

COPY requirements.txt /tmp/requirements.txt
WORKDIR /tmp
RUN pip install -r requirements.txt

COPY scripts /root/eiti_harvester

WORKDIR /root/eiti_harvester

CMD ./run_harvester.sh
