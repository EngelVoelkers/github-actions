FROM google/cloud-sdk:alpine

COPY deprecate-vm-images.py /entrypoint

RUN chmod 0555 /entrypoint

ENTRYPOINT ["/entrypoint"]
