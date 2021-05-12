import shlex
import arrow

from pytimeparse import parse

from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ServerError, ArgumentError
from . import mod_only, list_commands, list_submodules, help

__all__ = [
    'ooc_cmd_motd',
    'ooc_cmd_help',
    'ooc_cmd_kick',
    'ooc_cmd_ban',
    'ooc_cmd_banhdid',
    'ooc_cmd_unban',
    'ooc_cmd_mute',
    'ooc_cmd_unmute',
    'ooc_cmd_login',
    'ooc_cmd_refresh',
    'ooc_cmd_online',
    'ooc_cmd_mods',
    'ooc_cmd_unmod',
    'ooc_cmd_ooc_mute',
    'ooc_cmd_ooc_unmute',
    'ooc_cmd_bans',
    'ooc_cmd_baninfo'
]


def ooc_cmd_motd(client, arg):
    """
    Show the message of the day.
    Usage: /motd
    """
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.send_motd()


def ooc_cmd_help(client, arg):
    """
    Show help for a command, or show general help.
    Usage: /help
    """
    import inspect
    if arg == '':
        msg = inspect.cleandoc('''
        Welcome to tsuserver3! You can use /help <command> on any known
        command to get up-to-date help on it.
        You may also use /help <category> to see available commands for that category.

        If you don't understand a specific core feature, check the official
        repository for more information:

        https://github.com/AttorneyOnline/tsuserver3 

        Available Categories:
        ''')
        msg += '\n'
        msg += list_submodules()
        client.send_ooc(msg)
    else:
        arg = arg.lower()
        try:
            client.send_ooc(help(f'ooc_cmd_{arg}'))
        except AttributeError:
            try:
                msg = f'Submodule "{arg}" commands:\n\n'
                msg += list_commands(arg)
                client.send_ooc(msg)
            except AttributeError:
                client.send_ooc(
                    'No such command or submodule has been found in the help docs.')


@mod_only()
def ooc_cmd_kick(client, arg):
    """
    Kick a player.
    Usage: /kick <ipid|*|**> [reason]
    Special cases:
     - "*" kicks everyone in the current area.
     - "**" kicks everyone in the server.
    """
    if len(arg) == 0:
        raise ArgumentError(
            'You must specify a target. Use /kick <ipid> [reason]')
    elif arg[0] == '*':
        targets = [c for c in client.area.clients if c != client]
    elif arg[0] == '**':
        targets = [c for c in client.server.client_manager.clients if c != client]
    else:
        targets = None

    args = list(arg.split(' '))
    if targets is None:
        raw_ipid = args[0]
        try:
            ipid = int(raw_ipid)
        except:
            raise ClientError(f'{raw_ipid} does not look like a valid IPID.')
        targets = client.server.client_manager.get_targets(client, TargetType.IPID,
                                                           ipid, False)

    if targets:
        reason = ' '.join(args[1:])
        if reason == '':
            reason = 'N/A'
        for c in targets:
            database.log_misc('kick', client, target=c,
                              data={'reason': reason})
            client.send_ooc("{} was kicked.".format(
                c.char_name))
            c.send_command('KK', reason)
            c.disconnect()
    else:
        client.send_ooc(
            f'No targets with the IPID {ipid} were found.')


def ooc_cmd_ban(client, arg):
    """
    Ban a user. If a ban ID is specified instead of a reason,
    then the IPID is added to an existing ban record.
    Ban durations are 6 hours by default.
    Usage: /ban <ipid> "reason" ["<N> <minute|hour|day|week|month>(s)|perma"]
    Usage 2: /ban <ipid> <ban_id>
    """
    kickban(client, arg, False)


def ooc_cmd_banhdid(client, arg):
    """
    Ban both a user's HDID and IPID.
    DANGER: Banning webAO users by HDID has unintended consequences.
    Usage: See /ban.
    """
    kickban(client, arg, True)


def _convert_ipid_to_int(value):
    try:
        return int(value)
    except ValueError:
        raise ClientError(f'{value} does not look like a valid IPID.')


