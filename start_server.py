#!/usr/bin/env python3

# tsuserver3, an Attorney Online server
#
# Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# Install dependencies in case one is missing

import sys
import subprocess


def check_deps():
    py_version = sys.version_info
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 7):
        print("tsuserver3 requires at least Python 3.7! Your version: {}.{}"
                .format(py_version.major, py_version.minor))
        sys.exit(1)

    try:
        import arrow
    except ModuleNotFoundError:
        print('Installing dependencies for you...')
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--user', '-r',
                'requirements.txt'
                ])
            print('If an import error occurs after the installation, try '
                    'restarting the server.')
        except subprocess.CalledProcessError:
            print('Couldn\'t install it for you, because you don\'t have pip, '
                'or another error occurred.')


def main():
    from server.tsuserver import TsuServer3
    server = TsuServer3()
    server.start()


if __name__ == '__main__':
    print('tsuserver3 - an Attorney Online server')
    check_deps()
    main()
