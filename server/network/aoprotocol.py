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
import re
import unicodedata

import logging

import re

logger_debug = logging.getLogger('debug')
logger = logging.getLogger('events')

from enum import Enum
from time import localtime, strftime

from server import database
from server.exceptions import ClientError, AreaError, ArgumentError, ServerError
from server.fantacrypt import fanta_decrypt
from .. import commands


class AOProtocol(asyncio.Protocol):
    """The main class that deals with the AO protocol."""

    class ArgType(Enum):
        """Represents the data type of an argument for a network command."""
        STR = 1,
        STR_OR_EMPTY = 2,
        INT = 3,
        INT_OR_STR = 3

    def __init__(self, server):
        super().__init__()
        self.server = server
        self.client = None
        self.buffer = ''
        self.ping_timeout = None

    def dezalgo(self, input):
        """
        Turns any string into a de-zalgo'd version, with a tolerance to allow for special language characters.
        """
        print(self.server.zalgo_tolerance)
        filtered = re.sub('([\u0300\u036f\u1ab0\u1aff\u1dc0\u1dff\u20d0\u20ff\ufe20\ufe2f]' +
                          '{' + re.escape(str(self.server.zalgo_tolerance)) + ',})',
                          '', input)
        return filtered

    def data_received(self, data):
        """Handles any data received from the network.

        Receives data, parses them into a command and passes it
        to the command handler.

        :param data: bytes of data

        """
        buf = data
        ipid = self.client.ipid

        if buf is None:
            buf = b''

        if not isinstance(buf, str):
            # try to decode as utf-8, ignore any erroneous characters
            self.buffer += buf.decode('utf-8', 'ignore')
        else:
            self.buffer = buf

        self.buffer = self.buffer.translate({ord(c): None for c in '\0'})

        if len(self.buffer) > 8192:
            self.client.disconnect()
        for msg in self.get_messages():
            if len(msg) < 2:
                continue
            # general netcode structure is not great
            if msg[0] in ('#', '3', '4'):
                if msg[0] == '#':
                    msg = msg[1:]
                spl = msg.split('#', 1)
                msg = '#'.join([fanta_decrypt(spl[0])] + spl[1:])
            try:
                cmd, *args = msg.split('#')
                self.net_cmd_dispatcher[cmd](self, args)
            except KeyError:
                logger_debug.debug(f'Unknown incoming message from {ipid}: {msg}')

    def connection_made(self, transport):
        """Called upon a new client connecting

        :param transport: the transport object

        """
        self.client = self.server.new_client(transport)
        # Client needs to send CHECK#% within the timeout - otherwise,
        # it will be automatically dropped.
        self.ping_timeout = asyncio.get_event_loop().call_later(
            self.server.config['timeout'], self.client.disconnect)
        asyncio.get_event_loop().call_later(0.25, self.client.send_command,
                                            'decryptor',
                                            34)  # just fantacrypt things)

    def connection_lost(self, exc):
        """User disconnected

        :param exc: reason

        """
        self.server.remove_client(self.client)
        self.ping_timeout.cancel()

    def get_messages(self):
        """Parses out full messages from the buffer.
        
        :return: yields messages

        """
        while '#%' in self.buffer:
            spl = self.buffer.split('#%', 1)
            self.buffer = spl[1]
            yield spl[0]

    def validate_net_cmd(self, args, *types, needs_auth=True):
        """Makes sure the net command's arguments match expectations.

        :param args: actual arguments to the net command
        :param types: what kind of data types are expected
        :param needs_auth: whether you need to have chosen a character (Default value = True)
        :param *types: list of types corresponding to each argument in the command
        :returns: returns True if message was validated

        """
        if needs_auth and self.client.char_id == -1:
            return False
        if len(args) != len(types):
            return False
        for i, arg in enumerate(args):          
            if len(arg) == 0 and types[i] != self.ArgType.STR_OR_EMPTY:
                return False
            if types[i] == self.ArgType.INT:
                try:
                    args[i] = int(arg)
                except ValueError:
                    return False
        return True

    def net_cmd_hi(self, args):
        """Handshake.
        
        HI#<hdid:string>#%

        :param args: a list containing all the arguments

        """
        if not self.validate_net_cmd(args, self.ArgType.STR, needs_auth=False):
            return
        hdid = self.client.hdid = args[0]
        ipid = self.client.ipid

        database.add_hdid(ipid, hdid)
        ban = database.find_ban(ipid, hdid)
        if ban is not None:
            if ban.unban_date is not None:
                unban_date = ban.unban_date.date().isoformat()
            else:
                unban_date = 'N/A'

            msg = f'{ban.reason}\r\n'
            msg += f'ID: {ban.ban_id}\r\n'
            msg += f'Until: {unban_date}'

            database.log_connect(self.client, failed=True)
            self.client.send_command('BD', msg)
            self.client.disconnect()
            return
        else:
            self.client.is_checked = True

        database.log_connect(self.client, failed=False)
        self.client.send_command('ID', self.client.id, self.server.software,
                                 self.server.version)
        self.client.send_command('PN',
                                 self.server.player_count,
                                 self.server.config['playerlimit'])

    def net_cmd_id(self, args):
        """Client version and PV
        
        ID#<pv:int>#<software:string>#<version:string>#%
        """
        self.client.send_command('FL', 'yellowtext', 'customobjections',
                                 'flipping', 'fastloading', 'noencryption',
                                 'deskmod', 'evidence', 'modcall_reason',
                                 'cccc_ic_support', 'arup', 'casing_alerts')

    def net_cmd_ch(self, _):
        """Reset the client drop timeout (keepalive).
        
        CHECK#%
        """
        self.client.send_command('CHECK')
        self.ping_timeout.cancel()
        self.ping_timeout = asyncio.get_event_loop().call_later(
            self.server.config['timeout'], self.client.disconnect)

    def net_cmd_askchaa(self, _):
        """Ask for the counts of characters/evidence/music
        
        askchaa#%
        """
        char_cnt = len(self.server.char_list)
        evi_cnt = 0
        music_cnt = sum([len(x) for x in self.server.music_pages_ao1])
        self.client.send_command('SI', char_cnt, evi_cnt, music_cnt)

    def net_cmd_askchar2(self, _):
        """Asks for the character list. (AO1)
        
        askchar2#%
        """
        self.client.send_command('CI', *self.server.char_pages_ao1[0])

    def net_cmd_an(self, args):
        """Asks for specific pages of the character list.
        (AO1 only; part of askchar2 sequence)
        
        AN#<page:int>#%
        """
        if not self.validate_net_cmd(args, self.ArgType.INT, needs_auth=False):
            return
        if len(self.server.char_pages_ao1) > args[0] >= 0:
            self.client.send_command('CI',
                                     *self.server.char_pages_ao1[args[0]])
        else:
            self.client.send_command('EM', *self.server.music_pages_ao1[0])

    def net_cmd_ae(self, _):
        """Asks for specific pages of the evidence list.
        (AO1 only; part of askchar2 sequence)
        
        AE#<page:int>#%

        """
        pass  # todo evidence maybe later

    def net_cmd_am(self, args):
        """Asks for specific pages of the music list.
        (AO1 only; part of askchar2 sequence)
        
        AM#<page:int>#%

        """
        if not self.validate_net_cmd(args, self.ArgType.INT, needs_auth=False):
            return
        if len(self.server.music_pages_ao1) > args[0] >= 0:
            self.client.send_command('EM',
                                     *self.server.music_pages_ao1[args[0]])
        else:
            self.client.send_done()
            self.client.send_area_list()
            self.client.send_motd()

    def net_cmd_rc(self, _):
        """Asks for the whole character list (AO2)
        
        AC#%

        """

        self.client.send_command('SC', *self.server.char_list)

    def net_cmd_rm(self, _):
        """Asks for the whole music list (AO2)
        
        AM#%

        """

        self.client.send_command('SM', *self.server.music_list_ao2)

    def net_cmd_rd(self, _):
        """Asks for server metadata(charscheck, motd etc.) and a DONE#% signal(also best packet)
        
        RD#%

        """

        self.client.send_done()
        self.client.send_area_list()
        self.client.send_motd()

    def net_cmd_cc(self, args):
        """Character selection.
        
        CC#<client_id:int>#<char_id:int>#<hdid:string>#%

        """
        if not self.validate_net_cmd(args,
                                     self.ArgType.INT,
                                     self.ArgType.INT,
                                     self.ArgType.STR,
                                     needs_auth=False):
            return
        elif not self.client.is_checked:
            return

        cid = args[1]
        try:
            self.client.change_character(cid)
        except ClientError:
            return

    def net_cmd_ms(self, args):
        """IC message.
        
        Refer to the implementation for details.

        """
        if not self.client.is_checked:
            return
        elif self.client.is_muted:  # Checks to see if the client has been muted by a mod
            self.client.send_ooc('You are muted by a moderator.')
            return
        elif not self.client.area.can_send_message(self.client):
            return

        target_area = []
        if self.validate_net_cmd(args, self.ArgType.STR, # msg_type
                                 self.ArgType.STR_OR_EMPTY, self.ArgType.STR,#pre, folder
                                 self.ArgType.STR, self.ArgType.STR,# anim, text
                                 self.ArgType.STR, self.ArgType.STR,#pos, sfx
                                 self.ArgType.INT, self.ArgType.INT,#anim_type, cid
                                 self.ArgType.INT, self.ArgType.INT_OR_STR,#sfx_delay, button
                                 self.ArgType.INT, self.ArgType.INT,#evidence, flip
                                 self.ArgType.INT, self.ArgType.INT):#ding, color
            # Pre-2.6 validation monstrosity.
            msg_type, pre, folder, anim, text, pos, sfx, anim_type, cid, sfx_delay, button, evidence, flip, ding, color = args
            showname = ""
            charid_pair = -1
            offset_pair = 0
            nonint_pre = 0
        elif self.validate_net_cmd(
                args, self.ArgType.STR, self.ArgType.STR_OR_EMPTY,#msg_type, pre
                self.ArgType.STR, self.ArgType.STR, self.ArgType.STR,#folder, anim, text
                self.ArgType.STR, self.ArgType.STR, self.ArgType.INT,# pos, sfx, anim_type
                self.ArgType.INT, self.ArgType.INT, self.ArgType.INT_OR_STR,#cid, sfx_delay, button
                self.ArgType.INT, self.ArgType.INT, self.ArgType.INT,#evidence, flip, ding
                self.ArgType.INT, self.ArgType.STR_OR_EMPTY, self.ArgType.INT, #color, showname, charid_pair
                self.ArgType.INT, self.ArgType.INT): #offset_pair, nonint_pre
            # 2.6+ validation monstrosity.
            msg_type, pre, folder, anim, text, pos, sfx, anim_type, cid, sfx_delay, button, evidence, flip, ding, color, showname, charid_pair, offset_pair, nonint_pre = args
            if len(showname
                   ) > 0 and not self.client.area.showname_changes_allowed:
                self.client.send_ooc(
                    "Showname changes are forbidden in this area!")
                return
        else:
            return
        if self.client.area.is_iniswap(self.client, pre, anim,
                folder, sfx):
            self.client.send_ooc("Iniswap/custom emotes are blocked in this area")
            return
        if len(self.client.charcurse) > 0 and \
            folder != self.client.char_name:
            self.client.send_ooc(
                "You may not iniswap while you are charcursed!")
            return
        if not self.client.area.blankposting_allowed:
            if text == ' ':
                self.client.send_ooc(
                    "Blankposting is forbidden in this area!")
                return
            if text.isspace():
                self.client.send_ooc(
                    "Blankposting is forbidden in this area, and putting more spaces in does not make it not blankposting."
                )
                return
            if len(re.sub(r'[{}\\`|(~~)]', '', text).replace(
                    ' ', '')) < 3 and text != '<' and text != '>':
                self.client.send_ooc(
                    "While that is not a blankpost, it is still pretty spammy. Try forming sentences."
                )
                return
        if text.startswith('/a '):
            part = text.split(' ')
            try:
                aid = int(part[1])
                area = self.server.area_manager.get_area_by_id(aid)
                if self.client in area.owners:
                    target_area.append(aid)
                if not target_area:
                    self.client.send_ooc(f'You don\'t own {area.name}!')
                    return
                text = ' '.join(part[2:])
            except ValueError:
                self.client.send_ooc(
                    "That does not look like a valid area ID!")
                return
        elif text.startswith('/s '):
            part = text.split(' ')
            for a in self.server.area_manager.areas:
                if self.client in a.owners:
                    target_area.append(a.id)
            if not target_area:
                self.client.send_ooc('You don\'t any areas!')
                return
            text = ' '.join(part[1:])
        if msg_type not in ('chat', '0', '1'):
            return
        if anim_type not in (0, 1, 2, 5, 6):
            return
        if cid != self.client.char_id:
            return
        if sfx_delay < 0:
            return
        if '4' in button and "<and>" not in button:
            print(button)
            return
        if evidence < 0:
            return
        if ding not in (0, 1):
            return
        if color not in (0, 1, 2, 3, 4, 5, 6, 7, 8):
            return
        if len(showname) > 15:
            self.client.send_ooc("Your IC showname is way too long!")
            return
        if nonint_pre == 1:
            if button in (1, 2, 3, 4, 23):
                if anim_type == 1 or anim_type == 2:
                    anim_type = 0
                elif anim_type == 6:
                    anim_type = 5
        if self.client.area.non_int_pres_only:
            if anim_type == 1 or anim_type == 2:
                anim_type = 0
                nonint_pre = 1
            elif anim_type == 6:
                anim_type = 5
                nonint_pre = 1
        if not self.client.area.shouts_allowed:
            # Old clients communicate the objecting in anim_type.
            if anim_type == 2:
                anim_type = 1
            elif anim_type == 6:
                anim_type = 5
            # New clients do it in a specific objection message area.
            button = 0
            # Turn off the ding.
            ding = 0
        if color == 2 and not (self.client.is_mod
                               or self.client in self.client.area.owners):
            color = 0
        if color == 6:
            text = re.sub(r'[^\x00-\x7F]+', ' ',
                          text)  # remove all unicode to prevent redtext abuse
            if len(text.strip(' ')) == 1:
                color = 0
            else:
                if text.strip(' ') in ('<num>', '<percent>', '<dollar>',
                                       '<and>'):
                    color = 0
        if self.client.pos:
            pos = self.client.pos
        else:
            if pos not in ('def', 'pro', 'hld', 'hlp', 'jud', 'wit', 'jur',
                           'sea'):
                return
        msg = self.dezalgo(text)[:256]
        if self.client.shaken:
            msg = self.client.shake_message(msg)
        if self.client.disemvowel:
            msg = self.client.disemvowel_message(msg)
        self.client.pos = pos
        if evidence:
            if self.client.area.evi_list.evidences[
                    self.client.evi_list[evidence] - 1].pos != 'all':
                self.client.area.evi_list.evidences[
                    self.client.evi_list[evidence] - 1].pos = 'all'
                self.client.area.broadcast_evidence_list()

        # Here, we check the pair stuff, and save info about it to the client.
        # Notably, while we only get a charid_pair and an offset, we send back a chair_pair, an emote, a talker offset
        # and an other offset.
        self.client.charid_pair = charid_pair
        self.client.offset_pair = offset_pair
        if anim_type not in (5, 6):
            self.client.last_sprite = anim
        self.client.flip = flip
        self.client.claimed_folder = folder
        other_offset = 0
        other_emote = ''
        other_flip = 0
        other_folder = ''

        confirmed = False
        if charid_pair > -1:
            for target in self.client.area.clients:
                if target.char_id == self.client.charid_pair and target.charid_pair == self.client.char_id and target != self.client and target.pos == self.client.pos:
                    confirmed = True
                    other_offset = target.offset_pair
                    other_emote = target.last_sprite
                    other_flip = target.flip
                    other_folder = target.claimed_folder
                    break

        if not confirmed:
            charid_pair = -1
            offset_pair = 0

        self.client.area.send_command('MS', msg_type, pre, folder, anim, msg,
                                      pos, sfx, anim_type, cid, sfx_delay,
                                      button, self.client.evi_list[evidence],
                                      flip, ding, color, showname, charid_pair,
                                      other_folder, other_emote, offset_pair,
                                      other_offset, other_flip, nonint_pre)

        self.client.area.send_owner_command(
            'MS', msg_type, pre, folder, anim,
            '[' + self.client.area.abbreviation + ']' + msg, pos, sfx,
            anim_type, cid, sfx_delay, button, self.client.evi_list[evidence],
            flip, ding, color, showname, charid_pair, other_folder,
            other_emote, offset_pair, other_offset, other_flip, nonint_pre)

        self.server.area_manager.send_remote_command(
            target_area, 'MS', msg_type, pre, folder, anim, msg, pos, sfx,
            anim_type, cid, sfx_delay, button, self.client.evi_list[evidence],
            flip, ding, color, showname, charid_pair, other_folder,
            other_emote, offset_pair, other_offset, other_flip, nonint_pre)

        self.client.area.set_next_msg_delay(len(msg))
        database.log_ic(self.client, self.client.area, showname, msg)

        if (self.client.area.is_recording):
            self.client.area.recorded_messages.append(args)

    def net_cmd_ct(self, args):
        """OOC Message
        
        CT#<name:string>#<message:string>#%

        """
        if not self.client.is_checked:
            return
        if self.client.is_ooc_muted:  # Checks to see if the client has been muted by a mod
            self.client.send_ooc('You are muted by a moderator.')
            return
        if not self.validate_net_cmd(args, self.ArgType.STR, self.ArgType.STR):
            return
        if self.client.name != args[0] and self.client.fake_name != args[0]:
            if self.client.is_valid_name(args[0]):
                self.client.name = args[0]
                self.client.fake_name = args[0]
            else:
                self.client.fake_name = args[0]
        if self.client.name == '':
            self.client.send_ooc(
                'You must insert a name with at least one letter')
            return
        if len(self.client.name) > 30:
            self.client.send_ooc(
                'Your OOC name is too long! Limit it to 30 characters.')
            return
        for c in self.client.name:
            if unicodedata.category(c) == 'Cf':
                self.client.send_ooc(
                    'You cannot use format characters in your name!')
                return
        if self.client.name.startswith(
                self.server.config['hostname']) or self.client.name.startswith(
                    '<dollar>G') or self.client.name.startswith('<dollar>M'):
            self.client.send_ooc('That name is reserved!')
            return
        if args[1].startswith(' /'):
            self.client.send_ooc(
                'Your message was not sent for safety reasons: you left a space before that slash.'
            )
            return
        if args[1].startswith('/'):
            spl = args[1][1:].split(' ', 1)
            cmd = spl[0].lower()
            arg = ''
            if len(spl) == 2:
                arg = spl[1][:256]
            try:
                called_function = f'ooc_cmd_{cmd}'
                if cmd == 'help' and arg != '':
                    self.client.send_ooc(commands.help(f'ooc_cmd_{arg}'))
                else:
                    getattr(commands, called_function)(self.client, arg)
            except AttributeError:
                print('Attribute error with ' + called_function)
                self.client.send_ooc('Invalid command.')
            except (ClientError, AreaError, ArgumentError, ServerError) as ex:
                self.client.send_ooc(ex)
            except Exception as ex:
                self.client.send_ooc('An internal error occurred. Please check the server log.')
                logger.exception('Exception while running a command')
        else:
            args[1] = self.dezalgo(args[1])
            if self.client.shaken:
                args[1] = self.client.shake_message(args[1])
            if self.client.disemvowel:
                args[1] = self.client.disemvowel_message(args[1])
            self.client.area.send_command('CT', self.client.name, args[1])
            self.client.area.send_owner_command(
                'CT',
                '[' + self.client.area.abbreviation + ']' + self.client.name,
                args[1])
            database.log_room('ooc', self.client, self.client.area, message=args[1])

    def net_cmd_mc(self, args):
        """Play music.
        
        MC#<song_name:int>#<???:int>#%

        """
        if not self.client.is_checked:
            return
        try:
            area = self.server.area_manager.get_area_by_name(args[0])
            self.client.change_area(area)
        except AreaError:
            if self.client.is_muted:  # Checks to see if the client has been muted by a mod
                self.client.send_ooc(
                    'You are muted by a moderator.')
                return
            if not self.client.is_dj:
                self.client.send_ooc(
                    'You were blockdj\'d by a moderator.')
                return
            if self.client.area.cannot_ic_interact(self.client):
                self.client.send_ooc(
                    "You are not on the area's invite list, and thus, you cannot change music!"
                )
                return
            if not self.validate_net_cmd(
                    args, self.ArgType.STR,
                    self.ArgType.INT) and not self.validate_net_cmd(
                        args, self.ArgType.STR, self.ArgType.INT,
                        self.ArgType.STR):
                return
            if args[1] != self.client.char_id:
                return
            if self.client.change_music_cd():
                self.client.send_ooc(
                    'You changed song too many times. Please try again after {} seconds.'
                    .format(int(self.client.change_music_cd())))
                return
            try:
                name, length = self.server.get_song_data(args[0])

                if self.client.area.jukebox:
                    showname = ''
                    if len(args) > 2:
                        showname = args[2]
                        if len(
                                showname
                        ) > 0 and not self.client.area.showname_changes_allowed:
                            self.client.send_ooc(
                                "Showname changes are forbidden in this area!")
                            return
                    self.client.area.add_jukebox_vote(self.client, name,
                                                      length, showname)
                    database.log_room('jukebox.vote', self.client, self.client.area, message=name)
                else:
                    if len(args) > 2:
                        showname = args[2]
                        if len(
                                showname
                        ) > 0 and not self.client.area.showname_changes_allowed:
                            self.client.send_ooc(
                                "Showname changes are forbidden in this area!")
                            return
                        self.client.area.play_music_shownamed(
                            name, self.client.char_id, showname, length)
                        self.client.area.add_music_playing_shownamed(
                            self.client, showname, name)
                    else:
                        self.client.area.play_music(name, self.client.char_id,
                                                    length)
                        self.client.area.add_music_playing(self.client, name)
                    database.log_room('music', self.client, self.client.area, message=name)
            except ServerError:
                return
        except ClientError as ex:
            self.client.send_ooc(ex)

    def net_cmd_rt(self, args):
        """Plays the Testimony/CE animation.
        
        RT#<type:string>#%

        """
        if not self.client.is_checked:
            return
        if not self.client.area.shouts_allowed:
            self.client.send_ooc(
                "You cannot use the testimony buttons here!")
            return
        if self.client.is_muted:  # Checks to see if the client has been muted by a mod
            self.client.send_ooc('You are muted by a moderator.')
            return
        if not self.client.can_wtce:
            self.client.send_ooc(
                'You were blocked from using judge signs by a moderator.')
            return
        if self.client.area.cannot_ic_interact(self.client):
            self.client.send_ooc(
                "You are not on the area's invite list, and thus, you cannot use the WTCE buttons!"
            )
            return
        if not self.validate_net_cmd(
                args, self.ArgType.STR) and not self.validate_net_cmd(
                    args, self.ArgType.STR, self.ArgType.INT):
            return
        if args[0] == 'testimony1':
            sign = 'WT'
        elif args[0] == 'testimony2':
            sign = 'CE'
        elif args[0] == 'judgeruling':
            sign = 'JR'
        else:
            return
        if self.client.wtce_mute():
            self.client.send_ooc(
                'You used witness testimony/cross examination signs too many times. Please try again after {} seconds.'
                .format(int(self.client.wtce_mute())))
            return
        if len(args) == 1:
            self.client.area.send_command('RT', args[0])
        elif len(args) == 2:
            self.client.area.send_command('RT', args[0], args[1])
        self.client.area.add_to_judgelog(self.client, f'used {sign}')
        database.log_room('wtce', self.client, self.client.area, message=sign)

    def net_cmd_setcase(self, args):
        """Sets the casing preferences of the given client.
        
        SETCASE#<cases:string>#<will_cm:int>#<will_def:int>#<will_pro:int>#<will_judge:int>#<will_jury:int>#<will_steno:int>#%
        
        Note: Though all but the first arguments are ints, they technically behave as bools of 0 and 1 value.

        """
        self.client.casing_cases = args[0]
        self.client.casing_cm = args[1] == "1"
        self.client.casing_def = args[2] == "1"
        self.client.casing_pro = args[3] == "1"
        self.client.casing_jud = args[4] == "1"
        self.client.casing_jur = args[5] == "1"
        self.client.casing_steno = args[6] == "1"

    def net_cmd_casea(self, args):
        """Announces a case with a title, and specific set of people to look for.
        
        CASEA#<casetitle:string>#<need_cm:int>#<need_def:int>#<need_pro:int>#<need_judge:int>#<need_jury:int>#<need_steno:int>#%
        
        Note: Though all but the first arguments are ints, they technically behave as bools of 0 and 1 value.

        """
        if not self.client.is_checked:
            return
        if self.client in self.client.area.owners:
            if not self.client.can_call_case():
                self.client.send_ooc(
                    'Please wait 60 seconds between case announcements!')
                return

            if not args[1] == "1" and not args[2] == "1" and not args[
                    3] == "1" and not args[4] == "1" and not args[5] == "1":
                self.client.send_ooc(
                    'You should probably announce the case to at least one person.'
                )
                return
            msg = '=== Case Announcement ===\r\n{} [{}] is hosting {}, looking for '.format(
                self.client.char_name, self.client.id, args[0])

            lookingfor = [p for p, q in \
                zip(['defense', 'prosecutor', 'judge', 'juror', 'stenographer'], args[1:])
                if q == '1']

            msg += ', '.join(lookingfor) + '.\r\n=================='

            self.client.server.send_all_cmd_pred('CASEA', msg, args[1],
                                                 args[2], args[3], args[4],
                                                 args[5], '1')

            self.client.set_case_call_delay()

            log_data = {k: v for k, v in \
                zip(('message', 'def', 'pro', 'jud', 'jur', 'steno'), args)}
            database.log_room('case', self.client, self.client.area, message=log_data)
        else:
            self.client.send_ooc(
                'You cannot announce a case in an area where you are not a CM!'
            )

    def net_cmd_hp(self, args):
        """Sets the penalty bar.
        
        HP#<type:int>#<new_value:int>#%

        """
        if not self.client.is_checked:
            return
        if self.client.is_muted:  # Checks to see if the client has been muted by a mod
            self.client.send_ooc('You are muted by a moderator.')
            return
        if self.client.area.cannot_ic_interact(self.client):
            self.client.send_ooc(
                "You are not on the area's invite list, and thus, you cannot change the Confidence bars!"
            )
            return
        if not self.validate_net_cmd(args, self.ArgType.INT, self.ArgType.INT):
            return
        try:
            self.client.area.change_hp(args[0], args[1])
            self.client.area.add_to_judgelog(self.client,
                                             'changed the penalties')
            database.log_room('hp', self.client, self.client.area)
        except AreaError:
            return

    def net_cmd_pe(self, args):
        """Adds a piece of evidence.
        
        PE#<name: string>#<description: string>#<image: string>#%

        :param args: 

        """
        if not self.client.is_checked:
            return
        elif len(args) < 3:
            return
        # evi = Evidence(args[0], args[1], args[2], self.client.pos)
        self.client.area.evi_list.add_evidence(self.client, args[0], args[1],
                                               args[2], 'all')
        database.log_room('evidence.add', self.client, self.client.area)
        self.client.area.broadcast_evidence_list()

    def net_cmd_de(self, args):
        """Deletes a piece of evidence.
        
        DE#<id: int>#%

        """
        if not self.client.is_checked:
            return
        self.client.area.evi_list.del_evidence(
            self.client, self.client.evi_list[int(args[0])])
        database.log_room('evidence.del', self.client, self.client.area)
        self.client.area.broadcast_evidence_list()

    def net_cmd_ee(self, args):
        """Edits a piece of evidence.
        
        EE#<id: int>#<name: string>#<description: string>#<image: string>#%

        """
        if not self.client.is_checked:
            return
        elif len(args) < 4:
            return

        evi = (args[1], args[2], args[3], 'all')

        self.client.area.evi_list.edit_evidence(
            self.client, self.client.evi_list[int(args[0])], evi)
        database.log_room('evidence.edit', self.client, self.client.area)
        self.client.area.broadcast_evidence_list()

    def net_cmd_zz(self, args):
        """Sent on mod call.

        """
        if not self.client.is_checked:
            return

        if self.client.is_muted:  # Checks to see if the client has been muted by a mod
            self.client.send_ooc('You are muted by a moderator.')
            return

        if self.client.char_id is -1:
            self.client.send_ooc(
                "You cannot call a moderator while spectating.")
            return

        if not self.client.can_call_mod():
            self.client.send_ooc(
                "You must wait 30 seconds between mod calls.")
            return

        current_time = strftime("%H:%M", localtime())

        if len(args) < 1:
            self.server.send_all_cmd_pred(
                'ZZ',
                '[{}] {} ({}) in {} without reason (not using 2.6?)'.format(
                    current_time, self.client.char_name,
                    self.client.ip, self.client.area.name),
                pred=lambda c: c.is_mod)
            self.client.set_mod_call_delay()
            database.log_room('modcall', self.client, self.client.area)
        else:
            self.server.send_all_cmd_pred(
                'ZZ',
                '[{}] {} ({}) in {} with reason: {}'.format(
                    current_time, self.client.char_name,
                    self.client.ip, self.client.area.name,
                    args[0][:100]),
                pred=lambda c: c.is_mod)
            self.client.set_mod_call_delay()
            database.log_room('modcall', self.client, self.client.area, message=args[0])

    def net_cmd_opKICK(self, args):
        """
        Unused; kick a user from the client UI.

        """
        self.net_cmd_ct(['opkick', '/kick {}'.format(args[0])])

    def net_cmd_opBAN(self, args):
        """
        Unused; ban a user from the client UI.

        """
        self.net_cmd_ct(['opban', '/ban {}'.format(args[0])])

    net_cmd_dispatcher = {
        'HI': net_cmd_hi,  # handshake
        'ID': net_cmd_id,  # client version
        'CH': net_cmd_ch,  # keepalive
        'askchaa': net_cmd_askchaa,  # ask for list lengths
        'askchar2': net_cmd_askchar2,  # ask for list of characters
        'AN': net_cmd_an,  # character list
        'AE': net_cmd_ae,  # evidence list
        'AM': net_cmd_am,  # music list
        'RC': net_cmd_rc,  # AO2 character list
        'RM': net_cmd_rm,  # AO2 music list
        'RD': net_cmd_rd,  # AO2 done request, charscheck etc.
        'CC': net_cmd_cc,  # select character
        'MS': net_cmd_ms,  # IC message
        'CT': net_cmd_ct,  # OOC message
        'MC': net_cmd_mc,  # play song
        'RT': net_cmd_rt,  # WT/CE buttons
        'SETCASE':
        net_cmd_setcase,  # set case-announcement preferences for user
        'CASEA': net_cmd_casea,  # announce a case
        'HP': net_cmd_hp,  # penalties
        'PE': net_cmd_pe,  # add evidence
        'DE': net_cmd_de,  # delete evidence
        'EE': net_cmd_ee,  # edit evidence
        'ZZ': net_cmd_zz,  # call mod button
        'opKICK': net_cmd_opKICK,  # /kick with guard on
        'opBAN': net_cmd_opBAN,  # /ban with guard on
    }
