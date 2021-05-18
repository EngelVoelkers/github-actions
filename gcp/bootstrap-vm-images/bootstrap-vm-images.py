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


def download_script(arguments):
    request = requests.get(arguments.script)
    with open(arguments.destination, 'w') as fh:
        fh.write(request.content.decode('utf8'))


def prepare_gcloud_auth_cmd(arguments):
    credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', None)
    if credentials is None:
        raise EnvironmentError('Can not find GOOGLE_APPLICATION_CREDENTIALS')

    cmd = [
        'gcloud',
        'auth',
        'activate-service-account',
        f'--key-file={credentials}'
    ]

    return cmd


def prepare_get_instance_cmd(arguments):
    cmd = [
        'gcloud',
        'compute',
        'instances',
        'describe',
        f'{args.image_name}',
        f'--project={args.project}',
        f'--zone={args.zone}'
    ]

    return cmd


def prepare_create_instance_cmd(arguments):
    cmd = [
        'gcloud',
        'compute',
        'instances',
        'create',
        f'{arguments.image_name}',
        f'--boot-disk-device-name={arguments.image_name}',
        f'--image-family={arguments.from_image}',
        f'--image-project={arguments.from_image_project}',
        f'--project={arguments.project}',
        f'--zone={arguments.zone}',
        f'--machine-type={arguments.machine_type}',
        f'--network={arguments.network}',
        f'--subnet={arguments.sub_network}'
    ]

    if arguments.tags:
        cmd.append(f'--tags={arguments.tags}')

    if arguments.scopes:
        cmd.append(f'--scopes={arguments.scopes}')

    if arguments.labels:
        cmd.append(f'--labels={arguments.labels}')

    return cmd


def prepare_delete_instance_cmd(arguments):
    cmd = [
        'gcloud',
        '-q',
        'compute',
        'instances',
        'delete',
        f'{arguments.image_name}',
        f'--zone={arguments.zone}',
        f'--project={arguments.project}',
        '--delete-disks=all'
    ]

    return cmd


def prepare_scp_copy_cmd(arguments):
    cmd = [
        'gcloud',
        '-q',
        'compute',
        'scp',
        f'--zone={arguments.zone}',
        f'--project={arguments.project}',
        f'--ssh-key-expire-after={arguments.ssh_key_expire}',
        f'{arguments.destination}',
        f'bootstrapper@{arguments.image_name}:bootstrap.sh'
    ]

    return cmd


def prepare_chmod_cmd(arguments):
    cmd = [
        'gcloud',
        '-q',
        'compute',
        'ssh',
        f'bootstrapper@{arguments.image_name}',
        f'--zone={arguments.zone}',
        f'--project={arguments.project}',
        f'--ssh-key-expire-after={arguments.ssh_key_expire}',
        f'--command="\"chmod 0750 ./bootstrap.sh\""'
    ]

    return cmd


def prepare_sudo_cmd(arguments):
    cmd = [
        'gcloud',
        '-q',
        'compute',
        'ssh',
        f'bootstrapper@{arguments.image_name}',
        f'--zone={arguments.zone}',
        f'--project={arguments.project}',
        f'--ssh-key-expire-after={arguments.ssh_key_expire}',
    ]

    if arguments.variables:
        variables = f'export {arguments.variables}; '
    else:
        variables = ''

    cmd.append(f'--command="\"{variables}sudo -E ./bootstrap.sh\""')

    return cmd


def prepare_rm_cmd(arguments):
    cmd = [
        'gcloud',
        '-q',
        'compute',
        'ssh',
        f'bootstrappe@{arguments.image_name}',
        f'--zone={arguments.zone}',
        f'--project={arguments.project}',
        f'--ssh-key-expire-after={arguments.ssh_key_expire}',
        f'--command="\"rm -f -- ./bootstrap.sh\""'
    ]

    return cmd


def prepare_create_image_cmd(arguments):
    cmd = [
        'gcloud',
        'compute',
        'images',
        'create',
        f'{arguments.image_name}',
        f'--source-disk={arguments.image_name}',
        f'--source-disk-zone={arguments.zone}',
        f'--family={arguments.os_family}',
        f'--project={arguments.project}'
    ]

    return cmd


def get_or_create_instance(arguments):
    try:
        cmd = prepare_get_instance_cmd(arguments)
        print(f'Running: {" ".join(cmd)}')
        if arguments.dry_run is False:
            subprocess.check_call(cmd, stdout=None, stderr=None)
    except subprocess.CalledProcessError:
        cmd = prepare_create_instance_cmd(arguments)
        print(f'Running: {" ".join(cmd)}')
        if arguments.dry_run is False:
            subprocess.check_output(cmd).decode('utf8')
    else:
        print(f'Instance with name "{arguments.image_name}" already exists.')


def get_and_delete_instance(arguments):
    try:
        cmd = prepare_get_instance_cmd(arguments)
        print(f'Running: {" ".join(cmd)}')
        if arguments.dry_run is False:
            subprocess.check_call(cmd, stdout=None, stderr=None)
    except subprocess.CalledProcessError:
        print(f'Instance with name "{arguments.image_name}" already deleted.')
    else:
        cmd = prepare_delete_instance_cmd(arguments)
        print(f'Running: {" ".join(cmd)}')
        if arguments.dry_run is False:
            subprocess.check_output(cmd).decode('utf8')


def compose(arguments):
    fd, destination = tempfile.mkstemp()
    arguments.destination = destination
    try:
        PREPARED_CMDS = [
            prepare_scp_copy_cmd(arguments),
            prepare_chmod_cmd(arguments),
            prepare_sudo_cmd(arguments),
            prepare_rm_cmd(arguments),
            prepare_create_image_cmd(arguments)
        ]

        print(f'Download {arguments.script} to {arguments.destination}')
        if arguments.dry_run is False:
            download_script(arguments)

        cmd = prepare_gcloud_auth_cmd(arguments)
        print(f'Running: {" ".join(cmd)}')
        if arguments.dry_run is False:
            subprocess.check_output(cmd).decode('utf8')

        get_or_create_instance(arguments)

        for cmd in PREPARED_CMDS:
            print(f'Running: {" ".join(cmd)}')
            if arguments.dry_run is False:
                subprocess.check_output(cmd).decode('utf8')

        get_and_delete_instance(arguments)
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