@mod_only()
def kickban(client, arg: str, ban_hdid):
    args = shlex.split(arg)
    ban_id = None
    default_ban_duration = client.server.config['default_ban_duration']

    if len(args) < 2:
        raise ArgumentError('Not enough arguments.')

    elif len(args) == 2:
        ipid = _convert_ipid_to_int(args[0])
        ban_id = args[1]
        reason = None
        ban_duration = parse(str(default_ban_duration))
        unban_date = arrow.get().shift(seconds=ban_duration).datetime

    elif len(args) == 3:
        ipid = _convert_ipid_to_int(args[0])
        reason = args[1]
        duration = args[2]
        ban_duration = parse(str(duration))

        if duration is None:
            raise ArgumentError('Invalid ban duration.')
        elif 'perma' in duration.lower():
            unban_date = None
        else:
            if ban_duration is not None:
                unban_date = arrow.get().shift(seconds=ban_duration).datetime
            else:
                raise ArgumentError(f'{duration} is an invalid ban duration')

    else:
        raise ArgumentError(f'Ambiguous input: {arg}\nPlease wrap your arguments '
                            'in quotes.')

    try:
        raw_ipid = args[0]
        ipid = int(raw_ipid)
    except ValueError:
        raise ClientError(f'{raw_ipid} does not look like a valid IPID.')

    if ban_id != None:
        existing_ban = database.find_ban(None, None, ban_id)
        if existing_ban:
            if bool(existing_ban.unbanned) == True:
                raise ClientError(f'{ban_id} is already unbanned.')

    ban_id = database.ban(ipid, reason, ban_type='ipid', banned_by=client,
                          ban_id=ban_id, unban_date=unban_date)

    targets = client.server.client_manager.get_targets(
        client, TargetType.IPID, ipid, False)
    if targets:
        for c in targets:
            if ban_hdid:
                database.ban(c.hdid, reason, ban_type='hdid', ban_id=ban_id)
            c.send_command('KB', reason)
            c.disconnect()
            database.log_misc('ban', client, target=c, data={'reason': reason})
        client.send_ooc(f'{len(targets)} clients were kicked.')
    client.send_ooc(f'{ipid} was banned. Ban ID: {ban_id}')


@mod_only()
def ooc_cmd_unban(client, arg):
    """
    Unban a list of users.
    Usage: /unban <ban_id...>
    """
    if len(arg) == 0:
        raise ArgumentError(
            'You must specify a target. Use /unban <ban_id...>')
    args = list(arg.split(' '))
    client.send_ooc(f'Attempting to lift {len(args)} ban(s)...')
    for ban_id in args:
        if database.unban(ban_id):
            client.send_ooc(f'Removed ban ID {ban_id}.')
        else:
            client.send_ooc(f'{ban_id} is not on the ban list.')
        database.log_misc('unban', client, data={'id': ban_id})


@mod_only()
def ooc_cmd_mute(client, arg):
    """
    Prevent a user from speaking in-character.
    Usage: /mute <ipid>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /mute <ipid>.')
    args = list(arg.split(' '))
    client.send_ooc(f'Attempting to mute {len(args)} IPIDs.')
    for raw_ipid in args:
        if raw_ipid.isdigit():
            ipid = int(raw_ipid)
            clients = client.server.client_manager.get_targets(
                client, TargetType.IPID, ipid, False)
            if (clients):
                msg = 'Muted the IPID ' + str(ipid) + '\'s following clients:'
                for c in clients:
                    c.is_muted = True
                    database.log_misc('mute', client, target=c)
                    msg += ' ' + c.char_name + ' [' + str(c.id) + '],'
                msg = msg[:-1]
                msg += '.'
                client.send_ooc(msg)
            else:
                client.send_ooc(
                    "No targets found. Use /mute <ipid> <ipid> ... for mute.")
        else:
            client.send_ooc(
                f'{raw_ipid} does not look like a valid IPID.')


@mod_only()
def ooc_cmd_unmute(client, arg):
    """
    Unmute a user.
    Usage: /unmute <ipid>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    args = list(arg.split(' '))
    client.send_ooc(f'Attempting to unmute {len(args)} IPIDs.')
    for raw_ipid in args:
        if raw_ipid.isdigit():
            ipid = int(raw_ipid)
            clients = client.server.client_manager.get_targets(
                client, TargetType.IPID, ipid, False)
            if (clients):
                msg = f'Unmuted the IPID ${str(ipid)}\'s following clients:'
                for c in clients:
                    c.is_muted = False
                    database.log_misc('unmute', client, target=c)
                    msg += ' ' + c.char_name + ' [' + str(c.id) + '],'
                msg = msg[:-1]
                msg += '.'
                client.send_ooc(msg)
            else:
                client.send_ooc(
                    "No targets found. Use /unmute <ipid> <ipid> ... for unmute."
                )
        else:
            client.send_ooc(
                f'{raw_ipid} does not look like a valid IPID.')


