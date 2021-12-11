# KFO-Server, an Attorney Online server
#
# Copyright (C) 2020 Crystalwarrior <varsash@gmail.com>
#
# Derivative of tsuserver3, an Attorney Online server. Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
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

import re
import string
import time
import math
import os
from heapq import heappop, heappush

from enum import Enum

from server import database
from server.constants import TargetType
from server.exceptions import ClientError, AreaError, ServerError

import oyaml as yaml #ordered yaml

class ClientManager:
    """Holds the list of all clients currently connected to the server."""
    class Client:
        """Represents a single instance of a user.

        Clients may only belong to a single area.
        """
        def __init__(self, server, transport, user_id, ipid):
            self.is_checked = False
            self.transport = transport
            self.hdid = ''
            self.id = user_id
            self.char_id = -1
            self.area = server.hub_manager.default_hub().default_area()
            self.server = server
            self.name = ''
            self.fake_name = ''
            self.is_mod = False
            self.mod_profile_name = None
            self.is_dj = True
            self.can_wtce = True
            self.pos = ''
            self.evi_list = []
            self.disemvowel = False
            self.shaken = False
            self.charcurse = []
            self.muted_global = False
            self.muted_adverts = False
            self.is_muted = False
            self.is_ooc_muted = False
            self.pm_mute = False
            self.mod_call_time = 0
            self.ipid = ipid
            self.version = ''

            # Pairing stuff
            self.charid_pair = -1
            self.offset_pair = 0
            self.last_sprite = ''
            self.flip = 0
            self.claimed_folder = ''

            # Casing stuff
            self.casing_cm = False
            self.casing_cases = ''
            self.casing_def = False
            self.casing_pro = False
            self.casing_jud = False
            self.casing_jur = False
            self.casing_steno = False
            self.case_call_time = 0

            # flood-guard stuff
            self.mus_counter = 0
            self.mus_mute_time = 0
            self.mus_change_time = [
                x * self.server.config['music_change_floodguard']
                ['interval_length']
                for x in range(self.server.config['music_change_floodguard']
                               ['times_per_interval'])
            ]
            self.wtce_counter = 0
            self.wtce_mute_time = 0
            self.wtce_time = [
                x * self.server.config['wtce_floodguard']['interval_length']
                for x in range(self.server.config['wtce_floodguard']
                               ['times_per_interval'])
            ]
            # security stuff
            self.clientscon = 0
            self.gm_save_time = 0

            # movement system stuff
            self.last_move_time = 0
        
            # client status stuff
            self._showname = ''
            self.blinded = False
            self._hidden = False
            self.hidden_in = None
            self.sneaking = False
            self.listen_pos = None
            self.following = None
            self.edit_ambience = False

            # 0 = listen to NONE
            # 1 = listen to IC
            # 2 = listen to OOC
            # 3 = Listen to ALL
            self.remote_listen = 2

            # if True, this char's msg will be narrating over current IC visuals without showing a character (AO2.9.1+)
            self.narrator = False
            # if True, this char's msg will be replaced with ../misc/blank
            self.blankpost = False
            # if True, this char's msg will be narrating over current IC visuals without showing a character, but only to yourself (AO2.9.1+)
            self.firstperson = False

            # a list of all areas the client can currently see
            self.local_area_list = []
            # a list of all songs the client can currently see
            self.local_music_list = []
            # reference to the storage/musiclists/ref.yaml for displaying purposes
            self.music_ref = ''
            # a music list that was loaded manually by the client
            self.music_list = []
            # whether or not to replace music list with ours
            self.replace_music = False
            # list of areas to broadcast the message, music and judge buttons to
            self.broadcast_list = []
            # Whether we're viewing hub list or not in the A/M area list
            self.viewing_hub_list = False

        def send_raw_message(self, msg):
            """
            Send a raw packet over TCP.
            :param msg: string to send
            """
            self.transport.write(msg.encode('utf-8'))

        def send_command(self, command, *args):
            """
            Compose and send an AO-compatible message, with arguments
            delimited by `#` and ending with `#%`.
            :param command: command name
            :param *args: list of arguments
            """
            if args:
                if command == 'MS':
                    for evi_num in range(len(self.evi_list)):
                        if self.evi_list[evi_num] == args[11]:
                            lst = list(args)
                            lst[11] = evi_num
                            args = tuple(lst)
                            break
                self.send_raw_message(
                    f'{command}#{"#".join([str(x) for x in args])}#%')
            else:
                self.send_raw_message(f'{command}#%')

        def send_ooc(self, msg):
            """
            Send an out-of-character message to the client.
            :param msg: message to send
            """
            self.send_command('CT', self.server.config['hostname'], msg, '1')

        def send_motd(self):
            """Send the message of the day to the client."""
            motd = self.server.config['motd']
            if motd != '':
                self.send_ooc(f'=== MOTD ===\r\n{motd}\r\n=============')

        def send_hub_info(self):
            """Send the hub info to the client."""
            info = self.area.area_manager.info
            if info != '':
                self.send_ooc(f'=== HUB [{self.area.area_manager.id}] {self.area.area_manager.name} INFO ===\r\n{info}\r\n=============')

        def send_player_count(self):
            """
            Send a message stating the number of players currently online
            to the client.
            """
            players = self.server.player_count
            limit = self.server.config['playerlimit']
            self.send_ooc(f'{players}/{limit} players online.')

        def is_valid_name(self, name):
            """
            Check if the given string is valid as an OOC name.
            :param name: name to check
            """
            printset = set(string.ascii_letters + string.digits + "*~ -_.',")
            name_ws = name.replace(' ', '')
            if not name_ws or name_ws.isdigit():
                return False
            if not set(name_ws).issubset(printset): #illegal chars in ooc name
                return False
            for client in self.server.client_manager.clients:
                # Unless they're our multiclient, we may only have a unique name
                if self.ipid != client.ipid and client.name == name:
                    return False
            return True

        def disconnect(self):
            """Disconnect the client gracefully."""
            self.transport.close()

        def change_character(self, char_id, force=False):
            """
            Change the client's character or force the character selection
            screen to appear for the client.
            :param char_id: character ID to switch to
            :param force: whether or not the client is forced to switch
            to another character if the target character is not available
            (Default value = False)
            """
            # If it's -1, we want to be the spectator character.
            if char_id != -1:
                if not self.server.is_valid_char_id(char_id):
                    raise ClientError('Invalid character ID.')
                if not self.is_mod and self not in self.area.owners:
                    if len(self.charcurse) > 0:
                        if not char_id in self.charcurse:
                            raise ClientError('Character not available.')
                        force = True
                    if not self.area.is_char_available(char_id):
                        if force:
                            for client in self.area.clients:
                                if client.char_id == char_id:
                                    client.char_select()
                        else:
                            raise ClientError('Character not available.')
            # We're trying to spectate out of our own accord and either hub or area does not allow spectating.
            if char_id == -1 and not (self.area.area_manager.can_spectate and self.area.can_spectate) and not self.is_mod and not (self in self.area.owners) and not force:
                if not self.area.area_manager.can_spectate:
                    raise ClientError('Cannot spectate in this hub!')
                raise ClientError('Cannot spectate in this area!')
            old_char = self.char_name
            arup = (self.char_id == -1 or char_id == -1) and self.char_id != char_id
            self.char_id = char_id
            self.pos = ''
            self.send_command('PV', self.id, 'CID', self.char_id)
            # Commented out due to potentially causing clientside lag...
            # self.area.send_command('CharsCheck',
            #                        *self.get_available_char_list())
            if arup:
                self.area.area_manager.send_arup_players()
            new_char = self.char_name
            database.log_area('char.change', self, self.area,
                message={'from': old_char, 'to': new_char})

        def change_music_cd(self):
            """
            Check if the client can change music or not.
            :returns: how many seconds the client must wait to change music
            """
            if self.is_mod or self in self.area.owners:
                return 0

            # Get a list of unique IPIDs from the current area to determine if the "player" is truly alone in an area (spectators or hidden players don't count).
            players = set([c.ipid for c in self.area.clients if not c.hidden])
            # If we're alone in the area, we don't get spam protection.
            if len(players) <= 1:
                return 0

            if self.mus_mute_time:
                if time.time() - self.mus_mute_time < self.server.config[
                        'music_change_floodguard']['mute_length']:
                    return self.server.config['music_change_floodguard'][
                        'mute_length'] - (time.time() - self.mus_mute_time)
                else:
                    self.mus_mute_time = 0
            times_per_interval = self.server.config['music_change_floodguard'][
                'times_per_interval']
            interval_length = self.server.config['music_change_floodguard'][
                'interval_length']
            if time.time() - self.mus_change_time[
                (self.mus_counter - times_per_interval + 1) %
                    times_per_interval] < interval_length:
                self.mus_mute_time = time.time()
                return self.server.config['music_change_floodguard'][
                    'mute_length']
            self.mus_counter = (self.mus_counter + 1) % times_per_interval
            self.mus_change_time[self.mus_counter] = time.time()
            return 0

        def change_music(self, song, cid, showname='', effects=0, loop=True):
            if self.is_muted:  # Checks to see if the client has been muted by a mod
                self.send_ooc(
                    'You are muted by a moderator.')
                return
            if not self.is_dj:
                self.send_ooc(
                    'You were blockdj\'d by a moderator.')
                return
            if cid != self.char_id:
                return

            try:
                if song == "~stop.mp3" or self.server.get_song_is_category(self.construct_music_list(), song):
                    name, length = "~stop.mp3", 0
                else:
                    try:
                        name, length = self.server.get_song_data(
                            self.construct_music_list(), song)
                    except ServerError:
                        if self.is_mod or self in self.area.owners:
                            name = song
                            length = -1
                        else:
                            raise
                if not loop:
                    length = 0

                target_areas = [self.area]
                if len(self.broadcast_list) > 0 and (self.is_mod or self in self.area.owners):
                    try:
                        a_list = ', '.join([str(a.id) for a in self.broadcast_list])
                        self.send_ooc(f'Broadcasting to areas {a_list}')
                        target_areas = self.broadcast_list
                    except (AreaError, ValueError):
                        self.send_ooc('Your broadcast list is invalid! Do /clear_broadcast to reset it and /broadcast <id(s)> to set a new one.')
                        return

                for area in target_areas:
                    if area.cannot_ic_interact(self):
                        self.send_ooc(
                            f'You are not on area [{area.id}] {area.name} invite list, and thus, you cannot change music!'
                        )
                        continue
                    if not self.is_mod and not self in area.owners and not area.can_dj:
                        self.send_ooc(
                            f'You cannot change music in area [{area.id}] {area.name}!'
                        )
                        continue
                    if self.edit_ambience:
                        if self.is_mod or self in area.owners:
                            area.set_ambience(name)
                            self.send_ooc(
                                f'Setting area [{area.id}] {area.name} ambience to {name}.')
                            continue
                        else:
                            self.edit_ambinece = False

                    # Showname info
                    if showname != '':
                        if len(showname) > 0 and not area.showname_changes_allowed and not self.is_mod and not self in area.owners:
                            self.send_ooc(
                                f'Showname changes are forbidden in area [{area.id}] {area.name}!'
                            )
                            continue

                    # Effects info
                    effects = int(effects)
                    
                    # Jukebox check
                    if area.jukebox and not self.is_mod and not self in area.owners:
                        area.add_jukebox_vote(self, name,
                                                        length, showname)
                        database.log_area('jukebox.vote', self, area, message=name)
                    else:
                        if self.change_music_cd():
                            self.send_ooc(
                                f'You changed song too many times. Please try again after {int(self.change_music_cd())} seconds.'
                            )
                            return
                        area.play_music(name, self.char_id,
                                                    length, showname, effects)
                        area.add_music_playing(self, name, showname)
                # We only make one log entry to not CBT the log list. TODO: Broadcast logs
                database.log_area('music', self, self.area, message=name)
            except ServerError:
                if self.music_ref != '':
                    self.send_ooc(f'Error: song {song} was not accepted! View acceptable music by resetting your client\'s using /musiclist.')
                else:
                    self.send_ooc(f'Error: song {song} isn\'t recognized by server!')

        def wtce_mute(self):
            """
            Check if the client can use WT/CE or not.
            :returns: how many seconds the client must wait to use WT/CE
            """
            if self.is_mod or self in self.area.owners:
                return 0
            if self.wtce_mute_time:
                if time.time() - self.wtce_mute_time < self.server.config[
                        'wtce_floodguard']['mute_length']:
                    return self.server.config['wtce_floodguard'][
                        'mute_length'] - (time.time() - self.wtce_mute_time)
                else:
                    self.wtce_mute_time = 0
            times_per_interval = self.server.config['wtce_floodguard'][
                'times_per_interval']
            interval_length = self.server.config['wtce_floodguard'][
                'interval_length']
            if time.time() - self.wtce_time[
                (self.wtce_counter - times_per_interval + 1) %
                    times_per_interval] < interval_length:
                self.wtce_mute_time = time.time()
                return self.server.config['music_change_floodguard'][
                    'mute_length']
            self.wtce_counter = (self.wtce_counter + 1) % times_per_interval
            self.wtce_time[self.wtce_counter] = time.time()
            return 0

        def reload_character(self):
            """Reload the state of the current character."""
            try:
                self.change_character(self.char_id, True)
            except ClientError:
                raise

        def clear_music(self):
            self.music_ref = ''
            self.music_list.clear()

        def load_music(self, path):
            """Load a music list from a path. Use it for the local music list and reload it."""
            #TODO: Move the musiclist parsing function to tsuserver3.py or something
            try:
                with open(path, 'r', encoding='utf-8') as stream:
                    music_list = yaml.safe_load(stream)

                prepath = ''
                for item in music_list:
                    if 'use_unique_folder' in item and item['use_unique_folder'] == True:
                        prepath = os.path.splitext(os.path.basename(path))[0] + '/'

                    if 'category' not in item:
                        continue

                    for song in item['songs']:
                        song['name'] = prepath + song['name']
                self.music_list = music_list
            except ValueError:
                raise
            except AreaError:
                raise
        
        def construct_music_list(self):
            """
            Obtain the most relevant music list for the client.
            :param client_music: when True, include the client's music in the equation.
            """
            # Server music list
            song_list = self.server.music_list

            # Hub music list
            if self.area.area_manager.music_ref != '' and len(self.area.area_manager.music_list) > 0:
                if self.area.area_manager.replace_music:
                    song_list = self.area.area_manager.music_list
                else:
                    song_list = song_list + self.area.area_manager.music_list

            # Area music list
            if self.area.music_ref != '' and self.area.music_ref != self.area.area_manager.music_ref and len(self.area.music_list) > 0:
                if self.area.replace_music:
                    song_list = self.area.music_list
                else:
                    song_list = song_list + self.area.music_list

            # Client music list
            if self.area.client_music and self.area.area_manager.client_music and \
               self.music_ref != '' and not (self.music_ref in [self.area.music_ref, self.area.area_manager.music_ref]) and \
               len(self.music_list) > 0:
                if self.replace_music:
                    song_list = self.music_list
                else:
                    song_list = song_list + self.music_list

            return song_list

        def refresh_music(self):
            """
            Rebuild the client's music list, updating the local music list if there was a change.
            """
            song_list = self.construct_music_list()
            if self.local_music_list != song_list:
                self.reload_music_list(song_list)

        def reload_music_list(self, music=[]):
            """
            Rebuild the music list with the provided array, or the server music list as a whole.
            """
            song_list = []

            if (len(music) > 0):
                song_list = music
            else:
                song_list = self.server.music_list

            self.local_music_list = music
            song_list = self.server.build_music_list_ao2(song_list)
            # KEEP THE ASTERISK
            self.send_command('FM', *song_list)

        def reload_area_list(self, areas=[]):
            """
            Rebuild the area list according to provided areas list.
            """
            if not self.area.area_manager.arup_enabled:
                area_list = [f'[HUB: {self.area.area_manager.id}] {self.area.area_manager.name}\n Double-Click me to see Hubs\n  _______']
            else:
                area_list = [f'[HUB: {self.area.area_manager.id}] {self.area.area_manager.name}']
            if (len(areas) > 0):
                # This is where we can handle all the 'rendering', such as extra info etc.
                for area in areas:
                    a = area.name
                    if not self.area.area_manager.arup_enabled:
                        a = f'[{area.id}] {area.name}'
                    area_list.append(a)

            self.local_area_list = areas
            # If we're currently viewing hub list, just update our local area list
            if self.viewing_hub_list:
                return
            # KEEP THE ASTERISK
            self.send_command('FA', *area_list)

        def set_area(self, area, target_pos=''):
            """
            Unsafe method to set the client's area, sending all the relevant packet info.
            Ignores preconditions like lock state, accessibility, char availability etc.
            :param area: area to switch to
            :param target_pos: which position to target in the new area
            """
            # This person switched hubs just now.
            if self.area.area_manager != area.area_manager:
                # Make sure a single person can't hoard all the hubs
                if self in self.area.area_manager.owners:
                    self.area.area_manager.remove_owner(self)
                # Don't allow multi-hub CMing either
                for a in self.area.area_manager.areas:
                    if self in a.owners:
                        a.remove_owner(self)
            if self in self.area.clients:
                self.area.remove_client(self)
            self.area = area
            if len(self.area.pos_lock) > 0 and not (target_pos in self.area.pos_lock):
                target_pos = self.area.pos_lock[0]
            if self.area.dark:
                target_pos = self.area.pos_dark
            if self not in self.area.clients:
                self.area.new_client(self)
            if target_pos != '':
                self.pos = target_pos

            # Make sure the client's available areas are updated
            self.area.broadcast_area_list(self)

            self.area.area_manager.send_arup_players()

            if self.viewing_hub_list:
              for hub in self.server.hub_manager.hubs:
                count = 0
                for a in hub.areas:
                    for c in a.clients:
                        if not a.hide_clients and not c.hidden:
                           count = count + 1
                hub.count = count
              self.send_command('FA', *['{ Hubs }\n Double-Click me to see Areas\n  _______', *[f'[{hub.id}] {hub.name} (users: {hub.count})' for hub in self.server.hub_manager.hubs]])
            
            # Update everyone's available characters list
            # Commented out due to potentially causing clientside lag...
            # self.area.send_command('CharsCheck',
            #                        *self.get_available_char_list())
            # Get defense HP bar
            self.send_command('HP', 1, self.area.hp_def)
            # Get prosecution HP bar
            self.send_command('HP', 2, self.area.hp_pro)

            # Send the background information
            if self.area.dark:
                self.send_command('BN', self.area.background_dark, self.pos)
            else:
                self.send_command('BN', self.area.background, self.pos)

            if len(self.area.pos_lock) > 0:
                #set that juicy pos dropdown
                self.send_command('SD', '*'.join(self.area.pos_lock))
            # Send the evidence information
            self.send_command('LE', *self.area.get_evidence_list(self))
            
            # Judge buttons are client-sided by default.
            jd = -1
            # This area won't let us use judge buttons unless we have privileges.
            if not self.area.can_wtce:
                # We can't use judge buttons, unless...
                jd = 0
                if self in self.area.owners or self.is_mod:
                    # We are a CM or Mod!
                    jd = 1
            if self in self.area.area_manager.owners:
                # We are a GM - we have supreme control over the hub. Give us judge buttons at all times!
                jd = 1
            if not self.can_wtce:
                # aw man we were muted by a mod we can't use wtce period :(
                jd = 0
            self.send_command('JD', jd)
            self.refresh_music()
            msg = f'Changed to area: [{self.area.id}] {self.area.name}.'
            if self.area.desc != '' and not self.blinded:
                desc = self.area.desc[:128]
                if len(self.area.desc) > len(desc):
                    desc += "... Use /desc to read the rest."
                msg += f'\nDescription: {desc}'
            self.send_ooc(msg)

            # We failed to enter the same area as whoever we've been following, break the follow
            if self.following != None and not (self.following in self.area.clients):
                self.unfollow()

        def can_access_area(self, area):
            return self.area == area or len(self.area.links) <= 0 or (str(area.id) in self.area.links and \
                    (len(self.area.links[str(area.id)]["evidence"]) <= 0 or \
                        self.hidden_in in self.area.links[str(area.id)]["evidence"]))

        def try_access_area(self, area):
            if self.area.locked and not self in self.area.owners and not self.id in self.area.invite_list:
                raise ClientError('Current area is locked!')

            if len(self.area.links) > 0:
                if not str(area.id) in self.area.links:
                    raise ClientError('Area is inaccessible!')

                if str(area.id) in self.area.links:
                    link = self.area.links[str(area.id)]
                    # Link requires us to be inside a piece of evidence
                    if len(link["evidence"]) > 0:
                        if not (self.hidden_in in link["evidence"]):
                            raise ClientError('Area is inaccessible!')
                    # Our path is locked :(
                    if link["locked"]:
                        raise ClientError('Path is locked!')

            if area.locked and not self.id in area.invite_list:
                raise ClientError('Area is locked!')

            if area.max_players > 0:
                players = len([x for x in area.clients if (not x in area.owners and not x.is_mod and not x.hidden)])
                if players >= area.max_players:
                    raise ClientError('Area is full!')
            elif area.max_players == 0:
                raise ClientError('Area cannot be accessed by normal means!')

        def change_area(self, area, password=''):
            """
            Switch the client to another area if it's accessible.
            :param area: area to switch to
            """
            if self.area == area:
                raise ClientError(f'Failed to enter [{area.id}] {area.name}: User already in specified area.')
            allowed = self.is_mod or self in area.owners or self.char_id == -1 or area == area.area_manager.default_area()
            if not allowed:
                try:
                    self.try_access_area(area)
                except ClientError as ex:
                    self.send_ooc(f'Failed to enter [{area.id}] {area.name}: {ex}')
                    return

                if (area.password != '' and password != area.password) or (
                    len(self.area.links) > 0 and str(area.id) in self.area.links and self.area.links[str(area.id)]["password"] != '' and password != self.area.links[str(area.id)]["password"]):
                    raise ClientError(f'Failed to enter [{area.id}] {area.name}: Incorrect password! Use /pw <id> [password]')

            if self.char_id == -1 and not (area.area_manager.can_spectate and area.can_spectate) and not self.is_mod and not self in area.owners:
                if not area.area_manager.can_spectate:
                    raise ClientError(f'Failed to enter [{area.id}] {area.name}: Cannot spectate in this hub!')
                raise ClientError(f'Failed to enter [{area.id}] {area.name}: Cannot spectate that area!')

            target_pos = ''
            if len(self.area.links) > 0:
                if str(area.id) in self.area.links:
                    # Get that link reference
                    link = self.area.links[str(area.id)]

                    if self.hidden_in in link["evidence"]:
                        self.hide(False, hidden=True)

                    target_pos = link["target_pos"]

            if self.hidden_in != None:
                # You gotta unhide first lol
                self.hide(False)
                self.area.broadcast_area_list(self)
                raise ClientError(f'Failed to enter [{area.id}] {area.name}: You had to leave your hiding spot!')

            delay = self.area.time_until_move(self)
            if not allowed and delay > 0:
                sec = int(math.ceil(delay * 0.001))
                raise ClientError(f'Failed to enter [{area.id}] {area.name}: You need to wait {sec} seconds until you can move again.')

            # Mods and area owners can be any character regardless of availability
            if not (self.is_mod or self in area.owners or self.char_id == -1) and not area.is_char_available(self.char_id):
                self.check_char_taken(area)

            old_area = self.area
            self.set_area(area, target_pos)
            self.last_move_time = round(time.time() * 1000.0)

            for c in self.server.client_manager.clients:
                # If target c is following us
                if c.following == self:
                    if self.area.area_manager != c.area.area_manager:
                        # The person we're following may be trying to sneak away from us.
                        c.unfollow(silent = not allowed and (self.hidden or self.sneaking))
                        continue
                    # If they're still in the same hub, we're not hidden/sneaking or they're a mod, gm or cm
                    # Attempt to transfer to their area
                    try:
                        c.change_area(area)
                        c.send_ooc(
                            f'Following [{self.id}] {self.showname} to [{area.id}] {area.name}.')
                    # Something obstructed us.
                    except ClientError:
                        c.send_ooc(
                            f'Cannot follow [{self.id}] {self.showname} to [{area.id}] {area.name}!')
                        c.unfollow(silent=True)
                        raise

            reason = ''
            if not self.area.dark and not self.area.force_sneak and not self.sneaking and not self.hidden:
                if not old_area.dark and not old_area.force_sneak:
                    if old_area.area_manager == self.area.area_manager:
                        for c in old_area.clients:
                            # Check if the GMs should really see this msg
                            if c in old_area.owners and c.remote_listen in [2, 3]:
                                continue
                            c.send_command('CT', self.server.config['hostname'],
                                            f'[{self.id}] {self.showname} leaves to [{self.area.id}] {self.area.name}.', '1')
                    else:
                        old_area.send_command('CT', self.server.config['hostname'],
                                                f'[{self.id}] {self.showname} leaves to Hub [{self.area.area_manager.id}] {self.area.area_manager.name}.', '1')
                        old_area.send_owner_command('CT', self.server.config['hostname'],
                                                f'[{self.id}] {self.showname} leaves to Hub [{self.area.area_manager.id}] {self.area.area_manager.name}', '1')

                desc = '.'
                if self.desc != '':
                    desc = ': ' + self.desc
                    # Find the first sentence (assuming it ends in a period).
                    if desc.find('.') != -1:
                        desc = ' ' + self.desc[:desc.find('.') + 1]
                    # Limit that to 64 chars
                    desc = desc[:64]
                    if len(self.desc) > 64:
                        desc += f'... Use /chardesc {self.id} to read the rest.'
                if old_area.area_manager == self.area.area_manager:
                    self.area.send_command('CT', self.server.config['hostname'],
                                    f'[{self.id}] {self.showname} enters from [{old_area.id}] {old_area.name}{desc}', '1')
                else:
                    self.area.send_command('CT', self.server.config['hostname'],
                                    f'[{self.id}] {self.showname} enters from Hub [{old_area.area_manager.id}] {old_area.area_manager.name}{desc}', '1')
                    self.area.send_owner_command('CT', self.server.config['hostname'],
                                    f'[{self.id}] {self.showname} enters from Hub [{old_area.area_manager.id}] {old_area.area_manager.name}', '1')
            else:
                if self.sneaking:
                    reason = ' (sneaking)'
                if self.hidden:
                    reason = ' (hidden)'
                if self.area.force_sneak:
                    reason = ' (new area forces sneaking)'
                if self.area.dark:
                    reason = ' (new area is dark)'
                self.send_ooc(
                    f'Changed area unannounced{reason}.')
                for c in self.area.owners:
                    if old_area.area_manager == self.area.area_manager:
                        if c in self.area.clients:
                            c.send_ooc(f'[{self.id}] {self.showname} enters unannounced from [{old_area.id}] {old_area.name}{reason}')
                    else:
                        c.send_ooc(f'[{self.id}] {self.showname} enters unannounced from Hub [{old_area.area_manager.id}] {old_area.area_manager.name}{reason}')

                if old_area.area_manager != self.area.area_manager:
                    for c in old_area.owners:
                        c.send_ooc(f'[{self.id}] {self.showname} leaves unannounced to Hub [{self.area.area_manager.id}] {self.area.area_manager.name}{reason}')

            if old_area.area_manager == self.area.area_manager:
                self.area.send_owner_command('CT', self.server.config['hostname'],
                                    f'[{self.id}] {self.showname} moves from [{old_area.id}] {old_area.name} to [{self.area.id}] {self.area.name}.{reason}', '1')

            if self.area.cannot_ic_interact(self):
                self.send_ooc(
                    'This area is muted - you cannot talk in-character unless invited.'
                )

        def get_area_list(self, hidden=False, unlinked=False):
            area_list = []
            for area in self.area.area_manager.areas:
                if self.area != area:
                    if not hidden and area.hidden:
                        continue
                    if len(self.area.links) > 0:
                        if not (str(area.id) in self.area.links):
                            if not unlinked:
                                continue
                        if not hidden and self.area.links[str(area.id)]["hidden"] == True:
                            continue
                        if not hidden and len(self.area.links[str(area.id)]["evidence"]) > 0 and not self.hidden_in in self.area.links[str(area.id)]["evidence"]:
                            continue

                area_list.append(area)

            return area_list

        def check_char_taken(self, area):
            try:
                new_char_id = area.get_rand_avail_char_id()
            except AreaError:
                raise ClientError('No available characters in that area.')

            self.change_character(new_char_id)
            self.send_ooc(
                f'Character taken, switched to {self.char_name}.')
            return new_char_id

        def send_area_list(self, full=False):
            """Send a list of areas over OOC."""
            msg = '=== Areas ==='
            area_list = self.get_area_list(full, full)
            for _, area in enumerate(area_list):
                users = ''
                if not area.hide_clients and not area.area_manager.hide_clients:
                    clients = area.clients
                    if not full:
                        clients = [c for c in area.clients if not c.hidden]
                    users = len(clients)
                    users = f'(users: {users}) '
                status = ''
                if self.area.area_manager.arup_enabled:
                    status = f'[{area.status}]'
                owner = ''
                if len(area._owners) > 0:
                    owner = f'[CM(s): {area.get_owners()}]'
                hidden = '📦' if area.hidden else ''
                locked = '🔒' if area.locked else ''
                pathlocked = '🚧' if str(area.id) in self.area.links and self.area.links[str(area.id)]["locked"] else ''
                passworded = '🔑' if area.password != '' else ''
                muted = '🔇' if area.muted else ''
                msg += '\r\n'
                if self.area == area:
                    msg += '* '
                if not self.can_access_area(area):
                    msg += '-x- '
                msg += f'[{area.id}] {area.name} {users}{status}{owner}{hidden}{locked}{pathlocked}{passworded}{muted}'
            self.send_ooc(msg)

        def get_area_info(self, area_id, mods, afk_check):
            """
            Get information about a specific area.
            :param area_id: area ID
            :param mods: limit player list to mods
            :param afk_check: Limit player list to afks
            :returns: information as a string
            """
            info = '\r\n'
            try:
                area = self.area.area_manager.get_area_by_id(area_id)
            except AreaError:
                raise

            if afk_check:
                player_list = area.afkers
            else:
                player_list = area.clients
            
            if not self.is_mod and not self in area.owners:
                # We exclude hidden players here because we don't want them to count for the user count
                player_list = [c for c in player_list if not c.hidden]
            status = ''
            if self.area.area_manager.arup_enabled:
                status = f' [{area.status}]'
            hidden = '📦' if area.hidden else ''
            locked = '🔒' if area.locked else ''
            passworded = '🔑' if area.password != '' else ''
            muted = '🔇' if area.muted else ''
            dark = '🌑' if area.dark else ''
            info += f'=== [{area.id}] {area.name} (users: {len(player_list)}) {status}{hidden}{locked}{passworded}{muted}{dark}==='

            sorted_clients = []
            for client in player_list:
                if (not mods) or client.is_mod:
                    sorted_clients.append(client)
            if not sorted_clients:
                return ''
            # Sort the client list alphabetically based on the showname/charfolder name
            sorted_clients = sorted(sorted_clients,
                                    key=lambda x: x.showname)
            # Afterwards, sort the client list based on their unique role or status
            sorted_clients = sorted(sorted_clients,
                                    key=lambda x: 1 if (x in area.afkers) else 2 if x.hidden else 3 if x.char_id == -1 else 4 if (x in area._owners) else 5 if (x in area.area_manager.owners) else 6 if x.is_mod else 0)
            for c in sorted_clients:
                info += '\r\n'
                if c.is_mod:
                    info += '[M]'
                elif c in area.area_manager.owners:
                    info += '[GM]'
                elif c in area._owners:
                    info += '[CM]'
                if c in area.afkers:
                    info += '💤'
                if c.hidden:
                    name = ''
                    if c.hidden_in != None:
                        name = f':{c.area.evi_list.evidences[c.hidden_in].name}'
                    info += f'📦{name}'
                info += f'[{c.id}] '
                if c.showname != c.char_name:
                    info += f'"{c.showname}" ({c.char_name})'
                else:
                    info += f'{c.showname}'
                if c.pos != '':
                    info += f' <{c.pos}>'
                if self.is_mod:
                    info += f' ({c.ipid})'
                if c.name != '' and (self.is_mod or self in area.owners):
                    info += f': {c.name}'
            return info

        def send_area_info(self, area_id, mods, afk_check=False):
            """
            Send information over OOC about a specific area.
            :param area_id: area ID
            :param mods: limit player list to mods
            :param afk_check: Limit player list to afks
            """
            # if area_id is -1 then return all areas. If mods is True then return only mods
            info = ''
            if area_id == -1:
                # all areas info
                cnt = 0
                info = '\n== Area List =='
                for i in range(len(self.area.area_manager.areas)):
                    area = self.area.area_manager.areas[i]
                    if afk_check:
                        client_list = area.afkers
                    else:
                        client_list = area.clients
                    if not self.is_mod and not self in area.owners:
                        # We exclude hidden players here because we don't want them to count for the user count
                        client_list = [c for c in client_list if not c.hidden]
                    area_info = self.get_area_info(i, mods, afk_check)
                    if len(client_list) > 0 or len(
                               self.area.area_manager.areas[i].owners) > 0:
                        cnt += len(client_list)
                        info += f'{area_info}'
                if afk_check:
                    info = f'Current AFK-ers: {cnt}{info}'
                else:
                    info = f'Current online: {cnt}{info}'
            else:
                try:
                    area = self.area.area_manager.areas[area_id]
                    if afk_check:
                        client_list = area.afkers
                    else:
                        client_list = area.clients
                    if not self.is_mod and not self in area.owners:
                        # We exclude hidden players here because we don't want them to count for the user count
                        client_list = [c for c in client_list if not c.hidden]
                    area_info = self.get_area_info(area_id, mods, afk_check)
                    area_client_cnt = len(client_list)
                    if afk_check:
                        info = f'People AFK-ing in this area: {area_client_cnt}'
                    else:
                        info = f'People in this area: {area_client_cnt}'
                    info += area_info

                except AreaError:
                    raise
            self.send_ooc(info)

        def send_hub_list(self):
            msg = '=== Hubs ==='
            for hub in self.server.hub_manager.hubs:
                owner = 'FREE'
                if len(hub.owners) > 0:
                    owner = hub.get_gms()
                msg += '\r\n'
                if self.area.area_manager == hub:
                    msg += '* '
                msg += f'[{hub.id}] {hub.name} (users: {len([c for c in hub.clients if not c.hidden])}) GM(s): {owner}'
            self.send_ooc(msg)

        def send_done(self):
            """
            Send area information and finish the join handshake.
            This unconditionally causes the client to show the character
            selection screen, even if the client has already joined.
            """
            self.send_command('CharsCheck', *self.get_available_char_list())
            self.send_command('HP', 1, self.area.hp_def)
            self.send_command('HP', 2, self.area.hp_pro)
            if self.area.dark:
                self.send_command('BN', self.area.background_dark, self.area.pos_dark)
            else:
                self.send_command('BN', self.area.background, self.pos)
            self.send_command('LE', *self.area.get_evidence_list(self))
            self.send_command('MM', 1)

            self.area.area_manager.send_arup_players([self])
            self.area.area_manager.send_arup_status([self])
            self.area.area_manager.send_arup_cms([self])
            self.area.area_manager.send_arup_lock([self])

            self.send_command('DONE')

        def char_select(self):
            """Force the client to select a different character."""
            self.char_id = -1
            self.send_done()

        def get_available_char_list(self):
            """Get a list of character IDs that the client can select."""
            if len(self.charcurse) > 0:
                avail_char_ids = set(range(len(
                    self.server.char_list))) and set(self.charcurse)
            else:
                avail_char_ids = set(range(len(self.server.char_list))) - {
                    x.char_id
                    for x in self.area.clients
                }
            char_list = [-1] * len(self.server.char_list)
            for x in avail_char_ids:
                char_list[x] = 0
            return char_list

        def auth_mod(self, password):
            """
            Attempt to log in as a moderator.
            :param password: password string
            :returns: name of profile which the password belongs to, if login
            was successful
            :raises: ClientError if password is incorrect
            """
            modpasses = self.server.config['modpass']
            if isinstance(modpasses, dict):
                matches = [k for k in modpasses
                    if modpasses[k]['password'] == password]
            elif modpasses == password:
                matches = ['default']
            else:
                matches = []

            if self.is_mod:
                raise ClientError('Already logged in.')
            elif len(matches) > 0:
                self.is_mod = True
                self.mod_profile_name = matches[0]
                return self.mod_profile_name
            else:
                raise ClientError('Invalid password.')

        @property
        def ip(self):
            """Get an anonymized version of the IP address."""
            return self.ipid

        @property
        def char_name(self):
            """Get the name of the character that the client is using."""
            if self.char_id == -1:
                return 'Spectator'
            return self.server.char_list[self.char_id]

        @property
        def showname(self):
            """Get the showname of this client, or the char name if none."""
            if self._showname == '':
                return self.char_name
            # No clue why this would ever hapepn but here we go
            if self.char_id > len(self.server.char_list):
                return 'Unknown'
            return self._showname

        @showname.setter
        def showname(self, value):
            self._showname = value

        @property
        def move_delay(self):
            """Get the character's movement delay."""
            return self.area.area_manager.get_character_data(self.char_id, 'move_delay', 0)

        @move_delay.setter
        def move_delay(self, value):
            """Set the character's move delay in the character data."""
            self.area.area_manager.set_character_data(self.char_id, 'move_delay', value)

        @property
        def keys(self):
            """Get the character's keys."""
            return self.area.area_manager.get_character_data(self.char_id, 'keys', [])

        @keys.setter
        def keys(self, value):
            """Set the character's keys in the character data."""
            self.area.area_manager.set_character_data(self.char_id, 'keys', value)

        @property
        def desc(self):
            """Get the character's description."""
            return self.area.area_manager.get_character_data(self.char_id, 'desc', '')

        @desc.setter
        def desc(self, value):
            """Set the character's description character data."""
            self.area.area_manager.set_character_data(self.char_id, 'desc', value)

        @property
        def hidden(self):
            """Return if the character is hidden or not. Always True if char_id is -1 (spectator)"""
            return self.char_id == -1 or self._hidden

        def hide(self, tog=True, target=None, hidden=False):
            msg = 'no longer hidden'
            if tog:
                msg = 'now hidden'
                if target != None:
                    evidence = None
                    for i, evi in enumerate(self.area.evi_list.evidences):
                        if not self.area.evi_list.can_see(evi, self.pos):
                            continue
                        if (target.lower() == evi.name.lower() or target == str(i)):
                            if not self.area.evi_list.can_hide_in(evi):
                                raise ClientError('Targeted evidence cannot be hidden in.')
                            evidence = i
                            break
                    if evidence != None:
                        evi = self.area.evi_list.evidences[evidence]
                        if evi.hiding_client != None:
                            c = evi.hiding_client
                            c.hide(False)
                            c.area.broadcast_area_list(c)
                            raise ClientError(f'{c.showname} was already hiding in that evidence!')
                        self.hidden_in = evidence
                        evi.hiding_client = self
                        msg += f' inside the {evi.name}'
                    else:
                        raise ClientError('Targeted evidence does not exist.')
            else:
                if self.hidden_in != None:
                    evi = self.area.evi_list.evidences[self.hidden_in]
                    evi.hiding_client = None
                    self.hidden_in = None
                    if not hidden:
                        self.area.broadcast_ooc(f'{self.showname} emerges from the {evi.name}!')
                        # Impose all move delays as if we moved an area when unhiding so people have to be smart about it
                        self.last_move_time = round(time.time() * 1000.0)

            self._hidden = tog
            self.send_ooc(f'You are {msg} from /getarea and playercounts.')
            self.area.area_manager.send_arup_players()

        def blind(self, tog=True):
            self.blinded = tog
            msg = 'no longer'
            if tog:
                msg = 'now'
            self.send_ooc(f'You are {msg} blinded from the area and seeing non-broadcasted IC messages.')
            self.send_command('LE', *self.area.get_evidence_list(self))

        def sneak(self, tog=True):
            self.sneaking = tog
            msg = 'no longer'
            if tog:
                msg = 'now'
            self.send_ooc(f'You are {msg} sneaking (area transfer announcements will {msg} be hidden).')

        def follow(self, target):
            try:
                self.change_area(target.area)
                self.following = target
                self.send_ooc(
                    f'You are now following [{target.id}] {target.showname}.')
            except ValueError:
                raise
            except (AreaError, ClientError):
                raise
        
        def unfollow(self, silent=False):
            if self.following != None:
                try:
                    if not silent:
                        self.send_ooc(
                            f'You are no longer following [{self.following.id}] {self.following.showname}.')
                    self.following = None
                except:
                    self.following = None

        def change_position(self, pos=''):
            """
            Change the character's current position in the area.
            :param pos: position in area (Default value = '')
            """
            if len(self.area.pos_lock) > 0 and not (pos in self.area.pos_lock):
                poslist = ', '.join(str(l) for l in self.area.pos_lock)
                raise ClientError(f'Invalid pos! Available pos are {poslist}.')
            if self.hidden_in != None:
                # YOU DARE MOVE?!
                self.hide(False)
                self.area.broadcast_area_list(self)
            self.pos = pos
            self.send_ooc(f'Position set to {pos}.')
            # Send a "Set Position" packet
            self.send_command('SP', self.pos)
            # Send evidence list
            self.send_command('LE', *self.area.get_evidence_list(self))

        def set_mod_call_delay(self):
            """Begin the mod call cooldown."""
            self.mod_call_time = round(time.time() * 1000.0 + 30000)

        def can_call_mod(self):
            """Whether or not the client can currently call mod."""
            return (time.time() * 1000.0 - self.mod_call_time) > 0

        def set_case_call_delay(self):
            """Begin the case announcement cooldown."""
            self.case_call_time = round(time.time() * 1000.0 + 60000)

        def can_call_case(self):
            """Whether or not the client can currently announce a case."""
            return (time.time() * 1000.0 - self.case_call_time) > 0

        def disemvowel_message(self, message):
            """Disemvowel a chat message."""
            message = re.sub('[aeiou]', '', message, flags=re.IGNORECASE)
            return re.sub(r'\s+', ' ', message)

        def shake_message(self, message):
            """Mix the words in a chat message."""
            import random
            parts = message.split()
            random.shuffle(parts)
            return ' '.join(parts)

    def __init__(self, server):
        self.clients = set()
        self.server = server
        self.cur_id = [i for i in range(self.server.config['playerlimit'])]

    def new_client_preauth(self, client):
        maxclients = self.server.config['multiclient_limit']
        for c in self.server.client_manager.clients:
            if c.ipid == client.ipid:
                if c.clientscon > maxclients:
                    return False
        return True

    def new_client(self, transport):
        """
        Create a new client, add it to the list, and assign it a player ID.
        :param transport: asyncio transport
        """
        try:
            user_id = heappop(self.cur_id)
        except IndexError:
            transport.write(b'BD#This server is full.#%')
            raise ClientError

        peername = transport.get_extra_info('peername')[0]
        
        c = self.Client(
            self.server, transport, user_id,
            database.ipid(peername))
        self.clients.add(c)
        temp_ipid = c.ipid
        for client in self.server.client_manager.clients:
            if client.ipid == temp_ipid:
                client.clientscon += 1
        return c

    def remove_client(self, client):
        """
        Remove a disconnected client from the client list.
        :param client: disconnected client
        """
        if client in client.area.area_manager.owners:
            client.area.area_manager.owners.remove(client)
        for hub in self.server.hub_manager.hubs:
            for a in hub.areas:
                if client in a._owners:
                    a.remove_owner(client, dc=True)
                # This discards the client's ID from any of the area invite lists
                # as that ID will no longer refer to this specific player.
                if client.id in a.invite_list:
                    a.invite_list.discard(client.id)
        heappush(self.cur_id, client.id)
        temp_ipid = client.ipid
        for c in self.server.client_manager.clients:
            if c.ipid == temp_ipid:
                c.clientscon -= 1
            if c.following == client:
                c.unfollow()
        self.clients.remove(client)

    def get_targets(self, client, key, value, local=False, single=False):
        """
        Find players by a combination of identifying data.
        Possible keys: player ID, OOC name, character name, HDID, IPID,
        IP address (same as IPID)

        :param client: client
        :param key: the type of identifier that `value` represents
        :param value: data identifying a client
        :param local: search in current area only (Default value = False)
        :param single: search only a single user (Default value = False)
        """
        areas = None
        if local:
            areas = [client.area]
        else:
            areas = client.area.area_manager.areas
        targets = []
        if key == TargetType.ALL:
            for nkey in range(6):
                targets += self.get_targets(client, nkey, value, local)
        for area in areas:
            for client in area.clients:
                if key == TargetType.IP:
                    if value.lower().startswith(client.ip.lower()):
                        targets.append(client)
                elif key == TargetType.OOC_NAME:
                    if value.lower().startswith(
                            client.name.lower()) and client.name:
                        targets.append(client)
                elif key == TargetType.CHAR_NAME:
                    if value.lower().startswith(
                            client.char_name.lower()):
                        targets.append(client)
                elif key == TargetType.ID:
                    if client.id == value:
                        targets.append(client)
                elif key == TargetType.IPID:
                    if client.ipid == value:
                        targets.append(client)
                elif key == TargetType.AFK:
                    if client in area.afkers:
                        targets.append(client)
        return targets

    def get_muted_clients(self):
        """Get a list of muted clients."""
        clients = []
        for client in self.clients:
            if client.is_muted:
                clients.append(client)
        return clients

    def get_ooc_muted_clients(self):
        """Get a list of OOC-muted clients."""
        clients = []
        for client in self.clients:
            if client.is_ooc_muted:
                clients.append(client)
        return clients

    def toggle_afk(self, client):
        if client in client.area.afkers:
            client.area.broadcast_ooc('{} is no longer AFK.'.format(client.showname))
            client.send_ooc('You are no longer AFK. Welcome back!')  # Making the server a bit friendly wouldn't hurt, right?
            client.area.afkers.remove(client)
        else:
            client.area.broadcast_ooc('{} is now AFK.'.format(client.showname))
            client.send_ooc('You are now AFK. Have a good day!')
            client.area.afkers.append(client)

    def refresh_music(self, clients=None):
        """
        Refresh the listed clients' music lists.
        :param clients: list of clients whose music lists should be regenerated.

        """
        if clients == None:
            clients = self.clients
        for client in clients:
            client.refresh_music()

    def get_multiclients(self, ipid=-1, hdid=''):
        return [c for c in self.clients if c.ipid == ipid or c.hdid == hdid]

    def get_mods(self):
        return [c for c in self.clients if c.is_mod]
