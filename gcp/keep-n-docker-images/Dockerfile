FROM google/cloud-sdk:alpine

COPY keep-n-docker-images.sh /entrypoint.sh

RUN chmod 0555 /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
