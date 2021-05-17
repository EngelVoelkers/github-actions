#!/usr/bin/env bash
set -x -e -u -o pipefail



logging() {
    echo "Bootstrap Images: $1"
}


TIMESTAMP="$(date +%s)-${RANDOM}"
SCOPES=${SCOPES:-""}
ZONE=${ZONE:-""}
MACHINE_TYPE=${MACHINE_TYPE:-""}
TAGS=${TAGS:-""}
NETWORK=${NETWORK:-""}
SUBNETWORK=${SUBNETWORK:-""}
IMAGE_NAME=${IMAGE_NAME:-""}
PROJECT=${PROJECT:-""}
LABELS=${LABELS:-""}
DRY_RUN=${DRY_RUN:-0}
SCRIPT=${SCRIPT:-""}
BRANCH=${BRANCH:-""}
FROM_IMAGE=${FROM_IMAGE:-"debian-10"}
FROM_IMAGE_PROJECT=${FROM_IMAGE_PROJECT:-"debian-cloud"}
OS_FAMILY=${OS_FAMILY:-""}
SUBST_SCRIPT=$(mktemp)
SCRIPT_ENVS=${SCRIPT_ENVS:-""}

usage() {
    echo "Usage: $0 [-h | --help ]  [-t TAGS] [-s SCOPES] [-l LABELS] [-f FROM_IMAGE] [-g FROM_IMAGE_PROJECT] [-d] -i IMAGE_NAME -z ZONE -n NETWORK -m MACHINE_TYPE -u SUBNETWORK -e SCRIPT -p PROJECT -o OS_FAMILY

    $0 can also be executed with the appropriate ENV Variables. For example:

    PROJECT=gcp-workplace-dev INSTANCE=test-instance SCRIPT=/path/to/script $0

    Optional Arguments:
        -i  IMAGE_NAME (the image name to use.) *REQUIRED*
        -z  ZONE *REQUIRED*
        -n  NETWORK *REQUIRED*
        -m  MACHINE_TYPE *REQUIRED*
        -u  SUBNETWORK *REQUIRED*
        -t  TAGS (comma delimited list.) *OPTIONAL*
        -p  PROJECT *REQUIRED*
        -s  SCOPES (comma delimited list.) *OPTIONAL*
        -l  LABELS (comma delimited list of key=value pairs.) *OPTIONAL*
        -f  FROM_IMAGE (the base image you want to fork from. Default: '${FROM_IMAGE}') *OPTIONAL*
        -g  FROM_IMAGE_PROJECT (the project where the base image is located. Default: '${FROM_IMAGE_PROJECT}'). *OPTIONAL*
        -e  SCRIPT (http path to the bootstrap script file) *REQUIRED*
        -v  VARIABLES (define comma delimited key=value pairs that gets exported to the script as environment variables.) *OPTIONAL*
        -o  OS_FAMILY (the os family used to store the new image) *REQUIRED*
        -d  Set this to make a dry run where no changes are made. Use 'DRY_RUN=1' as ENV Variable. *OPTIONAL*
    "
}


while getopts ":i:z:n:m:u:t:p:s:l:f:g:e:v:o:d" arg; do
    case $arg in
        p)
            PROJECT=${OPTARG}
            ;;
        s)
            SCOPES=${OPTARG}
            ;;
        i)
            IMAGE_NAME=${OPTARG}
            ;;
        z)
            ZONE=${OPTARG}
            ;;
        n)
            NETWORK=${OPTARG}
            ;;
        m)
            MACHINE_TYPE=${OPTARG}
            ;;
        u)
            SUBNETWORK=${OPTARG}
            ;;
        t)
            TAGS=${OPTARG}
            ;;
        l)
            LABELS=${OPTARG}
            ;;
        f)
            FROM_IMAGE=${OPTARG}
            ;;
        g)
            FROM_IMAGE_PROJECT=${OPTARG}
            ;;
        d)
            DRY_RUN=1
            ;;
        e)
            SCRIPT=${OPTARG}
            ;;
        v)
            IFS=',' read -ra SCRIPT_ENVS <<< "${OPTARG}"
            ;;
        o)
            OS_FAMILY=${OPTARG}
            ;;
        *)
            usage
            exit 0
            ;;
    esac
done
shift $((OPTIND-1))


declare -A REQUIRED_ARGS=( \
    [IMAGE_NAME]=${IMAGE_NAME} \
    [ZONE]=${ZONE} \
    [NETWORK]=${NETWORK} \
    [MACHINE_TYPE]=${MACHINE_TYPE} \
    [SUBNETWORK]=${SUBNETWORK} \
    [SCRIPT]=${SCRIPT} \
    [PROJECT]=${PROJECT} \
    [OS_FAMILY]=${OS_FAMILY} \
)


for key in ${!REQUIRED_ARGS[*]}; do
    if [ "x${REQUIRED_ARGS[$key]}" = "x" ]; then
        logging "You must set the ${key} Argument."
    fi
done


IMAGE_NAME=$(tr "[:upper:]" "[:lower:]" <<< "${IMAGE_NAME}-${TIMESTAMP}")


if [ "x${TAGS}" = "x" ]; then
    TAGS="${IMAGE_NAME}"
