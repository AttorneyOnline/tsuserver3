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
from enum import Enum

from server import commands
from server import logger
from server.exceptions import ClientError, AreaError, ArgumentError, ServerError
from server.fantacrypt import fanta_decrypt


class AOProtocol(asyncio.Protocol):
    class ArgType(Enum):
        STR = 1,
        INT = 2

    def __init__(self, server):
        super().__init__()
        self.server = server
        self.client = None
        self.buffer = ''
        self.ping_timeout = None

    def data_received(self, data):
        self.buffer += data.decode()
        if len(self.buffer) > 8192:
            self.client.disconnect()
        for msg in self.get_messages():
            if len(msg) < 2:
                self.client.disconnect()
                return
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
                return

    def connection_made(self, transport):
        self.client = self.server.new_client(transport)
        self.ping_timeout = asyncio.get_event_loop().call_later(self.server.config['timeout'], self.client.disconnect)
        self.client.send_command('decryptor', 34)  # just fantacrypt things

    def connection_lost(self, exc):
        self.server.remove_client(self.client)

    def get_messages(self):
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
        if needs_auth and self.client.char_id == -1:
            return False
        if len(args) != len(types):
            return False
        for i, arg in enumerate(args):
            if len(arg) == 0:
                return False
            if types[i] == self.ArgType.INT:
                try:
                    args[i] = int(arg)
                except ValueError:
                    return False
        return True

    def net_cmd_hi(self, args):
        if not self.validate_net_cmd(args, self.ArgType.STR, needs_auth=False):
            return
        self.client.hdid = args[0]
        if self.server.ban_manager.is_banned(self.client.get_ip()):
            self.client.disconnect()
            return
        self.client.send_command('ID', self.client.id, self.server.version)
        self.client.send_command('PN', self.server.get_player_count() - 1, self.server.config['playerlimit'])

    def net_cmd_ch(self, _):
        self.client.send_command('CHECK')
        self.ping_timeout.cancel()
        self.ping_timeout = asyncio.get_event_loop().call_later(self.server.config['timeout'], self.client.disconnect)

    def net_cmd_askchaa(self, _):
        char_cnt = len(self.server.char_list)
        evi_cnt = 0
        music_cnt = sum([len(x) for x in self.server.music_pages_ao1])
        self.client.send_command('SI', char_cnt, evi_cnt, music_cnt)

    def net_cmd_askchar2(self, _):
        self.client.send_command('CI', *self.server.char_pages_ao1[0])

    def net_cmd_an(self, args):
        if not self.validate_net_cmd(args, self.ArgType.INT, needs_auth=False):
            return
        if len(self.server.char_pages_ao1) > args[0] >= 0:
            self.client.send_command('CI', *self.server.char_pages_ao1[args[0]])
        else:
            self.client.send_command('EM', *self.server.music_pages_ao1[0])

    def net_cmd_ae(self, _):
        pass  # todo evidence maybe later

    def net_cmd_am(self, args):
        if not self.validate_net_cmd(args, self.ArgType.INT, needs_auth=False):
            return
        if len(self.server.music_pages_ao1) > args[0] >= 0:
            self.client.send_command('EM', *self.server.music_pages_ao1[args[0]])
        else:
            self.client.send_done()

    def net_cmd_cc(self, args):
        if not self.validate_net_cmd(args, self.ArgType.INT, self.ArgType.INT, self.ArgType.STR, needs_auth=False):
            return
        cid = args[1]
        try:
            self.client.change_character(cid)
        except ClientError:
            return

    def net_cmd_ms(self, args):
        if not self.validate_net_cmd(args, self.ArgType.STR, self.ArgType.STR, self.ArgType.STR, self.ArgType.STR,
                                     self.ArgType.STR, self.ArgType.STR, self.ArgType.STR, self.ArgType.INT,
                                     self.ArgType.INT, self.ArgType.INT, self.ArgType.INT, self.ArgType.INT,
                                     self.ArgType.INT, self.ArgType.INT, self.ArgType.INT):
            return
        msg_type, pre, folder, anim, text, pos, sfx, anim_type, cid1, sfx_delay, button, unk, cid2, ding, color = args
        if msg_type != 'chat':
            return
        if anim_type not in (0, 1, 2, 5, 6):
            return
        if cid1 != cid2 or cid1 != self.client.char_id:
            return
        if sfx_delay < 0:
            return
        if button not in (0, 1, 2, 3):
            return
        if ding not in (0, 1):
            return
        if color not in (0, 1, 2, 3, 4):
            return
        if color == 2 and not self.client.is_mod:
            color = 0
        msg = text[:256]
        self.client.area.send_command('MS', msg_type, pre, folder, anim, msg, pos, sfx, anim_type, cid1,
                                      sfx_delay, button, unk, cid2, ding, color)
        logger.log_server('[IC][{}][{}]{}'.format(self.client.area.id, self.client.get_char_name(), msg), self.client)

    def net_cmd_ct(self, args):
        if not self.validate_net_cmd(args, self.ArgType.STR, self.ArgType.STR):
            return
        if self.client.name == '':
            self.client.name = args[0]
        if args[1].startswith('/'):
            spl = args[1][1:].split(' ', 1)
            cmd = spl[0]
            arg = ''
            if len(spl) == 2:
                arg = spl[1][:256]
            try:
                getattr(commands, 'ooc_cmd_{}'.format(cmd))(self.client, arg)
            except AttributeError:
                self.client.send_host_message('Invalid command.')
            except (ClientError, AreaError, ArgumentError, ServerError) as ex:
                self.client.send_host_message(ex)
        else:
            self.client.area.send_command('CT', self.client.name, args[1])
            logger.log_server('[OOC][{}][{}]{}'.format(self.client.area.id, self.client.get_char_name(), args[1]),
                              self.client)

    def net_cmd_mc(self, args):
        if not self.validate_net_cmd(args, self.ArgType.STR, self.ArgType.INT):
            return
        if args[1] != self.client.char_id:
            return
        try:
            area = self.server.area_manager.get_area_by_name(args[0])
            self.client.change_area(area)
        except AreaError:
            try:
                name, length = self.server.get_song_data(args[0])
                self.client.area.play_music(name, self.client, length)
            except ServerError:
                return
        except ClientError as ex:
            self.client.send_host_message(ex)

    def net_cmd_rt(self, args):
        if not self.validate_net_cmd(args, self.ArgType.STR):
            return
        if args[0] not in ('testimony1', 'testimony2'):
            return
        self.client.area.send_command('RT', args[0])
        logger.log_server("[{}]{} Used WT/CE".format(self.client.area.id, self.client.get_char_name()), self.client)

    net_cmd_dispatcher = {
        'HI': net_cmd_hi,  # handshake
        'CH': net_cmd_ch,  # keepalive
        'askchaa': net_cmd_askchaa,  # ask for list lengths
        'askchar2': net_cmd_askchar2,  # ask for list of characters
        'AN': net_cmd_an,  # character list
        'AE': net_cmd_ae,  # evidence list
        'AM': net_cmd_am,  # music list
        'CC': net_cmd_cc,  # select character
        'MS': net_cmd_ms,  # IC message
        'CT': net_cmd_ct,  # OOC message
        'MC': net_cmd_mc,  # play song
        'RT': net_cmd_rt,  # WT/CE buttons
    }
