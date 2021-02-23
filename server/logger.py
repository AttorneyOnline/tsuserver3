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

import sys
import logging
import logging.handlers
import time

from server.client_manager import ClientManager


def setup_logger(debug: bool):
    """Set up all loggers.
    Args:
        debug (bool): whether debug mode should be enabled
    """
    logging.Formatter.converter = time.gmtime
    debug_formatter = logging.Formatter('[%(asctime)s UTC] %(message)s')

    stdoutHandler = logging.StreamHandler(sys.stdout)
    stdoutHandler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '[%(name)s] %(module)s@%(lineno)d : %(message)s')
    stdoutHandler.setFormatter(formatter)
    logging.getLogger().addHandler(stdoutHandler)

    debug_log = logging.getLogger('debug')
    debug_log.setLevel(logging.DEBUG)

    debug_handler = logging.handlers.RotatingFileHandler('logs/debug.log', encoding='utf-8',
                                                         maxBytes=1024 * 1024 * 4)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(debug_formatter)
    debug_log.addHandler(debug_handler)

    # Intended to be a brief log for `tail -f`. To search through events,
    # use the database.
    info_log = logging.getLogger('events')
    info_log.setLevel(logging.INFO)
    file_handler = logging.handlers.RotatingFileHandler('logs/server.log', encoding='utf-8',
                                                        maxBytes=1024 * 512)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s UTC] %(message)s'))
    info_log.addHandler(file_handler)

    if not debug:
        debug_log.disabled = True
    else:
        debug_log.debug('Logger started')


def parse_client_info(client: ClientManager.Client) -> str:
    """Prepend information about a client to a log entry.

    Args:
        client (ClientManager.Client): Client you want to convert to log entry

    Returns:
        str: Information about a client
    """
    if client is None:
        return ''
    ipid = client.ip
    prefix = f'[{ipid:<15}][{client.id:<3}][{client.name}]'
    if client.is_mod:
        prefix += '[MOD]'
    return prefix
