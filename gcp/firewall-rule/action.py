#!/usr/bin/env python3
# -*- coding 'utf8' -*-

__author__ = 'Robin Wittler'
__contact__ = 'robin.wittler@engelvoelkers.com'
__version__ = '0.0.1'

import os
import sys
import json
from sh import gcloud, ErrorReturnCode
from argparse import ArgumentParser

firewall = gcloud.compute.bake(
    "firewall-rules",
    format='json'
)


def _auth(arguments):
    credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', None)
    if credentials is None:
        raise EnvironmentError(
            'Can not find GOOGLE_APPLICATION_CREDENTIALS '
            'in Environment Variables'
        )

    auth = gcloud.auth.bake(
        "activate-service-account"
    ).bake(key_file=credentials)
    if arguments.dry_run:
        print(auth)
    else:
        auth()


def _call(cmd, dry_run, fail_hard=True, deserialize=False):
    if dry_run:
        print(cmd)
        return
    try:
        ret = cmd()
        if deserialize:
            return json.loads(ret.stdout)
    except ErrorReturnCode as e:
        if fail_hard:
            raise e
        else:
            return None


def _diff_ports(proto, ports, existing):
    existing_ports = set()
    for allowed in existing.get('allowed'):
        if allowed.get('IPProtocol') != proto:
            continue
        existing_ports.update(_parse_ports(allowed.get('ports', [])))
    return _diff_lists(ports, existing_ports)


def _diff_lists(list_a, list_b):
    set_a = set([item for item in list_a if item])
    set_b = set([item for item in list_b if item])
    return (
        list(set_a - set_b),
        list(set_b - set_a),
    )


def _parse_ports(ports):
    if not ports:
        return []
    ret = set()
    if not hasattr(ports, 'sort'):
        ports = ports.split(',')
    for port in ports:
        if '-' in port:
            start, end = port.split('-')
            ret.update(list(range(int(start), int(end) + 1)))
        else:
            ret.add(port)
    return list(ret)


def _diff_msg(diff_type, new, old, verbose=0):
    ret = False
    if old:
        if verbose:
            print(f'Remove {diff_type}: {old}')
        ret = True
    if new:
        if verbose:
            print(f'Add {diff_type}: {new}')
        ret = True
    return ret


def _ports_format(tcp, udp):
    ret_string = ''
    if tcp:
        ret_string = ','.join(
            [
                f'tcp:{item}'
                for item in tcp.split(',')
            ]
        )
    if udp:
        udp = ','.join(
            [
                f'udp:{item}'
                for item in udp.split(',')
            ]
        )
        if ret_string:
            ret_string = f'{ret_string},{udp}'
        else:
            ret_string = udp
    return ret_string


def _diff_rule(arguments, existing):
    updates = {}
    tcp_ports = _diff_ports(
        'tcp',
        _parse_ports(arguments.tcp),
        existing
    )
    udp_ports = _diff_ports(
        'udp',
        _parse_ports(arguments.udp),
        existing
    )
    tags = _diff_lists(
        arguments.tags.split(','),
        existing.get('targetTags', [])
    )
    sources = _diff_lists(
        arguments.source.split(','),
        existing.get('sourceRanges', [])
    )
    if _diff_msg('TCP Ports', verbose=arguments.verbosity, *tcp_ports) \
            or _diff_msg('UDP Ports', verbose=arguments.verbosity, *udp_ports):
        updates['allow'] = _ports_format(
            arguments.tcp,
            arguments.udp
        )
    if _diff_msg('Target Tags', verbose=arguments.verbosity, *tags):
        updates['target_tags'] = arguments.tags
    if _diff_msg('IP Address Sources', verbose=arguments.verbosity, *sources):
        updates['source_ranges'] = arguments.source
    if existing.get('description', '') != arguments.description:
        updates['description'] = arguments.description
    return updates


def compose(arguments):
    _auth(arguments)
    rule = _call(
        firewall.describe.bake(arguments.name, project=arguments.project),
        False,
        False,
        True
    )
    if not rule:
        _call(
            firewall.create.bake(
                arguments.name,
                allow=_ports_format(
                    arguments.tcp,
                    arguments.udp
                ),
                description=arguments.description,
                direction='INGRESS',
                network=arguments.network,
                source_ranges=arguments.source,
                target_tags=arguments.tags,
                project=arguments.project
            ),
            arguments.dry_run,
            True,
            True
        )
        print('Created new Firewall Rule')
    else:
        if rule.get('direction', '') != "INGRESS":
            print('You tried to change a EGRESS rule')
            sys.exit(1)
        updates = _diff_rule(arguments, rule)
        if updates:
            _call(
                firewall.update.bake(
                    arguments.name,
                    project=arguments.project,
                    **updates
                ),
                arguments.dry_run,
                True,
                True
            )
            print('Updated Firewall rule')
        else:
            print('Firewall rule already up to date')

    print(
        "::set-output name=json_out::{data}".format(
            name=arguments.name,
            data=json.dumps(
                _call(
                    firewall.describe.bake(
                        arguments.name,
                        project=arguments.project
                    ),
                    False,
                    False,
                    True
                ) or {}
            ).replace(
                '%',
                '%25'
            ).replace(
                '\n',
                '%0A'
            ).replace(
                '\r',
                '%0D'
            )
        )
    )


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
        '--udp',
        default='',
        help='Comma seperated list of UDP Ports to open '
             '(use minus for range, e.g. 20000-25000).',
        required=False
    )

    parser.add_argument(
        '--description',
        default='',
        help='Description of the Rule',
        required=False
    )

    required_group = parser.add_argument_group(title='required arguments')

    required_group.add_argument(
        '--name',
        help=(
            'The Name of the firewall rule'
        ),
        required=True
    )

    required_group.add_argument(
        '--tcp',
        help='Comma seperated list of TCP Ports to open '
             '(use minus for range, e.g. 20000-25000).',
        required=True
    )

    required_group.add_argument(
        '--source',
        help='Allowed source IP addresses (CIDR notated).',
        required=True
    )

    required_group.add_argument(
        '--tags',
        help='Target tags for the rule (comma separated).',
        required=True
    )

    parser.add_argument(
        '--network',
        help='Network of the Rule',
        required=True
    )

    required_group.add_argument(
        '--project',
        help='The GCP Project',
        required=True
    )

    arguments = parser.parse_args(argv)
    arguments.verbosity = arguments.v
    return arguments


if __name__ == '__main__':
    args = parse_args()
    compose(args)
    sys.exit(0)
