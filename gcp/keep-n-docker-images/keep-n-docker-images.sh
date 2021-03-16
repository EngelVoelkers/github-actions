#!/bin/bash

IMAGE=$1
MAX=$2

#echo "DEBUG: This is github home => $( ls -la /github/home )"
#echo "DEBUG: This is github workplace => $( ls -la /github/workplace )"
#echo "DEBUG: This is the content of GOOGLE_APPLICATION_CREDENTIALS => ${GOOGLE_APPLICATION_CREDENTIALS}"
#echo "DEBUG: Show 'ls' for GOOGLE_APPLICATION_CREDENTIALS => $(ls -la $GOOGLE_APPLICATION_CREDENTIALS) "
#echo "DEBUG: Show gcloud auth list => $(gcloud auth list)"
#echo "DEBUG: Show gcloud config list => $(gcloud config list)"


gcloud auth activate-service-account github-actions@gcp-workplace-dev.iam.gserviceaccount.com --key-file "${GOOGLE_APPLICATION_CREDENTIALS}"


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
