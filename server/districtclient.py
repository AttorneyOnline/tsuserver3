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
import asyncio


class DistrictClient:
    def __init__(self, server):
        self.server = server
        self.reader = None
        self.writer = None
        self.message_queue = []

    async def connect(self):
        loop = asyncio.get_event_loop()
        while True:
            try:
                self.reader, self.writer = await asyncio.open_connection(self.server.config['district_ip'],
                                                                         self.server.config['district_port'], loop=loop)
                await self.handle_connection()
            except ConnectionRefusedError:
                pass
            except ConnectionResetError:
                self.writer = None
                self.reader = None
            finally:
                await asyncio.sleep(15)

    async def handle_connection(self):
        print('District connected.')
        self.send_raw_message('AUTH {}'.format(self.server.config['district_password']))
        while True:
            data = await self.reader.read(2048)
            if not data:
                return
            msg = data.decode()
            print(msg)

    async def write_queue(self):
        while self.message_queue:
            msg = self.message_queue.pop(0)
            self.writer.write(msg)
            await self.writer.drain()

    def send_raw_message(self, msg):
        if not self.writer:
            return
        self.message_queue.append('{}\r\n'.format(msg).encode())
        asyncio.ensure_future(self.write_queue(), loop=asyncio.get_event_loop())
