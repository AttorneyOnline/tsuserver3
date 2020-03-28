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
import os
import importlib

import asyncio
import websockets

import geoip2.database

import json
import yaml

import logging
logger = logging.getLogger('debug')

from server import database
from server.area_manager import AreaManager
from server.client_manager import ClientManager
from server.emotes import Emotes
from server.exceptions import ClientError,ServerError
from server.network.aoprotocol import AOProtocol
from server.network.aoprotocol_ws import new_websocket_client
from server.network.masterserverclient import MasterServerClient
import server.logger

class TsuServer3:
    """The main class for tsuserver3 server software."""
    def __init__(self):
        self.software = 'tsuserver3'
        self.release = 3
        self.major_version = 3
        self.minor_version = 0

        self.config = None
        self.allowed_iniswaps = []
        self.char_list = None
        self.char_emotes = None
        self.char_pages_ao1 = None
        self.music_list = None
        self.music_list_ao2 = None
        self.music_pages_ao1 = None
        self.backgrounds = None
        self.zalgo_tolerance = None
        self.ipRange_bans = []
        self.geoIpReader = None
        self.useGeoIp = False

        try:
            self.geoIpReader = geoip2.database.Reader('./storage/GeoLite2-ASN.mmdb')
            self.useGeoIp = True
            # on debian systems you can use /usr/share/GeoIP/GeoIPASNum.dat if the geoip-database-extra package is installed
        except FileNotFoundError:
            self.useGeoIp = False
            pass

        self.ms_client = None

        try:
            self.load_config()
            self.area_manager = AreaManager(self)
            self.load_iniswaps()
            self.load_characters()
            self.load_music()
            self.load_backgrounds()
            self.load_gimps()
            self.load_ipranges()
        except yaml.YAMLError as exc:
            print('There was a syntax error parsing a configuration file:')
            print(exc)
            print('Please revise your syntax and restart the server.')
            # Truly idiotproof
            if os.name == 'nt':
                input('(Press Enter to exit)')
            sys.exit(1)

        self.client_manager = ClientManager(self)
        server.logger.setup_logger(debug=self.config['debug'])

    def start(self):
        """Start the server."""
        loop = asyncio.get_event_loop()

        bound_ip = '0.0.0.0'
        if self.config['local']:
            bound_ip = '127.0.0.1'

        ao_server_crt = loop.create_server(lambda: AOProtocol(self), bound_ip,
                                           self.config['port'])
        ao_server = loop.run_until_complete(ao_server_crt)

        if self.config['use_websockets']:
            ao_server_ws = websockets.serve(new_websocket_client(self),
                                            bound_ip,
                                            self.config['websocket_port'])
            asyncio.ensure_future(ao_server_ws)

        if self.config['use_masterserver']:
            self.ms_client = MasterServerClient(self)
            asyncio.ensure_future(self.ms_client.connect(), loop=loop)

        if self.config['zalgo_tolerance']:
            self.zalgo_tolerance = self.config['zalgo_tolerance']

        asyncio.ensure_future(self.schedule_unbans())

        database.log_misc('start')
        print('Server started and is listening on port {}'.format(
            self.config['port']))

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        database.log_misc('stop')

        ao_server.close()
        loop.run_until_complete(ao_server.wait_closed())
        loop.close()

    async def schedule_unbans(self):
        while True:
            database.schedule_unbans()
            await asyncio.sleep(3600 * 12)

    @property
    def version(self):
        """Get the server's current version."""
        return f'{self.release}.{self.major_version}.{self.minor_version}'

    def new_client(self, transport):
        """
        Create a new client based on a raw transport by passing
        it to the client manager.
        :param transport: asyncio transport
        :returns: created client object
        """
        peername = transport.get_extra_info('peername')[0]

        if self.useGeoIp:
            try:
                geoIpResponse = self.geoIpReader.asn(peername)
                asn = str(geoIpResponse.autonomous_system_number)
            except geoip2.errors.AddressNotFoundError:
                asn = "Loopback"
                pass
        else:
            asn = "Loopback"

        for line,rangeBan in enumerate(self.ipRange_bans):
            if rangeBan != "" and peername.startswith(rangeBan) or asn == rangeBan:
                msg =   'BD#'
                msg +=  'Abuse\r\n'
                msg += f'ID: {line}\r\n'
                msg +=  'Until: N/A'
                msg +=  '#%'

                transport.write(msg.encode('utf-8'))
                raise ClientError

        c = self.client_manager.new_client(transport)
        c.server = self
        c.area = self.area_manager.default_area()
        c.area.new_client(c)
        return c

    def remove_client(self, client):
        """
        Remove a disconnected client.
        :param client: client object

        """
        client.area.remove_client(client)
        self.client_manager.remove_client(client)

    @property
    def player_count(self):
        """Get the number of non-spectating clients."""
        return len([client for client in self.client_manager.clients
            if client.char_id != -1])

    def load_config(self):
        """Load the main server configuration from a YAML file."""
        with open('config/config.yaml', 'r', encoding='utf-8') as cfg:
            self.config = yaml.safe_load(cfg)
            self.config['motd'] = self.config['motd'].replace('\\n', ' \n')
        if 'music_change_floodguard' not in self.config:
            self.config['music_change_floodguard'] = {
                'times_per_interval': 1,
                'interval_length': 0,
                'mute_length': 0
            }
        if 'wtce_floodguard' not in self.config:
            self.config['wtce_floodguard'] = {
                'times_per_interval': 1,
                'interval_length': 0,
                'mute_length': 0
            }

        if 'zalgo_tolerance' not in self.config:
            self.config['zalgo_tolerance'] = 3

        if isinstance(self.config['modpass'], str):
            self.config['modpass'] = {'default': {'password': self.config['modpass']}}
        if 'multiclient_limit' not in self.config:
            self.config['multiclient_limit'] = 16

    def load_characters(self):
        """Load the character list from a YAML file."""
        with open('config/characters.yaml', 'r', encoding='utf-8') as chars:
            self.char_list = yaml.safe_load(chars)
        self.build_char_pages_ao1()
        self.char_emotes = {char: Emotes(char) for char in self.char_list}

    def load_music(self):
        """Load the music list from a YAML file."""
        with open('config/music.yaml', 'r', encoding='utf-8') as music:
            self.music_list = yaml.safe_load(music)
        self.build_music_pages_ao1()
        self.build_music_list_ao2()

    def load_backgrounds(self):
        """Load the backgrounds list from a YAML file."""
        with open('config/backgrounds.yaml', 'r', encoding='utf-8') as bgs:
            self.backgrounds = yaml.safe_load(bgs)

    def load_iniswaps(self):
        """Load a list of characters for which INI swapping is allowed."""
        try:
            with open('config/iniswaps.yaml', 'r',
                      encoding='utf-8') as iniswaps:
                self.allowed_iniswaps = yaml.safe_load(iniswaps)
        except:
            logger.debug('Cannot find iniswaps.yaml')


    def load_gimps(self):
        with open('config/gimp.yaml', 'r', encoding='utf-8') as cfg:
            self.gimp_list = yaml.load(cfg)

    def load_ipranges(self):
        """Load a list of banned IP ranges."""
        try:
            with open('config/iprange_ban.txt', 'r',
                      encoding='utf-8') as ipranges:
                self.ipRange_bans = ipranges.read().splitlines()
        except:
            logger.debug('Cannot find iprange_ban.txt')

    def build_char_pages_ao1(self):
        """
        Cache a list of characters that can be used for the
        AO1 connection handshake.
        """
        self.char_pages_ao1 = [
            self.char_list[x:x + 10] for x in range(0, len(self.char_list), 10)
        ]
        for i in range(len(self.char_list)):
            self.char_pages_ao1[i // 10][i % 10] = '{}#{}&&0&&&0&'.format(
                i, self.char_list[i])

    def build_music_pages_ao1(self):
        """
        Cache a list of tracks that can be used for the
        AO1 connection handshake.
        """
        self.music_pages_ao1 = []
        index = 0
        # add areas first
        for area in self.area_manager.areas:
            self.music_pages_ao1.append(f'{index}#{area.name}')
            index += 1
        # then add music
        for item in self.music_list:
            self.music_pages_ao1.append('{}#{}'.format(index,
                                                       item['category']))
            index += 1
            for song in item['songs']:
                self.music_pages_ao1.append('{}#{}'.format(
                    index, song['name']))
                index += 1
        self.music_pages_ao1 = [
            self.music_pages_ao1[x:x + 10]
            for x in range(0, len(self.music_pages_ao1), 10)
        ]

    def build_music_list_ao2(self):
        """
        Cache a list of tracks that can be used for the
        AO2 connection handshake.
        """
        self.music_list_ao2 = []
        # add areas first
        for area in self.area_manager.areas:
            self.music_list_ao2.append(area.name)
            # then add music
        for item in self.music_list:
            self.music_list_ao2.append(item['category'])
            for song in item['songs']:
                self.music_list_ao2.append(song['name'])

    def is_valid_char_id(self, char_id):
        """
        Check if a character ID is a valid one.
        :param char_id: character ID
        :returns: True if within length of character list; False otherwise

        """
        return len(self.char_list) > char_id >= 0

    def get_char_id_by_name(self, name):
        """
        Get a character ID by the name of the character.
        :param name: name of character
        :returns: Character ID

        """
        for i, ch in enumerate(self.char_list):
            if ch.lower() == name.lower():
                return i
        raise ServerError('Character not found.')

    def get_song_data(self, music):
        """
        Get information about a track, if exists.
        :param music: track name
        :returns: tuple (name, length or -1)
        :raises: ServerError if track not found
        """
        for item in self.music_list:
            if item['category'] == music:
                return item['category'], -1
            for song in item['songs']:
                if song['name'] == music:
                    try:
                        return song['name'], song['length']
                    except KeyError:
                        return song['name'], -1
        raise ServerError('Music not found.')

    def send_all_cmd_pred(self, cmd, *args, pred=lambda x: True):
        """
        Broadcast an AO-compatible command to all clients that satisfy
        a predicate.
        """
        for client in self.client_manager.clients:
            if pred(client):
                client.send_command(cmd, *args)

    def broadcast_global(self, client, msg, as_mod=False):
        """
        Broadcast an OOC message to all clients that do not have
        global chat muted.
        :param client: sender
        :param msg: message
        :param as_mod: add moderator prefix (Default value = False)

        """
        char_name = client.char_name
        ooc_name = '{}[{}][{}]'.format('<dollar>G', client.area.abbreviation,
                                       char_name)
        if as_mod:
            ooc_name += '[M]'
        self.send_all_cmd_pred('CT',
                               ooc_name,
                               msg,
                               pred=lambda x: not x.muted_global)

    def send_modchat(self, client, msg):
        """
        Send an OOC message to all mods.
        :param client: sender
        :param msg: message

        """
        name = client.name
        ooc_name = '{}[{}][{}]'.format('<dollar>M', client.area.abbreviation,
                                       name)
        self.send_all_cmd_pred('CT', ooc_name, msg, pred=lambda x: x.is_mod)

    def broadcast_need(self, client, msg):
        """
        Broadcast an OOC "need" message to all clients who do not
        have advertisements muted.
        :param client: sender
        :param msg: message

        """
        char_name = client.char_name
        area_name = client.area.name
        area_id = client.area.abbreviation
        self.send_all_cmd_pred(
            'CT',
            '{}'.format(self.config['hostname']),
            '=== Advert ===\r\n{} in {} [{}] needs {}\r\n==============='.
            format(char_name, area_name, area_id, msg),
            '1',
            pred=lambda x: not x.muted_adverts)

    def send_arup(self, args):
        """Update the area properties for 2.6 clients.

        Playercount:
            ARUP#0#<area1_p: int>#<area2_p: int>#...
        Status:
            ARUP#1##<area1_s: string>##<area2_s: string>#...
        CM:
            ARUP#2##<area1_cm: string>##<area2_cm: string>#...
        Lockedness:
            ARUP#3##<area1_l: string>##<area2_l: string>#...

        :param args:

        """
        if len(args) < 2:
            # An argument count smaller than 2 means we only got the identifier of ARUP.
            return
        if args[0] not in (0, 1, 2, 3):
            return

        if args[0] == 0:
            for part_arg in args[1:]:
                try:
                    _sanitised = int(part_arg)
                except:
                    return
        elif args[0] in (1, 2, 3):
            for part_arg in args[1:]:
                try:
                    _sanitised = str(part_arg)
                except:
                    return

        self.send_all_cmd_pred('ARUP', *args, pred=lambda x: True)

    def refresh(self):
        """
        Refresh as many parts of the server as possible:
         - MOTD
         - Mod credentials (unmodding users if necessary)
         - Characters
         - Music
         - Backgrounds
         - Commands
         - Banlists
        """
        with open('config/config.yaml', 'r') as cfg:
            cfg_yaml = yaml.safe_load(cfg)
            self.config['motd'] = cfg_yaml['motd'].replace('\\n', ' \n')

            # Reload moderator passwords list and unmod any moderator affected by
            # credential changes or removals
            if isinstance(self.config['modpass'], str):
                self.config['modpass'] = {'default': {'password': self.config['modpass']}}
            if isinstance(cfg_yaml['modpass'], str):
                cfg_yaml['modpass'] = {'default': {'password': cfg_yaml['modpass']}}

            for profile in self.config['modpass']:
                if profile not in cfg_yaml['modpass'] or \
                   self.config['modpass'][profile] != cfg_yaml['modpass'][profile]:
                    for client in filter(
                            lambda c: c.mod_profile_name == profile,
                            self.client_manager.clients):
                        client.is_mod = False
                        client.mod_profile_name = None
                        database.log_misc('unmod.modpass', client)
                        client.send_ooc(
                            'Your moderator credentials have been revoked.')
            self.config['modpass'] = cfg_yaml['modpass']

        self.load_characters()
        self.load_iniswaps()
        self.load_music()
        self.load_backgrounds()
        self.load_ipranges()
        self.load_gimps()
        import server.commands
        importlib.reload(server.commands)
        server.commands.reload()
