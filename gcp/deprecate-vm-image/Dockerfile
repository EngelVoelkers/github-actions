FROM google/cloud-sdk:alpine

COPY deprecate-vm-images.sh /entrypoint.sh

RUN chmod 0555 /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
