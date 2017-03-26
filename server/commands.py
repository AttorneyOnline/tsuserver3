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
import random

from server import logger
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


def ooc_cmd_reload(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    try:
        client.reload_character()
    except ClientError:
        raise
    client.send_host_message('Character reloaded.')


def ooc_cmd_g(client, arg):
    if client.muted_global:
        raise ClientError('You have the global chat muted.')
    if len(arg) == 0:
        raise ArgumentError("Can't send an empty message.")
    client.server.broadcast_global(client, arg)
    logger.log_server('[{}][{}][GLOBAL]{}.'.format(client.area.id, client.get_char_name(), arg), client)


def ooc_cmd_gm(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if client.muted_global:
        raise ClientError('You have the global chat muted.')
    if len(arg) == 0:
        raise ArgumentError("Can't send an empty message.")
    client.server.broadcast_global(client, arg, True)
    logger.log_server('[{}][{}][GLOBAL-MOD]{}.'.format(client.area.id, client.get_char_name(), arg), client)


def ooc_cmd_lm(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError("Can't send an empty message.")
    client.area.send_command('CT', '{}[MOD][{}]'
                             .format(client.server.config['hostname'], client.get_char_name()), arg)
    logger.log_server('[{}][{}][LOCAL-MOD]{}.'.format(client.area.id, client.get_char_name(), arg), client)


def ooc_cmd_announce(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError("Can't send an empty message.")
    client.server.send_all_cmd_pred('CT', '{}'.format(client.server.config['hostname']),
                                    '=== Announcement ===\r\n{}\r\n=================='.format(arg))
    logger.log_server('[{}][{}][ANNOUNCEMENT]{}.'.format(client.area.id, client.get_char_name(), arg), client)


def ooc_cmd_judgelog(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        area = client.area
    else:
        try:
            area = client.server.area_manager.get_area_by_id(int(arg))
        except AreaError:
            raise
        except ValueError:
            raise ArgumentError('Invalid area ID. Use /judgelog <id>.')
    msg = '=== Judge Log [{}] ==='.format(area.id)
    for j in area.judgelog:
        msg += '\r\n{}'.format(j)
    client.send_host_message(msg)


def ooc_cmd_toggleglobal(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.muted_global = not client.muted_global
    glob_stat = 'on'
    if client.muted_global:
        glob_stat = 'off'
    client.send_host_message('Global chat turned {}.'.format(glob_stat))


def ooc_cmd_need(client, arg):
    if client.muted_adverts:
        raise ClientError('You have advertisements muted.')
    if len(arg) == 0:
        raise ArgumentError("You must specify what you need.")
    client.server.broadcast_need(client, arg)
    logger.log_server('[{}][{}][NEED]{}.'.format(client.area.id, client.get_char_name(), arg), client)


def ooc_cmd_toggleadverts(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.muted_adverts = not client.muted_adverts
    adv_stat = 'on'
    if client.muted_adverts:
        adv_stat = 'off'
    client.send_host_message('Advertisements turned {}.'.format(adv_stat))


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


def ooc_cmd_getarea(client, arg):
    if len(arg) == 0:
        try:
            client.send_area_info(client.area.id)
        except AreaError:
            raise
    else:
        try:
            client.send_area_info(int(arg))
        except AreaError:
            raise
        except ValueError:
            raise ArgumentError('Invalid argument. Use /getarea <id>.')


def ooc_cmd_getareas(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command takes no arguments.')
    client.send_all_area_info()


def ooc_cmd_doc(client, arg):
    if len(arg) == 0:
        client.send_host_message('Document: {}'.format(client.area.doc))
        logger.log_server(
            '[{}][{}]Requested document. Link: {}'.format(client.area.id, client.get_char_name(), client.area.doc))
    else:
        client.area.change_doc(arg)
        client.area.send_host_message('{} changed the doc link.'.format(client.get_char_name()))
        logger.log_server('[{}][{}]Changed document to: {}'.format(client.area.id, client.get_char_name(), arg))


def ooc_cmd_cleardoc(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    client.send_host_message('Document cleared.')
    logger.log_server('[{}][{}]Cleared document. Old link: {}'
                      .format(client.area.id, client.get_char_name(), client.area.doc))
    client.area.change_doc()


def ooc_cmd_status(client, arg):
    if len(arg) == 0:
        client.send_host_message('Current status: {}'.format(client.area.status))
    else:
        try:
            client.area.change_status(arg)
            client.area.send_host_message('{} changed status to {}.'.format(client.get_char_name(), client.area.status))
            logger.log_server(
                '[{}][{}]Changed status to {}'.format(client.area.id, client.get_char_name(), client.area.status))
        except AreaError:
            raise


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
        client.send_host_message('PM sent to {}, {} user(s). Message: {}'.format(args[0], len(target_clients), msg))
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


def ooc_cmd_randomchar(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    try:
        free_id = client.area.get_rand_avail_char_id()
    except AreaError:
        raise
    try:
        client.change_character(free_id)
    except ClientError:
        raise
    client.send_host_message('Randomly switched to {}'.format(client.get_char_name()))


def ooc_cmd_help(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    help_url = 'https://github.com/AttorneyOnlineVidya/tsuserver3'
    help_msg = 'Available commands, source code and issues can be found here: {}'.format(help_url)
    client.send_host_message(help_msg)


def ooc_cmd_pos(client, arg):
    if len(arg) == 0:
        client.change_position()
        client.send_host_message('Position reset.')
    else:
        try:
            client.change_position(arg)
        except ClientError:
            raise
        client.send_host_message('Position changed.')


def ooc_cmd_bg(client, arg):
    if len(arg) == 0:
        raise ArgumentError('You must specify a name. Use /bg <background>.')
    if not client.is_mod and client.area.bg_lock == "true":
        raise AreaError("This area's background is locked")
    try:
        client.area.change_background(arg)
    except AreaError:
        raise
    client.area.send_host_message('{} changed the background to {}.'.format(client.get_char_name(), arg))
    logger.log_server('[{}][{}]Changed background to {}'.format(client.area.id, client.get_char_name(), arg), client)

def ooc_cmd_bglock(client,arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    if client.area.bg_lock  == "true":
        client.area.bg_lock = "false"
    else:
        client.area.bg_lock = "true"
    client.area.send_host_message('A mod has set the background lock to {}.'.format(client.area.bg_lock))
    logger.log_server('[{}][{}]Changed bglock to {}'.format(client.area.id, client.get_char_name(), client.area.bg_lock), client)


def ooc_cmd_motd(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.send_motd()


def ooc_cmd_roll(client, arg):
    roll_max = 11037
    if len(arg) != 0:
        try:
            val = int(arg)
            if not 1 <= val <= roll_max:
                raise ArgumentError('Roll value must be between 1 and {}.'.format(roll_max))
        except ValueError:
            raise ArgumentError('Argument must be a number')
    else:
        val = 6
    roll = random.randint(1, val)
    client.area.send_host_message('{} rolled {} out of {}.'.format(client.get_char_name(), roll, val))
    logger.log_server(
        '[{}][{}]Used /roll and got {} out of {}.'.format(client.area.id, client.get_char_name(), roll, val))


def ooc_cmd_coinflip(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    coin = ['heads', 'tails']
    flip = random.choice(coin)
    client.area.send_host_message('{} flipped a coin and got {}.'.format(client.get_char_name(), flip))
    logger.log_server(
        '[{}][{}]Used /coinflip and got {}.'.format(client.area.id, client.get_char_name(), flip))


def ooc_cmd_currentmusic(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    if client.area.current_music == '':
        raise ClientError('There is no music currently playing.')
    client.send_host_message('The current music is {} and was played by {}.'.format(client.area.current_music,
                                                                                    client.area.current_music_player))


def ooc_cmd_login(client, arg):
    if len(arg) == 0:
        raise ArgumentError('You must specify the password.')
    try:
        client.auth_mod(arg)
    except ClientError:
        raise
    client.send_host_message('Logged in as a moderator.')
    logger.log_server('Logged in as moderator.', client)


def ooc_cmd_kick(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    targets = client.server.client_manager.get_targets(client, arg)
    if targets:
        for c in targets:
            logger.log_server('Kicked {}.'.format(c.get_ip()), client)
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
    logger.log_server('Banned {}.'.format(ip), client)

def ooc_cmd_unban(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    ip = arg.strip()
    if len(ip) < 7:
        raise ArgumentError('You must specify an IP.')
    try:
        client.server.ban_manager.remove_ban(ip)
    except ServerError:
        raise
    logger.log_server('Unbanned {}.'.format(ip), client)

def ooc_cmd_play(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a song.')
    client.area.play_music(arg, client.char_id, -1)
    client.area.add_music_playing(client, arg)
    logger.log_server('[{}][{}]Changed music to {}.'.format(client.area.id, client.get_char_name(), arg), client)


def ooc_cmd_mute(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    targets = client.server.client_manager.get_targets(client, arg)
    if targets:
        for c in targets:
            logger.log_server('Muted {}.'.format(c.get_ip()), client)
            c.send_command('MU', c.char_id)
            c.is_muted = True
        client.send_host_message('Muted {} existing client(s).'.format(len(targets)))
    else:
        client.send_host_message("No targets found.")


def ooc_cmd_unmute(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    if arg == "all":
        targets = client.server.client_manager.get_muted_clients()
    else:
        targets = client.server.client_manager.get_targets(client, arg)
    if targets:
        for c in targets:
            logger.log_server('Unmuted {}.'.format(c.get_ip()), client)
            c.send_command('UM', c.char_id)
            c.is_muted = False
        client.send_host_message('Unmuted {} existing client(s).'.format(len(targets)))
    else:
        client.send_host_message("No targets found.")
