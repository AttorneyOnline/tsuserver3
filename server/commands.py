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

from server.exceptions import ClientError, ServerError, ArgumentError


def ooc_cmd_switch(client, args):
    if len(args) == 0:
        raise ArgumentError('You must specify a character name.')
    try:
        cid = client.server.get_char_id_by_name(' '.join(args))
    except ServerError:
        raise
    try:
        client.change_character(cid)
    except ClientError:
        raise
    client.send_host_message('Character changed.')


def ooc_cmd_g(client, args):
    if len(args) == 0:
        raise ArgumentError("Can't send an empty message.")
    client.server.broadcast_global(client, ' '.join(args))


def ooc_cmd_need(client, args):
    if len(args) == 0:
        raise ArgumentError("You must specify what you need.")
    client.server.broadcast_need(client, ' '.join(args))
