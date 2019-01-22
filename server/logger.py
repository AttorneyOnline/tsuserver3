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


def setup_logger(debug):
    """
    Set up all loggers.
    :param debug: whether debug mode should be enabled

    """
    logging.Formatter.converter = time.gmtime
    debug_formatter = logging.Formatter('[%(asctime)s UTC] %(message)s')

    stdoutHandler = logging.StreamHandler(sys.stdout)
    stdoutHandler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(name)s] %(module)s@%(lineno)d : %(message)s')
    stdoutHandler.setFormatter(formatter)
    logging.getLogger().addHandler(stdoutHandler)

    debug_log = logging.getLogger('debug')
    debug_log.setLevel(logging.DEBUG)

    debug_handler = logging.handlers.RotatingFileHandler('logs/debug.log',
        maxBytes=1024 * 1024 * 4)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(debug_formatter)
    debug_log.addHandler(debug_handler)

    # Intended to be a brief log for `tail -f`. To search through events,
    # use the database.
    info_log = logging.getLogger('events')
    info_log.setLevel(logging.INFO)
    file_handler = logging.handlers.RotatingFileHandler('logs/server.log',
        maxBytes=1024 * 512)
    file_handler.setFormatter(logging.Formatter('[%(asctime)s UTC] %(message)s'))
    info_log.addHandler(file_handler)

    if not debug:
        debug_log.disabled = True
    else:
        debug_log.debug('Logger started')


    server_handler = logging.handlers.RotatingFileHandler('logs/server.log', maxBytes=log_size, backupCount=log_backups,
                                                          encoding='utf-8')
    server_handler.setLevel(logging.INFO)
    server_handler.setFormatter(srv_formatter)
    server_log.addHandler(server_handler)

    mod_log = logging.getLogger('mod')
    mod_log.setLevel(logging.INFO)

    mod_handler = logging.handlers.RotatingFileHandler('logs/mod.log', maxBytes=log_size, backupCount=log_backups,
                                                          encoding='utf-8')
    mod_handler.setLevel(logging.INFO)
    mod_handler.setFormatter(mod_formatter)
    mod_log.addHandler(mod_handler)

    serverpoll_log = logging.getLogger('serverpoll')
    serverpoll_log.setLevel(logging.INFO)
    serverpoll_handler = logging.FileHandler('logs/serverpoll.log', encoding='utf-8')
    serverpoll_handler.setLevel(logging.INFO)
    serverpoll_handler.setFormatter(srv_formatter)
    serverpoll_log.addHandler(serverpoll_handler)

    area_logs = []
    area_handler = []
    i = 0
    if not os.path.exists('logs/area/'):
        os.makedirs('logs/area/')
    for area in areas:
        area_logs.append(logging.getLogger(area.name))
        area_logs[i].setLevel(logging.INFO)
        area_handler.append(logging.handlers.RotatingFileHandler('logs/area/'+ area.name + '.log', maxBytes=log_size, backupCount=log_backups,
                                                           encoding='utf-8'))
        area_handler[i].setLevel(logging.INFO)
        area_handler[i].setFormatter(srv_formatter)
        area_logs[i].addHandler(area_handler[i])
        i += 1

def log_debug(msg, client=None):
    msg = parse_client_info(client) + msg
    print("DEBUG: " + msg)
    logging.getLogger('debug').debug(msg)


def log_server(msg, client=None):
    msg = parse_client_info(client) + msg
    if client:
        logging.getLogger(client.area.name).info(msg)
        print("AREA " + client.area.name + ": " + msg)
    print("SERVER: " + msg)
    logging.getLogger('server').info(msg)


def log_mod(msg, client=None):
    msg = parse_client_info(client) + msg
    print("MOD: " + msg)
    logging.getLogger('mod').info(msg)

def log_serverpoll(msg, client=None):
    msg = parse_client_info(client) + msg
    print("SERVERPOLL: " + msg)
    logging.getLogger('serverpoll').info(msg)

def log_connect(msg, client=None):
    msg = parse_client_info(client) + msg
    print("CONNECT: " + msg)
    logging.getLogger('connect').info(msg)
    logging.getLogger('server').info(msg)

    
    
def parse_client_info(client):
    """Prepend information about a client to a log entry."""
    if client is None:
        return ''
    ipid = client.ip
    prefix = f'[{ipid:<15}][{client.id:<3}][{client.name}]'
    if client.is_mod:
        prefix += '[MOD]'
    return prefix