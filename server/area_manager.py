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
import random
import time
from enum import Enum

import oyaml as yaml #ordered yaml
import os

from server import database
from server.exceptions import AreaError

from server.area import Area

from collections import OrderedDict

class AreaManager:
    """Holds the list of all areas."""

    def __init__(self, hub_manager, name):
        self.hub_manager = hub_manager
        self.areas = []
        self.owners = set()

        # prefs
        self._name = name
        self.abbreviation = self.abbreviate()
        self.move_delay = 0
        self.arup_enabled = True
        self.hide_clients = False
        self.info = ''
        self.can_gm = True
        self.music_ref = ''
        self.music_override = False
        # /prefs

        self.music_list = []
        self.replace_music = False

        # Save character information for character select screen ID's in the hub data
        # ex. {"1": {"keys": [1, 2, 3, 5], "fatigue": 100.0, "hunger": 34.0}, "2": {"keys": [4, 6, 8]}}
        self.character_data = {}

    @property
    def name(self):
        """Area's name string. Abbreviation is also updated according to this."""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self.abbreviation = self.abbreviate()

    @property
    def id(self):
        """Get area's index in the HubManager's 'hubs' list."""
        return self.hub_manager.hubs.index(self)

    @property
    def server(self):
        """Area's server. Accesses HubManager's 'server' property"""
        return self.hub_manager.server

    @property
    def clients(self):
        clients = set()
        for area in self.areas:
            clients = clients | area.clients
        return clients

    def abbreviate(self):
        """Abbreviate our name."""
        if self.name.lower().startswith("hub"):
            return "H" + self.name.split()[-1]
        if len(self.name.split()) > 1:
            return "".join(item[0].upper() for item in self.name.split())
        if len(self.name) > 3:
            return self.name[:3].upper()
        return self.name.upper()

    def load(self, hub):
        """
        Create all hub data from a YAML dictionary.
        :param hub: what to parse.

        """
        if 'hub' in hub:
            self.name = hub['hub']
        if 'abbreviation' in hub:
            self.abbreviation = hub['abbreviation']
        if 'move_delay' in hub:
            self.move_delay = hub['move_delay']
        if 'arup_enabled' in hub:
            self.arup_enabled = hub['arup_enabled']
        if 'hide_clients' in hub:
            self.hide_clients = hub['hide_clients']
        if 'info' in hub:
            self.info = hub['info']
        if 'can_gm' in hub:
            self.can_gm = hub['can_gm']
        if 'music_ref' in hub:
            self.music_ref = hub['music_ref']
        if 'music_override' in hub:
            self.music_override = hub['music_override']

        if 'character_data' in hub:
            try:
                self.load_character_data(hub['character_data'])
            except:
                print('Character data reference path invalid!')
        if 'areas' in hub:
            self.load_areas(hub['areas'])

        self.broadcast_area_list()

    def load_areas(self, areas):
        while len(self.areas) < len(areas):
            # Make sure that the area manager contains enough areas to update with new information
            self.create_area()
        i = 0
        for area in areas:
            if 'area' in area:
                self.areas[i].load(area)
                i += 1

    def save(self):
        hub = OrderedDict()
        hub['hub'] = self.name
        hub['abbreviation'] = self.abbreviation
        hub['move_delay'] = self.move_delay
        hub['arup_enabled'] = self.arup_enabled
        hub['hide_clients'] = self.hide_clients
        hub['info'] = self.info
        hub['can_gm'] = self.can_gm
        hub['music_ref'] = self.music_ref
        hub['music_override'] = self.music_override
        areas = []
        for area in self.areas:
            areas.append(area.save())
        hub['areas'] = areas
        return hub

    def clear_music(self):
        self.music_list.clear()
        self.music_ref = ''

    def load_music(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as stream:
                self.music_list = yaml.safe_load(stream)

            prepath = ''
            for item in self.music_list:
                # deprecated, use 'replace_music' area pref instead
                # if 'replace' in item:
                #    self.replace_music = item['replace'] == True
                if 'use_unique_folder' in item and item['use_unique_folder'] == True:
                    prepath = os.path.splitext(os.path.basename(path))[0] + '/'

                if 'category' not in item:
                    continue
                
                if 'songs' in item:
                    for song in item['songs']:
                        song['name'] = prepath + song['name']
        except ValueError:
            raise
        except AreaError:
            raise


    def load_character_data(self, path='config/character_data.yaml'):
        """
        Load all the character-specific information such as movement delay, keys, etc.
        :param path: filepath to the YAML file.

        """
        try:
            with open(path, 'r') as chars:
                data = yaml.safe_load(chars)
        except:
            raise AreaError(f'File path {path} is invalid!')

        try:
            self.character_data = data
        except:
            raise AreaError(f'Something went wrong while loading the character data!')

    def save_character_data(self, path='config/character_data.yaml'):
        """
        Save all the character-specific information such as movement delay, keys, etc.
        :param path: filepath to the YAML file.

        """
        try:
            with open(path, 'w', encoding='utf-8') as stream:
                yaml.dump(self.character_data, stream, default_flow_style=False)
        except:
            raise AreaError(f'File path {path} is invalid!')

    def get_character_data(self, c_id, key, default_value = None):
        """
        Obtain the character data from the Hub data.
        :param c_id: The Character Folder ID
        :param key: The key to search the value for
        :param default_value: What value should be returned if the look-up failed

        """
        if c_id not in self.character_data:
            return default_value
        if key not in self.character_data[c_id]:
            return default_value
        return self.character_data[c_id][key]

    def set_character_data(self, c_id, key, value):
        """
        Obtain the character data from the Hub data.
        :param c_id: The Character Folder ID
        :param key: The key to save over
        :param value: The value to save

        """
        if c_id not in self.character_data:
            self.character_data[c_id] = {}
        self.character_data[c_id][key] = value

    def create_area(self):
        """Create a new area instance and return it."""
        idx = len(self.areas)
        area = Area(self, f'Area {idx}')
        self.areas.append(area)
        return area

    def remove_area(self, area):
        """
        Remove an area instance.
        :param area: target area instance.
        
        """
        if not (area in self.areas):
            raise AreaError('Area not found.')
        # Make a copy because it can change size during iteration
        # (causes runtime error otherwise)
        if self.default_area() != area:
            target_area = self.default_area()
        else:
            try:
                target_area = self.get_area_by_id(1)
            except:
                raise AreaError('May not remove last existing area!')
        clients = area.clients.copy()
        for client in clients:
            client.set_area(target_area)
        self.areas.remove(area)

    def swap_area(self, area1, area2):
        """
        Swap area instances area1 and area2.
        :param area1: first area to swap.
        :param area2: second area to swap.
        
        """
        if not (area1 in self.areas):
            raise AreaError('First area not found.')
        if not (area2 in self.areas):
            raise AreaError('Second area not found.')
        a, b = self.areas.index(area1), self.areas.index(area2)
        # Swap 'em good
        self.areas[b], self.areas[a] = self.areas[a], self.areas[b]

    def add_owner(self, client):
        """
        Add a GM to the Hub.
        """
        self.owners.add(client)

        # Make sure the client's available areas are updated
        client.area.broadcast_area_list(client)

        # HAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHHAHAHAHAHA
        # This should be remade by only sending updates to those players
        # who would actually be affected, and all players who don't need
        # an update are ignored.
        self.send_arup_players()
        self.send_arup_status()
        self.send_arup_cms()
        self.send_arup_lock()
        # HAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHHAHAHAHAHA

        client.area.broadcast_evidence_list()

        self.broadcast_ooc(
            f'{client.char_name} [{client.id}] is GM in this hub now.')

    def remove_owner(self, client):
        """
        Remove a GM from the Hub.
        """
        self.owners.remove(client)

        # Make sure the client's available areas are updated
        client.area.broadcast_area_list(client)

        # HAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHHAHAHAHAHA
        # This should be remade by only sending updates to those players
        # who would actually be affected, and all players who don't need
        # an update are ignored.
        self.send_arup_players()
        self.send_arup_status()
        self.send_arup_cms()
        self.send_arup_lock()
        # HAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHHAHAHAHAHA

        client.area.broadcast_evidence_list()

        self.broadcast_ooc(
            f'{client.char_name} [{client.id}] is no longer GM in this hub.')

    def default_area(self):
        """Get the default area."""
        return self.areas[0]

    def get_area_by_name(self, name):
        """Get an area by name."""
        for area in self.areas:
            if area.name.lower() == name.lower():
                return area
        raise AreaError('Area not found.')

    def get_area_by_id(self, num):
        """Get an area by ID."""
        for area in self.areas:
            if area.id == num:
                return area
        raise AreaError('Area not found.')

    def get_area_by_abbreviation(self, abbr):
        """Get an area by abbreviation."""
        for area in self.areas:
            if area.abbreviation.lower() == abbr.lower():
                return area
        raise AreaError('Area not found.')

    def send_command(self, cmd, *args):
        """
        Broadcast an AO-compatible command to all areas and all clients in those areas.
        """
        for area in self.areas:
            area.send_command(cmd, *args)

    def send_remote_command(self, area_ids, cmd, *args):
        """
        Broadcast an AO-compatible command to a specified
        list of areas and their owners.
        :param area_ids: list of area IDs
        :param cmd: command name
        :param *args: command arguments
        """
        for a_id in area_ids:
            self.get_area_by_id(a_id).send_command(cmd, *args)
            self.get_area_by_id(a_id).send_owner_command(cmd, *args)

    def broadcast_area_list(self):
        """Global update of all areas for the client music lists in the hub."""
        for area in self.areas:
            area.broadcast_area_list()

    def broadcast_ooc(self, msg):
        """Broadcast an OOC message to all areas in this hub."""
        for area in self.areas:
            area.send_command('CT', area.server.config['hostname'], msg, '1')
        area.send_owner_command(
            'CT',
            '[ALL]' + area.server.config['hostname'],
            msg, '1')

    def send_arup_players(self):
        """Broadcast ARUP packet containing player counts."""
        if not self.arup_enabled:
            return
        players_list = [0]
        for client in self.server.client_manager.clients:
            for area in client.local_area_list:
                playercount = -1
                if not self.hide_clients and not area.hide_clients:
                    playercount = len([c for c in area.clients if not c.hidden])
                players_list.append(playercount)
            self.server.send_arup(client, players_list)

    def send_arup_status(self):
        """Broadcast ARUP packet containing area statuses."""        
        if not self.arup_enabled:
            return
        status_list = [1]
        for client in self.server.client_manager.clients:
            for area in client.local_area_list:
                status_list.append(area.status)
            self.server.send_arup(client, status_list)

    def send_arup_cms(self):
        """Broadcast ARUP packet containing area CMs."""
        if not self.arup_enabled:
            return        
        cms_list = [2]
        for client in self.server.client_manager.clients:
            for area in client.local_area_list:
                cm = 'FREE'
                if len(area.owners) > 0:
                    cm = area.get_cms()
                cms_list.append(cm)
            self.server.send_arup(client, cms_list)

    def send_arup_lock(self):
        """Broadcast ARUP packet containing the lock status of each area."""
        if not self.arup_enabled:
            return        
        lock_list = [3]
        for client in self.server.client_manager.clients:
            for area in client.local_area_list:
                lock_list.append(area.is_locked.name)
            self.server.send_arup(client, lock_list)
