#!/usr/bin/env python3
# -*- coding 'utf8' -*-

__author__ = 'Robin Wittler'
__contact__ = 'robin.wittler@engelvoelkers.com'
__version__ = '0.0.1'


import os
import sys
import requests
import tempfile
import subprocess
from argparse import ArgumentParser


def download_script(args):
    request = requests.get(args.script)
    with open(args.destination, 'w') as fh:
        fh.write(request.content.decode('utf8'))


def prepare_gcloud_auth_cmd(args):
    credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', None)
    if credentials is None:
        raise EnvironmentError('Can not find GOOGLE_APPLICATION_CREDENTIALS')

    cmd = [
        f'gcloud auth activate-service-account',
        f'--key-file {credentials}'
    ]

    return cmd

def prepare_create_instance_cmd(args):
    cmd = [
        f'gcloud compute instance create {args.image_name}',
        f'--boot-disk-device-name {args.image_name}',
        f'--image-family {args.from_image}',
        f'--image-project {args.from_image_project}',
        f'--project {args.project}',
        f'--zone {args.zone}',
        f'--machine-type {args.machine_type}',
        f'--network {args.network}',
        f'--subnet {args.sub_network}'
    ]

    if args.tags:
        cmd.append(f'--tags {args.tags}')

    if args.scopes:
        cmd.append(f'--scopes {args.scopes}')

    if args.labels:
        cmd.append(f'--labels {args.labels}')

    return cmd


def prepare_delete_instance_cmd(args):
    cmd = [
        f'gcloud -q compute instances delete {args.image_name}',
        f'--zone {args.zone}',
        f'--project {args.project}',
        '--delete-disks all'
    ]

    return cmd


def prepare_scp_copy_cmd(args, src):
    cmd = [
        f'gcloud compute scp',
        f'--zone {args.zone}',
        f'--project {args.project}',
        f'--ssh-key-expire-after={args.ssh_key_expire}',
        f'{src}',
        f'bootstrapper@{args.image_name}:bootstrap.sh'
    ]

    return cmd


def prepare_chmod_cmd(args):
    cmd = [
        f'gcloud compute ssh bootstrapper@{args.image_name}',
        f'--zone {args.zone}',
        f'--project {args.project}',
        f'--ssh-key-expire-after={args.ssh_key_expire}',
        f'--command "chmod 0750 ./bootstrap.sh"'
    ]

    return cmd


def prepare_sudo_cmd(args):
    cmd = [
        f'gcloud compute ssh bootstrappe@{args.image_name}',
        f'--zone {args.zone}',
        f'--project {args.project}',
        f'--ssh-key-expire-after={args.ssh_key_expire}',
    ]

    if args.variables:
        variables = f'export {args.variables};'
    else:
        variables = ''

    cmd.append(f'--command "{variables}sudo -E ./bootstrap.sh"')

    return cmd


def prepare_rm_cmd(args):
    cmd = [
        f'gcloud compute ssh bootstrappe@{args.image_name}',
        f'--zone {args.zone}',
        f'--project {args.project}',
        f'--ssh-key-expire-after={args.ssh_key_expire}',
        f'--command "rm -f -- ./bootstrap.sh"'
    ]

    return cmd


def compose(args):
    fd, destination = tempfile.mkstemp()
    args.destination = destination
    try:
        ALL_PREPARED_CMDS = [
            prepare_gcloud_auth_cmd(args),
            prepare_create_instance_cmd(args),
            prepare_scp_copy_cmd(args, destination),
            prepare_chmod_cmd(args),
            prepare_sudo_cmd(args),
            prepare_rm_cmd(args),
            prepare_delete_instance_cmd(args)
        ]

        print(f'Download {args.script} to {args.destination}')
        if args.dry_run is False:
            download_script(args)

        for cmd in ALL_PREPARED_CMDS:
            print(' '.join(cmd))
            if args.dry_run is False:
                print(subprocess.check_output(cmd))
    except subprocess.CalledProcessError as error:
        print(error)
        sys.exit(1)

    finally:
        os.unlink(destination)


def getopts():
    parser = ArgumentParser()

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    parser.add_argument(
        '-t',
        '--tags',
        help='Comma delimited list of network tags.',
        required=False
    )

    parser.add_argument(
        '-s',
        '--scopes',
        help='Comma delimited list of GCP scopes to use for the bootstrap vm.',
        required=False
    )

    parser.add_argument(
        '-l',
        '--labels',
        help='Comma delimeted list of key=value pairs.',
        required=False
    )

    parser.add_argument(
        '-f',
        '--from-image',
        help='The base image you want to fork from. Default: %(default)s',
        default='debian-10',
        required=False
    )

    parser.add_argument(
        '-g',
        '--from-image-project',
        default='debian-cloud',
        help='The project the base image is located. Default: %(default)s',
    )

    parser.add_argument(
        '-v',
        '--variables',
        help=(
            'Comma delimited key=value pairs that could be used within '
            'the script file.'
        ),
        metavar='VARIABLES',
        default='',
        required=False,
    )

    parser.add_argument(
        '--ssh-key-expire',
        default='10m',
        help='The time the used ssh key will expire. Default: %(default)s',
        required=False,
    )

    parser.add_argument(
        '-d',
        '--dry-run',
        action='store_true',
        default=False,
        help=(
            'Set this to make a dry run without any changes. '
            'Default: %(default)s'
        ),
        required=False,
    )

    required_group = parser.add_argument_group(title='required arguments')

    required_group.add_argument(
        '-i',
        '--image-name',
        help='The name of the resulting image.',
        required=True
    )

    required_group.add_argument(
        '-z',
        '--zone',
        help='The GCP Zone ID.',
        required=True
    )

    required_group.add_argument(
        '-n',
        '--network',
        help='The Network ID to use.',
        required=True
    )

    required_group.add_argument(
        '-u',
        '--sub-network',
        help='The subnetwork id to use.',
        required=True
    )

    required_group.add_argument(
        '-p',
        '--project',
        help='The GCP Project ID to use.',
        required=True
    )

    required_group.add_argument(
        '-e',
        '--script',
        help='The http path to the bootstrap script file.',
        required=True
    )

    required_group.add_argument(
        '-o',
        '--os-family',
        help='The os family to use when storing the new image.',
        required=True
    )

    required_group.add_argument(
        '-m',
        '--machine-type',
        help='The machine type to use (e.g. e2-standard-2).',
        required=True
    )

    args = parser.parse_args()

    args.image_name = args.image_name.lower()

    return args


if __name__ == '__main__':
    args = getopts()
    compose(args)
    sys.exit(0)
