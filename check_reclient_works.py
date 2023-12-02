#!/usr/bin/env python3
# Copyright (c) 2023 Contributors to the reclient-configs project. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import subprocess
import sys
import tempfile

from configure_reclient import Paths


DOCKER_IMAGE = 'docker://docker.io/library/debian@sha256:82bab30ed448b8e2509aabe21f40f0607d905b7fd0dec72802627a20274eba55'


def main():
    Paths.init_from_args(parse_args())
    return check_reclient_works()


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--src_dir',
        help='Chromium src directory.',
        required=True,
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--reclient_cfgs_dir',
        help=('Path to Chromium reclient_cfgs directory.'),
        default=Paths.reclient_cfgs_dir,
    )
    parser.add_argument(
        '--reclient_dir',
        help=('Path to Chromium reclient directory.'),
        default=Paths.reclient_dir,
    )
    return parser.parse_args()


def check_reclient_works():
    print('Starting reproxy')
    subprocess.check_call([
        f'{Paths.reclient_dir}/bootstrap',
        '--cfg',
        f'{Paths.reclient_cfgs_dir}/reproxy.cfg',
    ])
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            print('Remotely executing "echo hello > hello"')
            subprocess.check_call([
                f'{Paths.reclient_dir}/rewrapper',
                '--labels=type=tool',
                f'--platform=container-image={DOCKER_IMAGE},OSFamily=linux',
                '--output_files=hello',
                '/bin/bash', '-c', 'echo hello > hello',
            ], cwd=tmp_dir)
            with open(f'{tmp_dir}/hello') as f:
                result = f.read()
                if result == 'hello\n':
                    print('Received expected result')
                else:
                    print(f'Received unexpected result: "{result}"')
                    return 1
        return 0
    finally:
        print('Shutting down reproxy')
        subprocess.check_call([
            f'{Paths.reclient_dir}/bootstrap',
            '--cfg',
            f'{Paths.reclient_cfgs_dir}/reproxy.cfg',
            '--shutdown',
        ])


if __name__ == '__main__':
    sys.exit(main())
