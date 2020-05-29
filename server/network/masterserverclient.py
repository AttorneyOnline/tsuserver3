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

import asyncio
import time

import logging
logger = logging.getLogger('debug')



class MasterServerClient:
    """Advertises information about this server to the master server."""
    def __init__(self, server):
        self.server = server
        self.reader = None
        self.writer = None

    async def connect(self):
        loop = asyncio.get_event_loop()
        while True:
            try:
                self.reader, self.writer = await asyncio.open_connection(
                    self.server.config['masterserver_ip'],
                    self.server.config['masterserver_port'],
                    loop=loop)
                await self.handle_connection()
            except (ConnectionRefusedError, TimeoutError,
                    ConnectionResetError, asyncio.IncompleteReadError):
                logger.debug('Connection error occurred.')
                self.writer = None
                self.reader = None
            finally:
                logger.debug('Retrying MS connection in 30 seconds.')
                await asyncio.sleep(30)

    async def handle_connection(self):
        logger.debug('Master server connected.')
        print('Master server connected ({}:{})'.format(
            self.server.config['masterserver_ip'],
            self.server.config['masterserver_port']))

        await self.send_server_info()
        ping_timeout = False
        last_ping = time.time() - 20
        while True:
            self.reader.feed_data(b'END')
            full_data = await self.reader.readuntil(b'END')
            full_data = full_data[:-3]
            if len(full_data) > 0:
                data_list = list(full_data.split(b'#%'))[:-1]
                for data in data_list:
                    raw_msg = data.decode()
                    cmd, *args = raw_msg.split('#')
                    if cmd != 'CHECK' and cmd != 'PONG':
                        logger.debug(f'Incoming: {raw_msg}')
                    elif cmd == 'CHECK':
                        logger.debug('Replying to CHECK#% with ping')
                        await self.send_raw_message('PING#%')
                    elif cmd == 'PONG':
                        ping_timeout = False
                    elif cmd == 'NOSERV':
                        logger.debug('MS does not have our server. Readvertising.')
                        await self.send_server_info()
            if time.time() - last_ping > 10:
                if ping_timeout:
                    self.writer.close()
                    return
                last_ping = time.time()
                ping_timeout = True
                await self.send_raw_message('PING#%')
            await asyncio.sleep(1)

    async def send_server_info(self):
        logger.debug('Advertising to MS')
        cfg = self.server.config
        port = str(cfg['port'])
        if cfg['use_websockets']:
            port += '&{}'.format(cfg['websocket_port'])
        msg = 'SCC#{}#{}#{}#{}#%'.format(port, cfg['masterserver_name'],
                                         cfg['masterserver_description'],
                                         self.server.software)
        await self.send_raw_message(msg)

    async def send_raw_message(self, msg):
        self.writer.write(msg.encode())
        await self.writer.drain()