else
    TAGS="${TAGS},${IMAGE_NAME}"
fi


declare -a CMD_CREATE_INSTANCE=( \
    gcloud compute instances create "${IMAGE_NAME}" \
        --boot-disk-device-name "${IMAGE_NAME}" \
        --image-family "${FROM_IMAGE}" \
        --image-project "${FROM_IMAGE_PROJECT}" \
        --project "${PROJECT}" \
        --zone "${ZONE}" \
        --machine-type "${MACHINE_TYPE}"  \
        --network "${NETWORK}" \
        --subnet "${SUBNETWORK}" \
)


declare -A OPTIONAL_ARGS=( \
    [--tags]="${TAGS}" \
    [--scopes]="${SCOPES}" \
    [--labels]="${LABELS}" \
)


for key in ${!OPTIONAL_ARGS[*]}; do
    if [ ! "x${OPTIONAL_ARGS[$key]}" = "x" ]; then
        CMD_CREATE_INSTANCE+=( "${key} \"${OPTIONAL_ARGS[$key]}\"" )
    fi
done


declare -a CMD_DOWNLOAD_SCRIPT=( \
    curl -sSLf "${SCRIPT}" -o "${SUBST_SCRIPT}"
)


#declare -a CMD_ADD_FIREWALL_RULE=( \
#    gcloud compute firewall-rules create "${IMAGE_NAME}" \
#        --project "${PROJECT}" \
#        --target-tags "${IMAGE_NAME}" \
#        --direction INGRESS \
#        --allow=tcp:22 \
#        --network "${NETWORK}" \
#)


#declare -a CMD_DELETE_FIREWALL_RULE=( \
#    gcloud -q compute firewall-rules delete "${IMAGE_NAME}" \
#        --project "${PROJECT}" \
#)


declare -a CMD_STOP_INSTANCE=( \
    gcloud compute instances stop "${IMAGE_NAME}" \
        --project "${PROJECT}" \
        --zone "${ZONE}" \
)


declare -a CMD_CREATE_IMAGE=( \
    gcloud compute images create "${IMAGE_NAME}" \
        --source-disk "${IMAGE_NAME}" \
        --source-disk-zone "${ZONE}" \
        --family "${OS_FAMILY}" \
)


declare -a CMD_DELETE_INSTANCE=( \
    gcloud -q compute instances delete "${IMAGE_NAME}" \
        --zone "${ZONE}" \
        --project "${PROJECT}" \
        --delete-disks all \
)


SSH_KEY_VALIDITY="10m"

declare -a CMD_COPY_SCRIPT=( \
    gcloud compute scp --zone "${ZONE}" \
        --project "${PROJECT}" \
        --ssh-key-expire-after="${SSH_KEY_VALIDITY}" \
        "${SUBST_SCRIPT}" \
        bootstrapper@"${IMAGE_NAME}":bootstrap.sh \
)


declare  -a CMD_CHMOD_CMD=( \
    gcloud compute ssh bootstrapper@"${IMAGE_NAME}" \
        --zone "${ZONE}" \
        --project "${PROJECT}" \
        --ssh-key-expire-after="${SSH_KEY_VALIDITY}" \
        --command "\"chmod 0750 ./bootstrap.sh\"" \
)


declare -a CMD_SUDO_CMD=( \
    gcloud compute ssh bootstrapper@"${IMAGE_NAME}" \
        --zone "${ZONE}" \
        --project "${PROJECT}" \
        --ssh-key-expire-after="${SSH_KEY_VALIDITY}" \
        --command "\"export ${SCRIPT_ENVS[*]}; sudo -E ./bootstrap.sh\"" \
)


declare -a CMD_RM_CMD=( \
    gcloud compute ssh bootstrapper@"${IMAGE_NAME}" \
        --zone "${ZONE}" \
        --project "${PROJECT}" \
        --ssh-key-expire-after="${SSH_KEY_VALIDITY}" \
        --command "\"rm -f -- ./bootstrap.sh\"" \
)


declare -a COMMANDS=( \
    "${CMD_DOWNLOAD_SCRIPT[*]}" \
    #"${CMD_ADD_FIREWALL_RULE[*]}" \
    "${CMD_CREATE_INSTANCE[*]}" \
    "${CMD_COPY_SCRIPT[*]}" \
    "${CMD_CHMOD_CMD[*]}" \
    "${CMD_SUDO_CMD[*]}" \
    "${CMD_RM_CMD[*]}" \
    "${CMD_CREATE_IMAGE[*]}" \
    "${CMD_STOP_INSTANCE[*]}" \
    "${CMD_DELETE_INSTANCE[*]}" \
    #"${CMD_DELETE_FIREWALL_RULE[*]}" \
)


echo "Commands to execute:"
echo "==================="


for key in ${!COMMANDS[*]}; do
    echo "${COMMANDS[$key]}"
    echo
done


if [ ${DRY_RUN} -eq 1 ]; then
    echo "Dry run: No changes are made!"
    exit 0
fi


gcloud auth activate-service-account --key-file "${GOOGLE_APPLICATION_CREDENTIALS}"


for key in ${!COMMANDS[*]}; do
    bash -c "${COMMANDS[$key]}"
    echo
done
