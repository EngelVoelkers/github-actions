FROM google/cloud-sdk:alpine

COPY requirements.txt /requirements.txt

RUN apk add --no-cache py3-pip && \
    pip3 --no-cache-dir install -r ./requirements.txt && \
    rm -f -- /requirements.txt

COPY action.py /entrypoint

RUN chmod 0555 /entrypoint

ENTRYPOINT ["/entrypoint"]
