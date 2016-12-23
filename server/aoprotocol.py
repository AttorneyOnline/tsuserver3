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

    def data_received(self, data):
        print(data)
        self.buffer += data.decode()
        if len(self.buffer) > 8192:
            self.client.disconnect()
        for msg in self.get_messages():
            if msg[0] in ('#', '3', '4'):
                if msg[0] == '#':
                    msg = msg[1:]
                spl = msg.split('#', 1)
                msg = '#'.join([fanta_decrypt(spl[0])] + spl[1:])
            try:
                cmd, *args = msg.split('#')
                print('{}, {}'.format(cmd, args))
                self.net_cmd_dispatcher[cmd](self, args)
            except KeyError:
                return

    def connection_made(self, transport):
        self.client = self.server.new_client(transport)
        self.client.send_command('decryptor', 34)  # just fantacrypt things

    def connection_lost(self, exc):
        self.client.disconnect()

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
        if needs_auth and self.client.char_id < 0:
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
        # todo check bans
        self.client.hdid = args[0]
        self.client.send_command('ID', self.client.id, self.server.version)
        self.client.send_command('PN', self.server.get_player_count(), 100)

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
        self.client.change_character(cid)

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
        if cid1 != cid2 or cid1 != self.client.char_id or not self.server.is_valid_char_id(cid1):
            return
        if sfx_delay < 0:
            return
        if button not in (0, 1, 2, 3):
            return
        if ding not in (0, 1):
            return
        self.client.area.send_command('MS', msg_type, pre, folder, anim, text[:256], pos, sfx, anim_type, cid1,
                                      sfx_delay, button, unk, cid2, ding, color)

    def net_cmd_ct(self, args):
        if not self.validate_net_cmd(args, self.ArgType.STR, self.ArgType.STR):
            return
        if self.client.name == '':
            self.client.name = args[0]
        self.client.area.send_command('CT', self.client.name, args[1])

    net_cmd_dispatcher = {
        'HI': net_cmd_hi,  # handshake
        'askchaa': net_cmd_askchaa,  # ask for list lengths
        'askchar2': net_cmd_askchar2,  # ask for list of characters
        'AN': net_cmd_an,  # character list
        'AE': net_cmd_ae,  # evidence list
        'AM': net_cmd_am,  # music list
        'CC': net_cmd_cc,  # select character
        'MS': net_cmd_ms,  # IC message
        'CT': net_cmd_ct,  # OOC message
    }
