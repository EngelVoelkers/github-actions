#!/usr/bin/env python3
# -*- coding 'utf8' -*-

__author__ = 'Robin Wittler'
__contact__ = 'robin.wittler@engelvoelkers.com'
__version__ = '0.0.1'

import os
import sh
import sys
import tempfile
import requests

# noinspection PyUnresolvedReferences
from sh import (
    ErrorReturnCode,
    ErrorReturnCode_1
)
from argparse import ArgumentParser


# noinspection PyUnresolvedReferences
gcloud = sh.gcloud.bake()
template = gcloud.compute.bake('instance-templates')


def echo(verbosity, level, data):
    if verbosity >= level:
        print(data)


def download_script(arguments):
    echo(
        arguments.verbosity,
        1,
        f'Running: Download of {arguments.startup_script} '
        f'to {arguments.destination}'
    )
    if arguments.dry_run is False:
        request = requests.get(arguments.startup_script)
        result = f'{request.status_code} - {arguments.startup_script} {request.reason}'

        if request.status_code != 200:
            raise requests.exceptions.RequestException(
                f'{result}'
            )
        with open(arguments.destination, 'w') as fh:
            fh.write(request.content.decode('utf8'))
        echo(
            arguments.verbosity,
            2,
            f'Result: {result}'
        )
        echo(
            arguments.verbosity,
            3,
            f'Result: {request.content.decode("utf8")}'
        )



def auth(arguments):
    credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', None)
    if credentials is None:
        raise EnvironmentError(
            'Can not find GOOGLE_APPLICATION_CREDENTIALS '
            'in Environment Variables'
        )

    cmd = gcloud.auth.bake('activate-service-account', key_file=credentials)
    exec_cmd(
        cmd,
        dry_run=arguments.dry_run,
        verbosity=arguments.verbosity
    )


def template_create(arguments):
    cmd = template.create.bake(
        arguments.name,
        region=arguments.region,
        network=arguments.network,
        subnet=arguments.sub_network,
        machine_type=arguments.machine_type,
        boot_disk_type='pd-balanced',
    )

    if arguments.startup_script:
        cmd = cmd.bake(
            metadata_from_file=f'startup-script={arguments.destination}'
        )

    if arguments.scopes:
        cmd = cmd.bake(
            scopes=arguments.scopes
        )
    else:
        cmd = cmd.bake(
            'no_scopes'
        )

    if arguments.labels:
        cmd = cmd.bake(
            labels=arguments.labels
        )

    if arguments.tags:
        cmd = cmd.bake(
            tags=arguments.tags
        )

    if arguments.image:
        cmd = cmd.bake(
            image=arguments.image,
        )

    if arguments.image_family:
        cmd = cmd.bake(
            image_family=arguments.image_family,
        )

    #if arguments.image or arguments.image_family:
    #    cmd = cmd.bake(
    #        image_project=arguments.image_project
    #    )

    exec_cmd(
        cmd,
        dry_run=arguments.dry_run,
        verbosity=arguments.verbosity
    )


def compose(arguments):
    fd, destination = tempfile.mkstemp()
    arguments.destination = destination
    try:
        auth(arguments)
        if arguments.startup_script:
            download_script(arguments)
        template_create(arguments)
    except Exception as error:
        print(f'Error: {error}')
        sys.exit(1)
    finally:
        os.unlink(destination)


def exec_cmd(cmd, dry_run=False, verbosity=0):
    echo(verbosity, 1, f'Running: {cmd}')

    if dry_run is False:
        result = cmd(_err_to_out=True)
        echo(verbosity, 2, f'Result: {result.stdout.decode("utf8")}')
        return result


def parse_args(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = ArgumentParser()

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    parser.add_argument(
        '-v',
        action='count',
        required=False,
        default=0,
        help='Set this option to get more output. Can be used multiple times.'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=False,
        help=(
            'Set this to make a dry run without any changes. '
            'Default: %(default)s'
        ),
        required=False,
    )

    parser.add_argument(
        '--startup-script',
        help='The http path to a startup script file.',
        required=False
    )


    parser.add_argument(
        '--tags',
        help='Comma delimited list of network tags.',
        required=False
    )

    parser.add_argument(
        '--scopes',
        help='Comma delimited list of GCP scopes.',
        required=False
    )

    parser.add_argument(
        '--labels',
        help='Comma delimited list of key=value pairs.',
        required=False
    )

    parser.add_argument(
        '--image-project',
        required=False,
        default=None,
        help=(
            'The project where the image or image family is located. '
            'If not given the template project will be used. '
            'Default: %(default)s'
        )
    )
    # --image - project = IMAGE_PROJECT - -image = IMAGE
    # | --image - family = IMAGE_FAMILY]

    parser.add_argument(
        '--image',
        default=None,
        required=False,
        help=(
            'The name of the image to use. '
            'If image or image-family is not given, the project '
            'Default Image Family will be used (e.g. debian-10). '
            'Default: %(default)s'
        )
    )

    parser.add_argument(
        '--image-family',
        default=None,
        required=False,
        help=(
            'The name of the image-family to use. '
            'If image-family or image is not given, the project '
            'Default Image Family will be used (e.g. debian-10). '
            'Default: %(default)s'
        )
    )

    required_group = parser.add_argument_group(title='required arguments')

    required_group.add_argument(
        '--name',
        help='The name of the template',
        required=True
    )

    required_group.add_argument(
        '--project',
        help='The GCP Project',
        required=True
    )
    required_group.add_argument(
        '--region',
        help='The GCP Region.',
        required=True
    )

    required_group.add_argument(
        '--network',
        help='The Network ID to use.',
        required=True
    )

    required_group.add_argument(
        '--sub-network',
        help='The subnetwork id to use.',
        required=True
    )

    required_group.add_argument(
        '--machine-type',
        help='The machine type to use (e.g. e2-standard-2).',
        required=True
    )

    arguments = parser.parse_args(argv)
    arguments.verbosity = arguments.v
    #if not arguments.image_project:
    #    arguments.image_project = arguments.project

    if arguments.image_family and arguments.image:
        parser.exit(
            status=1,
            message='Error: image and image-family are mutually exclusive.'
        )
    return arguments


if __name__ == '__main__':
    args = parse_args()
    compose(args)
    sys.exit(0)
