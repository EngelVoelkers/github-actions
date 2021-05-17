FROM google/cloud-sdk:alpine

RUN pip3 --no-cache-dir install -r requirements.txt

COPY bootstrap-vm-images.py /entrypoint.py

RUN chmod 0555 /entrypoint.py

ENTRYPOINT ["/entrypoint.py"]
