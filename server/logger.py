# tsuserver3, an Attorney Online server
#
# Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging

import time


def setup_logger(debug):
    """
    Set up all loggers.
    :param debug: whether debug mode should be enabled

    """
    logging.Formatter.converter = time.gmtime
    debug_formatter = logging.Formatter('[%(asctime)s UTC]%(message)s')

    debug_log = logging.getLogger('debug')
    debug_log.setLevel(logging.DEBUG)

    debug_handler = logging.FileHandler('logs/debug.log', encoding='utf-8')
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(debug_formatter)
    debug_log.addHandler(debug_handler)

    if not debug:
        debug_log.disabled = True


def log_debug(msg, client=None):
    """Log a debug message that can be used for troubleshooting."""
    msg = parse_client_info(client) + msg
    logging.getLogger('debug').debug(msg)


def parse_client_info(client):
    """Prepend information about a client to a log entry."""
    if client is None:
        return ''
    ipid = client.ip
    prefix = f'[{ipid:<15}][{client.id:<3}][{client.name}]'
    if client.is_mod:
        prefix += '[MOD]'
    return prefix