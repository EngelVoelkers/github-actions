FROM google/cloud-sdk:alpine

COPY bootstrap-vm-images.sh /entrypoint.sh

RUN chmod 0555 /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
