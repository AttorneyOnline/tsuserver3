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
import aiohttp
import stun
import time
from threading import Thread

import logging
logger = logging.getLogger('debug')

stun_servers = [
    ('stun.l.google.com', 19302),
    ('global.stun.twilio.com', 3478),
    ('stun.voip.blackberry.com', 3478),
]

API_BASE_URL = 'https://servers.aceattorneyonline.com'

class MasterServerClient:
    """Advertises information about this server to the master server."""
    def __init__(self, server):
        self.server = server

    async def connect(self):
        async with aiohttp.ClientSession() as http:
            while True:
                try:
                    await self.send_server_info(http)
                except aiohttp.ClientError:
                    logger.exception('Connection error occurred.')
                finally:
                    await asyncio.sleep(60)

    def get_my_ip(self):
        for stun_ip, stun_port in stun_servers:
            nat_type, external_ip, _external_port = \
                stun.get_ip_info(stun_host=stun_ip, stun_port=stun_port)
            if nat_type != stun.Blocked:
                return external_ip

    async def send_server_info(self, http: aiohttp.ClientSession):
        loop = asyncio.get_event_loop()
        cfg = self.server.config
        body = {
            'ip': await loop.run_in_executor(None, self.get_my_ip),
            'port': cfg['port'],
            'name': cfg['masterserver_name'],
            'description': cfg['masterserver_description'],
            'players': self.server.player_count
        }

        if 'masterserver_custom_hostname' in cfg:
            body['ip'] = cfg['masterserver_custom_hostname']
        if cfg['use_websockets']:
            body['ws_port'] = cfg['websocket_port']

        async with http.post(f'{API_BASE_URL}/servers', json=body) as res:
            err_body = await res.text()
            try:
                res.raise_for_status()
            except aiohttp.ClientResponseError as err:
                logging.error(f"Got status={err.status} advertising {body}: {err_body}")

        logger.debug(f'Heartbeat to {API_BASE_URL}/servers')
