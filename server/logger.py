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
from logging.handlers import TimedRotatingFileHandler

import time
import datetime as dt

class MyFormatter(logging.Formatter):
    converter = dt.datetime.utcfromtimestamp

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%H:%M:%S")
            s = "%s.%03d" % (t, record.msecs)
        return s

def setup_logger(debug):
    logging.Formatter.converter = time.gmtime
    base_formatter = logging.Formatter('[%(asctime)s UTC]%(message)s')
    # suffix = time.strftime("%A, %B %d, %Y", time.gmtime())

    debug_log = logging.getLogger('debug')
    debug_log.setLevel(logging.DEBUG)

    debug_handler = TimedRotatingFileHandler(
        'logs/debug/debug.log', when='midnight', interval=1, encoding='utf-8')
    # debug_handler.suffix = '{}.log'.format(suffix)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(base_formatter)
    debug_log.addHandler(debug_handler)

    if not debug:
        debug_log.disabled = True

    mod_log = logging.getLogger('mod')
    mod_log.setLevel(logging.INFO)

    mod_handler = TimedRotatingFileHandler(
        'logs/mod/mod.log', when='midnight', interval=1, encoding='utf-8')
    # mod_handler.suffix = '{}.log'.format(suffix)
    mod_handler.setLevel(logging.INFO)
    mod_handler.setFormatter(base_formatter)
    mod_log.addHandler(mod_handler)

    server_log = logging.getLogger('server')
    server_log.setLevel(logging.INFO)

    server_handler = TimedRotatingFileHandler(
        'logs/server/server.log', when='midnight', interval=1, encoding='utf-8')
    # server_handler.suffix = '{}.log'.format(suffix)
    server_handler.setLevel(logging.INFO)
    server_handler.setFormatter(base_formatter)
    server_log.addHandler(server_handler)

    #Extreme logging for future demo playback
    demo_log = logging.getLogger('demo')
    demo_log.setLevel(logging.INFO)

    demo_formatter = MyFormatter('[%(asctime)s]%(message)s')

    demo_handler = TimedRotatingFileHandler(
        'logs/demo/demo.log', when='midnight', interval=1, encoding='utf-8')
    # demo_handler.suffix = '{}.log'.format(suffix)
    demo_handler.setLevel(logging.INFO)
    demo_handler.setFormatter(demo_formatter)
    demo_log.addHandler(demo_handler)

def log_debug(msg, client=None):
    msg = parse_client_info(client) + msg
    logging.getLogger('debug').debug(msg)


def log_server(msg, client=None):
    msg = parse_client_info(client) + msg
    logging.getLogger('server').info(msg)


def log_mod(msg, client=None):
    msg = parse_client_info(client) + msg
    logging.getLogger('mod').info(msg)


def log_demo(msg, client=None):
    msg = parse_client_demo_info(client) + msg
    logging.getLogger('demo').info(msg)


def parse_client_info(client):
    if client is None:
        return ''
    info = client.get_ip()
    extra = ''
    if client.is_mod:
        extra = '[MOD]'
    if client.is_gm:
        extra = '[GM]'

    return '[{} {} {} H{} A{}][{}]{}'.format(info, client.id, client.name, client.hub.id, client.area.id, client.get_char_name(True), extra)

def parse_client_demo_info(client):
    if client is None:
        return ''

    return '[H{} A{} C{}]'.format(client.hub.id, client.area.id, client.id)
