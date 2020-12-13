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
import arrow
import os


class EventLogger:
    """
    Code for the event logger. Note that this is not the same as the debug logger,
    which is a default instance of the "logging" library's logger class. This has its own
    debug logger, which is gross and confusing. TODO: Figure out if it's even used.
    """

    def setup_logger(self, debug):
        """
        Set up all loggers.
        :param debug: whether debug mode should be enabled

        """
        if not os.path.exists('logs'):
            os.mkdir('logs')
        logging.Formatter.converter = time.gmtime
        debug_formatter = logging.Formatter('[%(asctime)s UTC] %(message)s')

        stdoutHandler = logging.StreamHandler(sys.stdout)
        stdoutHandler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(name)s] %(module)s@%(lineno)d : %(message)s')
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
        file_handler.setFormatter(logging.Formatter('[%(asctime)s UTC] %(message)s'))
        info_log.addHandler(file_handler)

        if not debug:
            debug_log.disabled = True
        else:
            debug_log.debug('Logger started')

    def parse_client_info(self, client):
        """Prepend information about a client to a log entry."""
        if client is None:
            return ''
        ipid = client.ip
        prefix = f'[{ipid:<15}][{client.id:<3}][{client.name}]'
        if client.is_mod:
            prefix += '[MOD]'
        return prefix


class MessageBuffer():
    """
    Represents an instance of a message buffer used for as-needed logging. This should not
    be constructed unless the user turns on buffer mode.
    """
    buffer_counter: int
    message_buffer: list

    def __init__(self):
        self.buffer_counter = 0
        self.message_buffer = [None] * 501

    def add_to_buffer(self, message_type, message_subtype, client, message, showname=None):
        self.buffer_counter = (self.buffer_counter + 1) % 500
        fullstr = (f'[{arrow.get().datetime}][{message_subtype}][{message_type}][{client.area.abbreviation}]{"[MOD]" if client.is_mod else ""} {client.char_name}/{showname if message_type == "IC" else client.name} ({client.ipid}): {message}')
        self.message_buffer[self.buffer_counter] = fullstr
        print(fullstr)  # DEBUG REMOVE ME

    def dump_log(self, area, reason, client):
        if not os.path.exists('reports'):
            os.mkdir('reports')
        with open(os.path.join('reports', str(arrow.get().datetime).replace(':', '.') + '.txt'), 'w') as f:
            f.write(
                f'Mod call by: {client.char_name} ({client.ipid}) aka {client.name}\n')
            f.write('Reason: ' + reason + '\n')
            #cheap work arounds ahoy
            z = self.buffer_counter + 1
            for x in range(z, 501):
                if not self.message_buffer[x] == None and (area in self.message_buffer[x] or '[g][OOC]' in self.message_buffer[x]):
                    f.write(str(self.message_buffer[x] + '\n'))
            for x in range(0, z):
                if not self.message_buffer[x] == None and (area in self.message_buffer[x] or '[g][OOC]' in self.message_buffer[x]):
                    f.write(str(self.message_buffer[x] + '\n'))
