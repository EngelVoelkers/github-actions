#!/usr/bin/env python3
# -*- coding 'utf8' -*-

__author__ = 'Robin Wittler'
__contact__ = 'robin.wittler@engelvoelkers.com'
__version__ = '0.0.1'

import os
import sys
import subprocess
from argparse import ArgumentParser


def prepare_auth_cmd():
    credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', None)
    if credentials is None:
        raise EnvironmentError(
            'Can not find GOOGLE_APPLICATION_CREDENTIALS '
            'in Environment Variables'
        )

    cmd = [
        'gcloud',
        'auth',
        'activate-service-account',
        f'--key-file={credentials}'
    ]

    return cmd


def auth_cmd(arguments):
    return exec_cmd(
        prepare_auth_cmd(),
        echo=False,
        dry_run=arguments.dry_run,
        verbosity=arguments.verbosity
    )


def prepare_get_all_images_cmd(arguments):
    cmd = [
        'gcloud',
        'compute',
        'images',
        'list',
        f'--project={arguments.project}',
        f'--filter=family~\'{arguments.os_family}\'',
        '--format=value(name)',
        '--sort-by="~name"'
    ]

    return cmd


def get_all_images_cmd(arguments):
    result = exec_cmd(
        prepare_get_all_images_cmd(arguments),
        echo=False,
        dry_run=arguments.dry_run,
        verbosity=arguments.verbosity,
        output=True
    )

    if arguments.dry_run is True:
        return set()
    else:
        return set(result.rstrip().split('\n'))


def prepare_deprecate_image_cmd(image_name, arguments):
    cmd = [
        'gcloud',
        'compute',
        'images',
        'deprecate',
        f'{image_name}',
        '--state=DEPRECATED',
        f'--project={arguments.project}',
        f'--replacement={arguments.replacement}',
        f'--delete-in={arguments.delete_in}'
    ]

    return cmd


def deprecate_image_cmd(image_name, arguments):
    return exec_cmd(
        prepare_deprecate_image_cmd(
            image_name,
            arguments
        ),
        echo=False,
        dry_run=arguments.dry_run,
        verbosity=arguments.verbosity
    )


def compose(arguments):
    auth_cmd(arguments)
    all_images = get_all_images_cmd(arguments)
    for image_name in all_images.difference({arguments.replacement}):
        deprecate_image_cmd(image_name, arguments)
    print(
        '::set-output name=deleted_images::'
        f'{len(all_images.difference(arguments.replacement))}'
    )


def exec_cmd(cmd, echo=False, dry_run=False, verbosity=0, output=False):
    if verbosity >= 1:
        print(f'Running: {" ".join(cmd)}')
    if dry_run is False:
        if output is True:
            result = subprocess.check_output(cmd).decode('utf8')
            if verbosity >= 2:
                print(result)
            return result

        if echo is False or verbosity >= 2:
            return subprocess.check_call(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            return subprocess.check_call(cmd)


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

    parser.add_argument(
        '--delete-in',
        default='10d',
        help=(
            'Delete deprecated images after that period of time. '
            'Default: %(default)s'
        ),
        required=False
    )

    required_group = parser.add_argument_group(title='required arguments')

    required_group.add_argument(
        '--replacement',
        help=(
            'Use this image as the new default '
            'for the os family.'
        ),
        required=True
    )

    required_group.add_argument(
        '--os-family',
        help='Deprecate images of this os family.',
        required=True
    )

    required_group.add_argument(
        '--project',
        help='The GCP Project',
        required=True
    )

    arguments = parser.parse_args(argv)
    arguments.verbosity = arguments.v
    arguments.replacement = arguments.replacement.lower()
    return arguments


if __name__ == '__main__':
    args = parse_args()
    compose(args)
    sys.exit(0)
