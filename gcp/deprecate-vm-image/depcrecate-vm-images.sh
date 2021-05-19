#!/usr/bin/env bash
set -e -u -o pipefail


logging() {
    echo "Deprecating Images: $1"
}


REPLACEMENT=${REPLACEMENT:-"$1"}
OS_FAMILY=${OS_FAMILY:-"$2"}
PROJECT=${PROJECT:-"$3"}
DELETE_IN=${DELETE_IN:-"$4"}


if [ "x${REPLACEMENT}" = "x" ]; then
    logging "No Image used as replacement given!"
    exit 1
fi


if [ "x${OS_FAMILY}" = "x" ]; then
    logging "No OS Family given!"
    exit 1
fi


if [ "x${PROJECT}" = "x" ]; then
    logging "No PROJECT given!"
    exit 1
fi


if [ "x$DELETE_IN" = "x" ]; then
    logging "No deletion time given, using 10d as default."
    DELETE_IN="10d"
fi


gcloud auth activate-service-account --key-file "${GOOGLE_APPLICATION_CREDENTIALS}"


readarray -t ALL_OS_FAMILY_IMAGES < <(gcloud --project "${PROJECT}" compute images list --filter="family~'${OS_FAMILY}'" --format='value(name)' --sort-by='~name')


if [ ${#ALL_OS_FAMILY_IMAGES[*]} -gt 1 ]; then
    for image in ${ALL_OS_FAMILY_IMAGES[*]}; do
        if [ ${image} != ${REPLACEMENT} ]; then
            gcloud --project ${PROJECT} compute images deprecate ${image} --replacement ${REPLACEMENT} --state DEPRECATED --delete-in ${DELETE_IN}
        fi
    done
fi


echo "::set-output name=deleted_images::$(( ${#ALL_OS_FAMILY_IMAGES[*]} - 1 ))"
