FROM google/cloud-sdk:alpine

RUN apk add --no-cache jq

COPY keep-n-docker-images.sh /entrypoint.sh

RUN chmod 0555 /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
