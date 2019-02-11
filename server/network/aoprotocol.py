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
from enum import Enum
from time import gmtime, localtime, strftime

from server import commands
from server import logger
from server.exceptions import ClientError, AreaError, ArgumentError, ServerError
from server.fantacrypt import fanta_decrypt


class AOProtocol(asyncio.Protocol):
    """
    The main class that deals with the AO protocol.
    """

    class ArgType(Enum):
        STR = 1,
        STR_OR_EMPTY = 2,
        INT = 3

    def __init__(self, server):
        super().__init__()
        self.server = server
        self.client = None
        self.buffer = ''
        self.ping_timeout = None

    def data_received(self, data):
        """ Handles any data received from the network.

        Receives data, parses them into a command and passes it
        to the command handler.

        :param data: bytes of data
        """
        buf = data

        if not self.client.is_checked and self.server.ban_manager.is_banned(self.client.ipid):
            self.client.transport.close()
        else:
            self.client.is_checked = True

        if buf is None:
            buf = b''

        if not isinstance(buf, str):
            # try to decode as utf-8, ignore any erroneous characters
            self.buffer += buf.decode('utf-8', 'ignore')
        else:
            self.buffer = buf

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
                logger.log_debug('[INC][RAW]{}'.format(msg), self.client)
            try:
                cmd, *args = msg.split('#')
                self.net_cmd_dispatcher[cmd](self, args)
            except KeyError:
                logger.log_debug('[INC][UNK]{}'.format(msg), self.client)

    def connection_made(self, transport):
        """ Called upon a new client connecting

        :param transport: the transport object
        """
        self.client = self.server.new_client(transport)
        self.ping_timeout = asyncio.get_event_loop().call_later(self.server.config['timeout'], self.client.disconnect)
        asyncio.get_event_loop().call_later(0.25, self.client.send_command, 'decryptor', 34)  # just fantacrypt things)

    def connection_lost(self, exc):
        """ User disconnected

        :param exc: reason
        """
        self.server.remove_client(self.client)
        self.ping_timeout.cancel()

    def get_messages(self):
        """ Parses out full messages from the buffer.

        :return: yields messages
        """
        while '#%' in self.buffer:
            spl = self.buffer.split('#%', 1)
            self.buffer = spl[1]
            yield spl[0]
        # exception because bad netcode
        askchar2 = '#615810BC07D12A5A#'
        if self.buffer == askchar2:
            self.buffer = ''
            yield askchar2

    def validate_net_cmd(self, args, *types, needs_auth=True):
        """ Makes sure the net command's arguments match expectations.

        :param args: actual arguments to the net command
        :param types: what kind of data types are expected
        :param needs_auth: whether you need to have chosen a character
        :return: returns True if message was validated
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
        """ Handshake.

        HI#<hdid:string>#%

        :param args: a list containing all the arguments
        """
        if not self.validate_net_cmd(args, self.ArgType.STR, needs_auth=False):
            return
        self.client.hdid = args[0]
        if self.client.hdid not in self.client.server.hdid_list:
            self.client.server.hdid_list[self.client.hdid] = []
        if self.client.ipid not in self.client.server.hdid_list[self.client.hdid]:
            self.client.server.hdid_list[self.client.hdid].append(self.client.ipid)
            self.client.server.dump_hdids()
        for ipid in self.client.server.hdid_list[self.client.hdid]:
            if self.server.ban_manager.is_banned(ipid):
                self.client.send_command('BD')
                self.client.disconnect()
                return
        logger.log_server('Connected. HDID: {}.'.format(self.client.hdid), self.client)
        self.client.send_command('ID', self.client.id, self.server.software, self.server.get_version_string())
        self.client.send_command('PN', self.server.get_player_count() - 1, self.server.config['playerlimit'])

    def net_cmd_id(self, args):
        """ Client version and PV

        ID#<pv:int>#<software:string>#<version:string>#%

        """

        self.client.is_ao2 = False

        if len(args) < 2:
            return

        version_list = args[1].split('.')

        if len(version_list) < 3:
            return

        release = int(version_list[0])
        major = int(version_list[1])
        minor = int(version_list[2])

        if args[0] != 'AO2':
            return
        if release < 2:
            return
        elif release == 2:
            if major < 2:
                return
            elif major == 2:
                if minor < 5:
                    return

        self.client.is_ao2 = True

        self.client.send_command('FL', 'yellowtext', 'customobjections', 'flipping', 'fastloading', 'noencryption',
                                 'deskmod', 'evidence', 'modcall_reason', 'cccc_ic_support', 'arup', 'casing_alerts')

    def net_cmd_ch(self, _):
        """ Periodically checks the connection.

        CHECK#%

        """
        self.client.send_command('CHECK')
        self.ping_timeout.cancel()
        self.ping_timeout = asyncio.get_event_loop().call_later(self.server.config['timeout'], self.client.disconnect)

    def net_cmd_askchaa(self, _):
        """ Ask for the counts of characters/evidence/music

        askchaa#%

        """
        char_cnt = len(self.server.char_list)
        evi_cnt = 0
        music_cnt = sum([len(x) for x in self.server.music_pages_ao1])
        self.client.send_command('SI', char_cnt, evi_cnt, music_cnt)

    def net_cmd_askchar2(self, _):
        """ Asks for the character list.

        askchar2#%

        """
        self.client.send_command('CI', *self.server.char_pages_ao1[0])

    def net_cmd_an(self, args):
        """ Asks for specific pages of the character list.

        AN#<page:int>#%

        """
        if not self.validate_net_cmd(args, self.ArgType.INT, needs_auth=False):
            return
        if len(self.server.char_pages_ao1) > args[0] >= 0:
            self.client.send_command('CI', *self.server.char_pages_ao1[args[0]])
        else:
            self.client.send_command('EM', *self.server.music_pages_ao1[0])

    def net_cmd_ae(self, _):
        """ Asks for specific pages of the evidence list.

        AE#<page:int>#%

        """
        pass  # todo evidence maybe later

    def net_cmd_am(self, args):
        """ Asks for specific pages of the music list.

        AM#<page:int>#%

        """
        if not self.validate_net_cmd(args, self.ArgType.INT, needs_auth=False):
            return
        if len(self.server.music_pages_ao1) > args[0] >= 0:
            self.client.send_command('EM', *self.server.music_pages_ao1[args[0]])
        else:
            self.client.send_done()
            self.client.send_area_list()
            self.client.send_motd()

    def net_cmd_rc(self, _):
        """ Asks for the whole character list(AO2)

        AC#%

        """

        self.client.send_command('SC', *self.server.char_list)

    def net_cmd_rm(self, _):
        """ Asks for the whole music list(AO2)

        AM#%

        """

        self.client.send_command('SM', *self.server.music_list_ao2)

    def net_cmd_rd(self, _):
        """ Asks for server metadata(charscheck, motd etc.) and a DONE#% signal(also best packet)

        RD#%

        """

        self.client.send_done()
        self.client.send_area_list()
        self.client.send_motd()

    def net_cmd_cc(self, args):
        """ Character selection.

        CC#<client_id:int>#<char_id:int>#<hdid:string>#%

        """
        if not self.validate_net_cmd(args, self.ArgType.INT, self.ArgType.INT, self.ArgType.STR, needs_auth=False):
            return
        cid = args[1]
        try:
            self.client.change_character(cid)
        except ClientError:
            return

    def net_cmd_ms(self, args):
        """ IC message.

        Refer to the implementation for details.

        """
        if self.client.is_muted:  # Checks to see if the client has been muted by a mod
            self.client.send_host_message("You have been muted by a moderator")
            return
        if not self.client.area.can_send_message(self.client):
            return

        target_area = []

        if self.validate_net_cmd(args, self.ArgType.STR, self.ArgType.STR_OR_EMPTY, self.ArgType.STR,
                                 self.ArgType.STR,
                                 self.ArgType.STR, self.ArgType.STR, self.ArgType.STR, self.ArgType.INT,
                                 self.ArgType.INT, self.ArgType.INT, self.ArgType.INT, self.ArgType.INT,
                                 self.ArgType.INT, self.ArgType.INT, self.ArgType.INT):
            # Vanilla validation monstrosity.
            msg_type, pre, folder, anim, text, pos, sfx, anim_type, cid, sfx_delay, button, evidence, flip, ding, color = args
            showname = ""
            charid_pair = -1
            offset_pair = 0
            nonint_pre = 0
        elif self.validate_net_cmd(args, self.ArgType.STR, self.ArgType.STR_OR_EMPTY, self.ArgType.STR,
                                   self.ArgType.STR,
                                   self.ArgType.STR, self.ArgType.STR, self.ArgType.STR, self.ArgType.INT,
                                   self.ArgType.INT, self.ArgType.INT, self.ArgType.INT, self.ArgType.INT,
                                   self.ArgType.INT, self.ArgType.INT, self.ArgType.INT, self.ArgType.STR_OR_EMPTY):
            # 1.3.0 validation monstrosity.
            msg_type, pre, folder, anim, text, pos, sfx, anim_type, cid, sfx_delay, button, evidence, flip, ding, color, showname = args
            charid_pair = -1
            offset_pair = 0
            nonint_pre = 0
            if len(showname) > 0 and not self.client.hub.showname_changes_allowed:
                self.client.send_host_message("Showname changes are forbidden in this hub!")
                return
        elif self.validate_net_cmd(args, self.ArgType.STR, self.ArgType.STR_OR_EMPTY, self.ArgType.STR,
                                   self.ArgType.STR,
                                   self.ArgType.STR, self.ArgType.STR, self.ArgType.STR, self.ArgType.INT,
                                   self.ArgType.INT, self.ArgType.INT, self.ArgType.INT, self.ArgType.INT,
                                   self.ArgType.INT, self.ArgType.INT, self.ArgType.INT, self.ArgType.STR_OR_EMPTY,
                                   self.ArgType.INT, self.ArgType.INT):
            # 1.3.5 validation monstrosity.
            msg_type, pre, folder, anim, text, pos, sfx, anim_type, cid, sfx_delay, button, evidence, flip, ding, color, showname, charid_pair, offset_pair = args
            nonint_pre = 0
            if len(showname) > 0 and not self.client.hub.showname_changes_allowed:
                self.client.send_host_message("Showname changes are forbidden in this hub!")
                return
        elif self.validate_net_cmd(args, self.ArgType.STR, self.ArgType.STR_OR_EMPTY, self.ArgType.STR,
                                   self.ArgType.STR,
                                   self.ArgType.STR, self.ArgType.STR, self.ArgType.STR, self.ArgType.INT,
                                   self.ArgType.INT, self.ArgType.INT, self.ArgType.INT, self.ArgType.INT,
                                   self.ArgType.INT, self.ArgType.INT, self.ArgType.INT, self.ArgType.STR_OR_EMPTY,
                                   self.ArgType.INT, self.ArgType.INT, self.ArgType.INT):
            # 1.4.0 validation monstrosity.
            msg_type, pre, folder, anim, text, pos, sfx, anim_type, cid, sfx_delay, button, evidence, flip, ding, color, showname, charid_pair, offset_pair, nonint_pre = args
            if len(showname) > 0 and not self.client.hub.showname_changes_allowed:
                self.client.send_host_message("Showname changes are forbidden in this hub!")
                return
        else:
            return
        if self.client.hub.is_iniswap(self.client, pre, anim, folder) and folder != self.client.get_char_name():
            self.client.send_host_message("Iniswap is blocked in this area")
            return
        if len(self.client.charcurse) > 0 and folder != self.client.get_char_name():
            self.client.send_host_message("You may not iniswap while you are charcursed!")
            return
        if not self.client.hub.blankposting_allowed:
            if text == ' ':
                self.client.send_host_message("Blankposting is forbidden in this hub!")
                return
            if text.isspace():
                self.client.send_host_message(
                    "Blankposting is forbidden in this hub, and putting more spaces in does not make it not blankposting.")
                return
            if len(re.sub(r'[{}\\`|(~~)]', '', text).replace(' ', '')) < 3 and text != '<' and text != '>':
                self.client.send_host_message(
                    "While that is not a blankpost, it is still pretty spammy. Try forming sentences.")
                return
        if text.lstrip().startswith('(('):
            self.client.send_host_message("Please, *please* use the OOC chat instead of polluting IC. Normal OOC is local to area. You can use /h to talk hub-wide or /g to talk across the entire server.")
            return
        # if text.startswith('/a '):
        #     part = text.split(' ')
        #     try:
        #         aid = int(part[1])
        #         if self.client in self.server.area_manager.get_area_by_id(aid).owners:
        #             target_area.append(aid)
        #         if not target_area:
        #             self.client.send_host_message(
        #                 'You don\'t own {}!'.format(self.server.area_manager.get_area_by_id(aid).name))
        #             return
        #         text = ' '.join(part[2:])
        #     except ValueError:
        #         self.client.send_host_message("That does not look like a valid area ID!")
        #         return
        # elif text.startswith('/s '):
        #     part = text.split(' ')
        #     for a in self.server.area_manager.areas:
        #         if self.client in a.owners:
        #             target_area.append(a.id)
        #     if not target_area:
        #         self.client.send_host_message('You don\'t any areas!')
        #         return
        #     text = ' '.join(part[1:])
        if msg_type not in ('chat', '0', '1'):
            return
        if msg_type == 'chat': #For foregrounds
            msg_type = '1'
        if anim_type not in (0, 1, 2, 5, 6):
            return
        if cid != self.client.char_id:
            return
        if sfx_delay < 0:
            return
        if button not in (0, 1, 2, 3, 4):
            return
        if evidence < 0:
            return
        if ding not in (0, 1):
            return
        if color not in (0, 1, 2, 3, 4, 5, 6, 7, 8):
            return
        if len(showname) > 15:
            self.client.send_host_message("Your IC showname is way too long!")
            return
        if nonint_pre == 1:
            if button in (1, 2, 3, 4, 23):
                if anim_type == 1 or anim_type == 2:
                    anim_type = 0
                elif anim_type == 6:
                    anim_type = 5
        if self.client.hub.non_int_pres_only:
            if anim_type == 1 or anim_type == 2:
                anim_type = 0
                nonint_pre = 1
            elif anim_type == 6:
                anim_type = 5
                nonint_pre = 1
        if not self.client.hub.shouts_allowed:
            # Old clients communicate the objecting in anim_type.
            if anim_type == 2:
                anim_type = 1
            elif anim_type == 6:
                anim_type = 5
            # New clients do it in a specific objection message area.
            button = 0
            # Turn off the ding.
            ding = 0
        if color == 2 and not (self.client.is_mod):
            color = 0
        if color == 6:
            text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # remove all unicode to prevent redtext abuse
            if len(text.strip(' ')) == 1:
                color = 0
            else:
                if text.strip(' ') in ('<num>', '<percent>', '<dollar>', '<and>'):
                    color = 0
        if self.client.pos:
            pos = self.client.pos
        else:
            if pos not in ('def', 'pro', 'hld', 'hlp', 'jud', 'wit', 'jur', 'sea'):
                return
        msg = text[:256]
        if self.client.shaken:
            msg = self.client.shake_message(msg)
        if self.client.disemvowel:
            msg = self.client.disemvowel_message(msg)
        self.client.pos = pos
        if evidence:
            if self.client.area.evi_list.evidences[self.client.evi_list[evidence] - 1].pos != 'all':
                self.client.area.evi_list.evidences[self.client.evi_list[evidence] - 1].pos = 'all'
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

        if self.client.is_cm and len(self.client.broadcast_ic) > 0:
            i = 0
            for b in self.client.broadcast_ic:
                area = self.client.hub.get_area_by_id(b)
                if area:
                    if area.pos_lock in ('def', 'pro', 'hld', 'hlp', 'jud', 'wit'):
                        pos = area.pos_lock
                    area.send_command('MS', 'broadcast', pre, folder, anim, msg, pos, sfx, anim_type, cid,
                                        sfx_delay, button, self.client.evi_list[evidence], flip, ding, color, showname,
                                        charid_pair, other_folder, other_emote, offset_pair, other_offset, other_flip,
                                        nonint_pre)
                    area.set_next_msg_delay(len(msg))
                    if (area.is_recording):
                            current_time = strftime("%H:%M:%S UTC", gmtime())
                            area.recorded_messages.append('[{}][Broadcast][{}] {}: {}'.format(
                                current_time, self.client.id, self.client.get_char_name(), msg))
                            #self.client.area.recorded_messages.append(args)
                    i += 1
            self.client.send_host_message(
                'Broadcasting message to {} areas.'.format(len(self.client.broadcast_ic)))
        else:
            if self.client.area.pos_lock in ('def', 'pro', 'hld', 'hlp', 'jud', 'wit'):
                pos = self.client.area.pos_lock
            self.client.area.send_command('MS', msg_type, pre, folder, anim, msg, pos, sfx, anim_type, cid,
                                        sfx_delay, button, self.client.evi_list[evidence], flip, ding, color, showname,
                                        charid_pair, other_folder, other_emote, offset_pair, other_offset, other_flip,
                                        nonint_pre)
            self.client.area.set_next_msg_delay(len(msg))
            if (self.client.area.is_recording):
                current_time = strftime("%H:%M:%S UTC", gmtime())
                self.client.area.recorded_messages.append('[{}][{}] {}: {}'.format(
                    current_time, self.client.id, self.client.get_char_name(), msg))

        logger.log_server('[IC][{}][{}]{}'.format(self.client.hub.abbreviation, self.client.area.id, self.client.get_char_name(), msg),
                          self.client)

        if (self.client.area.is_recording):
            current_time = strftime("%H:%M:%S UTC", gmtime())
            self.client.area.recorded_messages.append('[{}][{}] {}: {}'.format(
                current_time, self.client.id, self.client.get_char_name(), msg))

    def net_cmd_ct(self, args):
        """ OOC Message

        CT#<name:string>#<message:string>#%

        """
        if self.client.is_ooc_muted:  # Checks to see if the client has been muted by a mod
            self.client.send_host_message("You have been muted by a moderator")
            return
        if not self.validate_net_cmd(args, self.ArgType.STR, self.ArgType.STR):
            return
        ooc_name = re.sub('\s+', ' ', args[0]).strip() #Strip the ooc_name of any excess whitespace
        if self.client.name != args[0] and self.client.fake_name != args[0]:
            if self.client.is_valid_name(args[0]):
                self.client.name = args[0]
                self.client.fake_name = args[0]
            else:
                self.client.fake_name = args[0]
        if self.client.name == '':
            self.client.send_host_message('You must insert a name with at least one letter')
            return
        if len(self.client.name) > 30:
            self.client.send_host_message('Your OOC name is too long! Limit it to 30 characters.')
            return
        for c in self.client.name:
            if unicodedata.category(c) == 'Cf':
                self.client.send_host_message('You cannot use format characters in your name!')
                return
        if self.client.name.startswith(self.server.config['hostname']) or self.client.name.startswith(
                '<dollar>G') or self.client.name.startswith('CM') or self.client.name.startswith('GM'):
            self.client.send_host_message('That name is reserved!')
            return
        if args[1].startswith(' /'):
            self.client.send_host_message(
                'Your message was not sent for safety reasons: you left a space before that slash.')
            return
        if args[1].startswith('/'):
            spl = args[1][1:].split(' ', 1)
            cmd = spl[0].lower()
            arg = ''
            if len(spl) == 2:
                arg = spl[1][:256]
            try:
                called_function = 'ooc_cmd_{}'.format(cmd)
                getattr(commands, called_function)(self.client, arg)
            except AttributeError:
                print('Attribute error with ' + called_function)
                self.client.send_host_message('Invalid command.')
            except (ClientError, AreaError, ArgumentError, ServerError) as ex:
                self.client.send_host_message(ex)
        else:
            if self.client.shaken:
                args[1] = self.client.shake_message(args[1])
            if self.client.disemvowel:
                args[1] = self.client.disemvowel_message(args[1])
            self.client.area.send_command('CT', self.client.name, args[1])
            # self.client.area.send_owner_command('CT', '[' + self.client.hub.abbreviation + ']' + self.client.name,
            #                                     args[1])
            logger.log_server(
                '[OOC][{}][{}]{}'.format(self.client.hub.abbreviation, self.client.get_char_name(),
                                         args[1]), self.client)

    def net_cmd_mc(self, args):
        """ Play music.

        MC#<song_name:int>#<???:int>#%

        """
        try:
            hub = self.server.hub_manager.get_hub_by_name(args[0])
            self.client.change_hub(hub)
        except AreaError:
            if self.client.is_muted:  # Checks to see if the client has been muted by a mod
                self.client.send_host_message("You have been muted by a moderator")
                return
            if not self.client.is_dj:
                self.client.send_host_message('You were blockdj\'d by a moderator.')
                return
            if self.client.area.cannot_ic_interact(self.client):
                self.client.send_host_message(
                    "You are not on the area's invite list, and thus, you cannot change music!")
                return
            if not self.validate_net_cmd(args, self.ArgType.STR, self.ArgType.INT) and not self.validate_net_cmd(args,
                                                                                                                 self.ArgType.STR,
                                                                                                                 self.ArgType.INT,
                                                                                                                 self.ArgType.STR):
                return
            if args[1] != self.client.char_id:
                return
            if self.client.change_music_cd():
                self.client.send_host_message(
                    'You changed song too many times. Please try again after {} seconds.'.format(
                        int(self.client.change_music_cd())))
                return
            try:
                if args[0].startswith('=='): #Trying to stop music because we pressed a category track
                    if len(args) > 2:
                        showname = args[2]
                        if len(showname) > 0 and not self.client.hub.showname_changes_allowed:
                            self.client.send_host_message("Showname changes are forbidden in this hub!")
                            return
                        self.client.area.play_music_shownamed('Stop', self.client.char_id, showname, 0)
                    else:
                        self.client.area.play_music('Stop', self.client.char_id, 0)
                    logger.log_server('[{}][{}]Stopped music.'
                                        .format(self.client.hub.abbreviation, self.client.get_char_name()),
                                        self.client)
                    return
                name, length = self.server.get_song_data(args[0])

                # if self.client.area.jukebox:
                #     showname = ''
                #     if len(args) > 2:
                #         showname = args[2]
                #         if len(showname) > 0 and not self.client.area.showname_changes_allowed:
                #             self.client.send_host_message("Showname changes are forbidden in this area!")
                #             return
                #     self.client.area.add_jukebox_vote(self.client, name, length, showname)
                #     logger.log_server('[{}][{}]Added a jukebox vote for {}.'.format(self.client.hub.abbreviation,
                #                                                                     self.client.get_char_name(), name),
                #                       self.client)
                # else:
                if len(args) > 2:
                    showname = args[2]
                    if len(showname) > 0 and not self.client.hub.showname_changes_allowed:
                        self.client.send_host_message("Showname changes are forbidden in this hub!")
                        return

                    if self.client.is_cm and len(self.client.broadcast_ic) > 0:
                        i = 0
                        for b in self.client.broadcast_ic:
                            area = self.client.hub.get_area_by_id(b)
                            if area:
                                area.play_music_shownamed(
                                    name, self.client.char_id, showname, length)
                                i += 1
                        self.client.send_host_message(
                            'Broadcasting music to {} areas.'.format(len(self.client.broadcast_ic)))
                    else:
                        self.client.area.play_music_shownamed(name, self.client.char_id, showname, length)
                    # self.client.area.add_music_playing_shownamed(self.client, showname, name)
                else:
                    if self.client.is_cm and len(self.client.broadcast_ic) > 0:
                        i = 0
                        for b in self.client.broadcast_ic:
                            area = self.client.hub.get_area_by_id(b)
                            if area:
                                area.play_music(
                                    name, self.client.char_id, length)
                                i += 1
                        self.client.send_host_message(
                            'Broadcasting music to {} areas.'.format(len(self.client.broadcast_ic)))
                    else:
                        self.client.area.play_music(name, self.client.char_id, length)
                    # self.client.area.add_music_playing(self.client, name)

                logger.log_server('[{}][{}]Changed music to {}.'
                                    .format(self.client.hub.abbreviation, self.client.get_char_name(), name),
                                    self.client)
            except ServerError:
                self.client.send_host_message('Error: song {} isn\'t recognized by server!'.format(args[0]))
        except ClientError as ex:
            self.client.send_host_message(ex)

    def net_cmd_rt(self, args):
        """ Plays the Testimony/CE animation.

        RT#<type:string>#%

        """
        if not self.client.hub.shouts_allowed:
            self.client.send_host_message("You cannot use the testimony buttons here!")
            return
        if self.client.is_muted:  # Checks to see if the client has been muted by a mod
            self.client.send_host_message("You have been muted by a moderator")
            return
        if not self.client.can_wtce:
            self.client.send_host_message('You were blocked from using judge signs by a moderator.')
            return
        if self.client.area.cannot_ic_interact(self.client):
            self.client.send_host_message(
                "You are not on the area's invite list, and thus, you cannot use the WTCE buttons!")
            return
        if not self.validate_net_cmd(args, self.ArgType.STR) and not self.validate_net_cmd(args, self.ArgType.STR,
                                                                                           self.ArgType.INT):
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
            self.client.send_host_message(
                'You used witness testimony/cross examination signs too many times. Please try again after {} seconds.'.format(
                    int(self.client.wtce_mute())))
            return
        if len(args) == 1:
            self.client.area.send_command('RT', args[0])
        elif len(args) == 2:
            self.client.area.send_command('RT', args[0], args[1])
        self.client.area.add_to_judgelog(self.client, 'used {}'.format(sign))
        logger.log_server("[{}]{} Used WT/CE".format(self.client.hub.abbreviation, self.client.get_char_name()),
                          self.client)

    def net_cmd_setcase(self, args):
        """ Sets the casing preferences of the given client.

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
        """ Announces a case with a title, and specific set of people to look for.

        CASEA#<casetitle:string>#<need_cm:int>#<need_def:int>#<need_pro:int>#<need_judge:int>#<need_jury:int>#<need_steno:int>#%

        Note: Though all but the first arguments are ints, they technically behave as bools of 0 and 1 value.

        """
        if self.client.is_cm:
            if not self.client.can_call_case():
                raise ClientError('Please wait 60 seconds between case announcements!')

            if not args[1] == "1" and not args[2] == "1" and not args[3] == "1" and not args[4] == "1" and not args[5] == "1":
                raise ArgumentError('You should probably announce the case to at least one person.')
            msg = '=== Case Announcement ===\r\n{} [{}] is hosting {}, looking for '.format(self.client.get_char_name(),
                                                                                            self.client.id, args[0])

            lookingfor = []

            if args[1] == "1":
                lookingfor.append("defence")
            if args[2] == "1":
                lookingfor.append("prosecutor")
            if args[3] == "1":
                lookingfor.append("judge")
            if args[4] == "1":
                lookingfor.append("juror")
            if args[5] == "1":
                lookingfor.append("stenographer")

            msg = msg + ', '.join(lookingfor) + '.\r\n=================='

            self.client.server.send_all_cmd_pred('CASEA', msg, args[1], args[2], args[3], args[4], args[5], '1')

            self.client.set_case_call_delay()

            logger.log_server('[{}][{}][CASE_ANNOUNCEMENT]{}, DEF: {}, PRO: {}, JUD: {}, JUR: {}, STENO: {}.'.format(
                self.client.hub.abbreviation, self.client.get_char_name(), args[0], args[1], args[2], args[3], args[4], args[5]),
                self.client)
        else:
            raise ClientError('You cannot announce a case in an area where you are not a CM!')


    def net_cmd_hp(self, args):
        """ Sets the penalty bar.

        HP#<type:int>#<new_value:int>#%

        """
        if self.client.is_muted:  # Checks to see if the client has been muted by a mod
            self.client.send_host_message("You have been muted by a moderator")
            return
        if self.client.area.cannot_ic_interact(self.client):
            self.client.send_host_message(
                "You are not on the area's invite list, and thus, you cannot change the Confidence bars!")
            return
        if not self.validate_net_cmd(args, self.ArgType.INT, self.ArgType.INT):
            return
        try:
            self.client.area.change_hp(args[0], args[1])
            self.client.area.add_to_judgelog(self.client, 'changed the penalties')
            logger.log_server('[{}]{} changed HP ({}) to {}'
                              .format(self.client.hub.abbreviation, self.client.get_char_name(), args[0], args[1]),
                              self.client)
        except AreaError:
            return

    def net_cmd_pe(self, args):
        """ Adds a piece of evidence.

        PE#<name: string>#<description: string>#<image: string>#%

        """
        if len(args) < 3:
            return
        # evi = Evidence(args[0], args[1], args[2], self.client.pos)
        self.client.area.evi_list.add_evidence(self.client, args[0], args[1], args[2], 'all')
        self.client.area.broadcast_evidence_list()

    def net_cmd_de(self, args):
        """ Deletes a piece of evidence.

        DE#<id: int>#%

        """

        self.client.area.evi_list.del_evidence(self.client, self.client.evi_list[int(args[0])])
        self.client.area.broadcast_evidence_list()

    def net_cmd_ee(self, args):
        """ Edits a piece of evidence.

        EE#<id: int>#<name: string>#<description: string>#<image: string>#%

        """

        if len(args) < 4:
            return

        evi = (args[1], args[2], args[3], 'all')

        self.client.area.evi_list.edit_evidence(self.client, self.client.evi_list[int(args[0])], evi)
        self.client.area.broadcast_evidence_list()

        desc = self.client.area.evi_list.evidences[self.client.evi_list[int(
            args[0])]].desc

        if(args[1] == '/loadhub'):
            if not self.client.is_mod and not self.client.is_cm:
                self.client.send_host_message(
                    "You must be authorized to do that.")
                return
            try:
                self.client.hub.load(desc.strip())
                self.client.hub.send_host_message(
                    "Loading hub save data...")
                self.client.area.evi_list.del_evidence(
                    self.client, self.client.evi_list[int(args[0])])
                self.client.area.broadcast_evidence_list()
            except:
                self.client.send_host_message(
                    "Could not load hub save data! Try pressing the [X] and make sure if your save data is correct.")

    def make_valid_string(self, name):
        printable = string.ascii_letters + string.digits + string.punctuation
        print(printable)
        if not set(name).issubset(set(printable)):
            name = re.sub('[{}]'.format(printable), '', name)
        return name

    def net_cmd_zz(self, args):
        """ Sent on mod call.

        """
        if self.client.is_muted:  # Checks to see if the client has been muted by a mod
            self.client.send_host_message("You have been muted by a moderator")
            return

        if not self.client.can_call_mod():
            self.client.send_host_message("You must wait 30 seconds between mod calls.")
            return

        current_time = strftime("%H:%M", localtime())

        if len(args) < 1:
            self.server.send_all_cmd_pred('ZZ', '[{}] {} ({}) in {} without reason (not using the Case Café client?)'
                                          .format(current_time, self.client.get_char_name(), self.client.get_ip(),
                                                  self.client.area.name), pred=lambda c: c.is_mod)
            self.client.set_mod_call_delay()
            logger.log_server(
                '[{}]{} called a moderator.'.format(self.client.hub.abbreviation, self.client.get_char_name()),
                self.client)
        else:
            self.server.send_all_cmd_pred('ZZ', '[{}] {} ({}) in {} with reason: {}'
                                          .format(current_time, self.client.get_char_name(), self.client.get_ip(),
                                                  self.client.area.name, args[0][:100]), pred=lambda c: c.is_mod)
            self.client.set_mod_call_delay()
            logger.log_server(
                '[{}]{} called a moderator: {}.'.format(self.client.hub.abbreviation, self.client.get_char_name(),
                                                        args[0]), self.client)

    def net_cmd_opKICK(self, args):
        self.net_cmd_ct(['opkick', '/kick {}'.format(args[0])])

    def net_cmd_opBAN(self, args):
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
        'SETCASE': net_cmd_setcase, # set case-announcement preferences for user
        'CASEA': net_cmd_casea, # announce a case
        'HP': net_cmd_hp,  # penalties
        'PE': net_cmd_pe,  # add evidence
        'DE': net_cmd_de,  # delete evidence
        'EE': net_cmd_ee,  # edit evidence
        'ZZ': net_cmd_zz,  # call mod button
        'opKICK': net_cmd_opKICK,  # /kick with guard on
        'opBAN': net_cmd_opBAN,  # /ban with guard on
    }
