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

from server.exceptions import ClientError, ServerError, ArgumentError, AreaError


def ooc_cmd_switch(client, arg):
    if len(arg) == 0:
        raise ArgumentError('You must specify a character name.')
    try:
        cid = client.server.get_char_id_by_name(arg)
    except ServerError:
        raise
    try:
        client.change_character(cid)
    except ClientError:
        raise
    client.send_host_message('Character changed.')


def ooc_cmd_g(client, arg):
    if len(arg) == 0:
        raise ArgumentError("Can't send an empty message.")
    client.server.broadcast_global(client, arg)


def ooc_cmd_need(client, arg):
    if len(arg) == 0:
        raise ArgumentError("You must specify what you need.")
    client.server.broadcast_need(client, arg)


def ooc_cmd_area(client, arg):
    args = arg.split()
    if len(args) == 0:
        client.send_area_list()
    elif len(args) == 1:
        try:
            area = client.server.area_manager.get_area_by_id(int(args[0]))
            client.change_area(area)
        except ValueError:
            raise ArgumentError('Area ID must be a number.')
        except (AreaError, ClientError):
            raise
    else:
        raise ArgumentError('Too many arguments. Use /area <id>.')


def ooc_cmd_pm(client, arg):
    args = arg.split()
    if len(args) < 2:
        raise ArgumentError('Not enough arguments. Use /pm <target> <message>.')
    target_clients = []
    msg = ' '.join(args[1:])
    for char_name in client.server.char_list:
        if arg.lower().startswith(char_name.lower()):
            char_len = len(char_name.split())
            to_search = ' '.join(args[:char_len])
            c = client.area.get_target_by_char_name(to_search)
            if c:
                target_clients.append(c)
                msg = ' '.join(args[char_len:])
                if not msg:
                    raise ArgumentError('Not enough arguments. Use /pm <target> <message>.')
                break
    if not target_clients:
        target_clients = client.server.client_manager.get_targets(client, args[0])
    if not target_clients:
        client.send_host_message('No targets found.')
    else:
        client.send_host_message('PM sent to {} user(s). Message: {}'.format(len(target_clients), msg))
        for c in target_clients:
            c.send_host_message(
                'PM from {} in {} ({}): {}'.format(client.name, client.area.name, client.get_char_name(), msg))


def ooc_cmd_charselect(client, arg):
    if arg:
        if client.is_mod:
            targets = client.server.client_manager.get_targets(client, arg)
            if targets:
                for c in targets:
                    c.char_select()
                client.send_host_message('Forced {} client(s) into character selection.'.format(len(targets)))
            else:
                client.send_host_message('No targets found.')
        else:
            raise ArgumentError("This command doesn't take any arguments.")
    else:
        client.char_select()


def ooc_cmd_login(client, arg):
    if len(arg) == 0:
        raise ArgumentError('You must specify the password.')
    try:
        client.auth_mod(arg)
    except ClientError:
        raise
    client.send_host_message('Logged in as a moderator.')


def ooc_cmd_kick(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    targets = client.server.client_manager.get_targets(client, arg)
    if targets:
        for c in targets:
            c.disconnect()
        client.send_host_message("Kicked {} client(s).".format(len(targets)))
    else:
        client.send_host_message("No targets found.")


def ooc_cmd_ban(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    ip = arg.strip()
    if len(ip) < 7:
        raise ArgumentError('You must specify an IP.')
    try:
        client.server.ban_manager.add_ban(ip)
    except ServerError:
        raise
    targets = client.server.client_manager.get_targets_by_ip(ip)
    if targets:
        for c in targets:
            c.disconnect()
        client.send_host_message('Kicked {} existing client(s).'.format(len(targets)))
    client.send_host_message('Added {} to the banlist.'.format(ip))
