FROM google/cloud-sdk:alpine

COPY action.py /entrypoint

RUN chmod 0555 /entrypoint

ENTRYPOINT ["/entrypoint"]
