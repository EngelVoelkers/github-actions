#!/bin/bash

IMAGE=$1
MAX=$2

read -r -d " " -a output <<< "$(gcloud container images list-tags "$IMAGE" --format="value(TAGS)")"
echo "Found ${#output[@]} Images of ${IMAGE} in the registry ..."
if [[ ${#output[@]} -gt ${MAX} ]]; then
    images_to_delete=$(( ${#output[@]} - "${MAX}" ))
    echo "Need to delete ${images_to_delete} Images."
    echo "${output[@]:MAX}" | while read -r -d " " TAG || [ -n "$TAG" ]; do
        gcloud -q container images delete "${IMAGE}":"${TAG}" --force-delete-tags
        echo -ne "Deleted Image ${IMAGE}:${TAG}. "
    done
else
    echo "No need to delete images."
    images_to_delete=0
fi

echo "::set-output name=deleted_images::${images_to_delete}"

exit 0
