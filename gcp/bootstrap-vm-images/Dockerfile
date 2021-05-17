FROM google/cloud-sdk:alpine

COPY bootstrap-vm-images.py /entrypoint.py

RUN chmod 0555 /entrypoint.py

ENTRYPOINT ["/entrypoint.py"]