def ooc_cmd_login(client, arg):
    """
    Login as a moderator.
    Usage: /login <password>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify the password.')
    login_name = None
    try:
        login_name = client.auth_mod(arg)
    except ClientError:
        client.send_command('AUTH', '0')
        database.log_misc('login.invalid', client)
        raise
    if client.area.evidence_mod == 'HiddenCM':
        client.area.broadcast_evidence_list()
    client.send_ooc('Logged in as a moderator.')
    client.send_command('AUTH', '1')
    database.log_misc('login', client, data={'profile': login_name})


@mod_only()
def ooc_cmd_refresh(client, arg):
    """
    Reload all moderator credentials, server options, and commands without
    restarting the server.
    Usage: /refresh
    """
    if len(arg) > 0:
        raise ClientError('This command does not take in any arguments!')
    else:
        try:
            client.server.refresh()
            database.log_misc('refresh', client)
            client.send_ooc('You have reloaded the server.')
        except ServerError:
            raise


def ooc_cmd_online(client, _):
    """
    Show the number of players online.
    Usage: /online
    """
    client.send_player_count()


def ooc_cmd_mods(client, arg):
    """
    Show a list of moderators online.
    Usage: /mods
    """
    client.send_area_info(-1, True)


def ooc_cmd_unmod(client, arg):
    """
    Log out as a moderator.
    Usage: /unmod
    """
    client.is_mod = False
    client.mod_profile_name = None
    if client.area.evidence_mod == 'HiddenCM':
        client.area.broadcast_evidence_list()
    client.send_ooc('you\'re not a mod now')
    client.send_command('AUTH', '-1')


@mod_only()
def ooc_cmd_ooc_mute(client, arg):
    """
    Prevent a user from talking out-of-character.
    Usage: /ooc_mute <ooc-name>
    """
    if len(arg) == 0:
        raise ArgumentError(
            'You must specify a target. Use /ooc_mute <OOC-name>.')
    targets = client.server.client_manager.get_targets(client,
                                                       TargetType.OOC_NAME,
                                                       arg, False)
    if not targets:
        raise ArgumentError('Targets not found. Use /ooc_mute <OOC-name>.')
    for target in targets:
        target.is_ooc_muted = True
        database.log_room('ooc_mute', client, client.area, target=target)
    client.send_ooc('Muted {} existing client(s).'.format(
        len(targets)))


@mod_only()
def ooc_cmd_ooc_unmute(client, arg):
    """
    Allow an OOC-muted user to talk out-of-character.
    Usage: /ooc_unmute <ooc-name>
    """
    if len(arg) == 0:
        raise ArgumentError(
            'You must specify a target. Use /ooc_unmute <OOC-name>.')
    targets = client.server.client_manager.get_ooc_muted_clients()
    if not targets:
        raise ArgumentError('Targets not found. Use /ooc_unmute <OOC-name>.')
    for target in targets:
        target.is_ooc_muted = False
        database.log_room('ooc_unmute', client, client.area, target=target)
    client.send_ooc('Unmuted {} existing client(s).'.format(
        len(targets)))


@mod_only()
def ooc_cmd_bans(client, _arg):
    """
    Get the 5 most recent bans.
    Usage: /bans
    """
    msg = 'Last 5 bans:\n'
    for ban in database.recent_bans():
        time = arrow.get(ban.ban_date).humanize()
        msg += f'{time}: {ban.banned_by_name} ({ban.banned_by}) issued ban ' \
               f'{ban.ban_id} (\'{ban.reason}\')\n'
    client.send_ooc(msg)


@mod_only()
def ooc_cmd_baninfo(client, arg):
    """
    Get information about a ban.
    Usage: /baninfo <id> ['ban_id'|'ipid'|'hdid']
    By default, id identifies a ban_id.
    """
    args = arg.split(' ')
    if len(arg) == 0:
        raise ArgumentError('You must specify an ID.')
    elif len(args) == 1:
        lookup_type = 'ban_id'
    else:
        lookup_type = args[1]

    if lookup_type not in ('ban_id', 'ipid', 'hdid'):
        raise ArgumentError('Incorrect lookup type.')

    bans = database.ban_history(**{lookup_type: args[0]})
    if bans is None:
        client.send_ooc('No ban found for this ID.')
    else:
        msg = f'Bans for {args[0]}'
        for ban in bans:
            msg += f'\nBan ID: {ban.ban_id}\n'
            msg += 'Affected IPIDs: ' + \
                ', '.join([str(ipid) for ipid in ban.ipids]) + '\n'
            msg += 'Affected HDIDs: ' + ', '.join(ban.hdids) + '\n'
            msg += f'Reason: "{ban.reason}"\n'
            msg += f'Unbanned: {bool(ban.unbanned)}\n'
            msg += f'Banned by: {ban.banned_by_name} ({ban.banned_by})\n'

            ban_date = arrow.get(ban.ban_date)
            msg += f'Banned on: {ban_date.format()} ({ban_date.humanize()})\n'
            if ban.unban_date is not None:
                unban_date = arrow.get(ban.unban_date)
                msg += f'Unban date: {unban_date.format()} ({unban_date.humanize()})'
            else:
                msg += 'Unban date: N/A'
        client.send_ooc(msg)
