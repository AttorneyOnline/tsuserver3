from server import logger
from server.constants import TargetType
from server.exceptions import ClientError, ServerError, ArgumentError

__all__ = [
    'ooc_cmd_motd',
    'ooc_cmd_help',
    'ooc_cmd_kick',
    'ooc_cmd_ban',
    'ooc_cmd_unban',
    'ooc_cmd_mute',
    'ooc_cmd_unmute',
    'ooc_cmd_login',
    'ooc_cmd_refresh',
    'ooc_cmd_online',
    'ooc_cmd_mods',
    'ooc_cmd_unmod',
    'ooc_cmd_ooc_mute',
    'ooc_cmd_ooc_unmute'
]


def ooc_cmd_motd(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.send_motd()


def ooc_cmd_help(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    help_url = 'https://github.com/AttorneyOnline/tsuserver3'
    help_msg = f'The commands available on this server can be found here: {help_url}'
    client.send_ooc(help_msg)


def ooc_cmd_kick(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError(
            'You must specify a target. Use /kick <ipid> [reason]')
    elif arg[0] == '*area':
        targets = client.area.clients
    elif arg[0] == '*':
        targets = client.server.client_manager.clients
    else:
        targets = None

    args = list(arg.split(' '))
    if targets is not None:
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
            logger.log_mod(
                'Kicked {} [{}]({}) (reason: {}).'.format(
                    c.char_name, c.id, c.ipid, reason), client)
            client.send_ooc("{} was kicked.".format(
                c.char_name))
            c.send_command('KK', reason)
            c.disconnect()
    else:
        client.send_ooc(
            f'No targets with the IPID {ipid} were found.')


def ooc_cmd_ban(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) <= 1:
        raise ArgumentError(
            'You must specify a target and reason. Use /ban <ipid> <reason>')
    args = list(arg.split(' '))

    raw_ipid = args[0]
    reason = ' '.join(args[1:])

    try:
        ipid = int(raw_ipid)
    except:
        raise ClientError(f'{raw_ipid} does not look like a valid IPID.')
    try:
        client.server.ban_manager.add_ban(ipid, reason)
    except ServerError:
        raise
    if ipid != None:
        targets = client.server.client_manager.get_targets(
            client, TargetType.IPID, ipid, False)
        if targets:
            for c in targets:
                c.send_command('KB', reason)
                c.disconnect()
            client.send_ooc(f'{len(targets)} clients were kicked.')
        client.send_ooc(f'{ipid} was banned.')
        logger.log_mod(f'Banned {ipid} (reason: {reason}).', client)


def ooc_cmd_unban(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError(
            'You must specify a target. Use /unban <ipid> <ipid> ...')
    args = list(arg.split(' '))
    client.send_ooc(f'Attempting to unban {len(args)} IPIDs.')
    for raw_ipid in args:
        try:
            client.server.ban_manager.remove_ban(int(raw_ipid))
        except:
            raise ClientError(f'{raw_ipid} does not look like a valid IPID.')
        logger.log_mod(f'Unbanned {raw_ipid}.', client)
        client.send_ooc(f'Unbanned {raw_ipid}')


def ooc_cmd_mute(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
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
                    logger.log_mod(
                        'Muted {} [{}]({}).'.format(c.char_name, c.id,
                                                    c.ipid), client)
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


def ooc_cmd_unmute(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
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
                    logger.log_mod(
                        'Unmuted {} [{}]({}).'.format(c.char_name, c.id,
                                                      c.ipid), client)
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
    if len(arg) == 0:
        raise ArgumentError('You must specify the password.')
    login_name = None
    try:
        login_name = client.auth_mod(arg)
    except ClientError:
        logger.log_server('Invalid login attempt.', client)
        raise
    if client.area.evidence_mod == 'HiddenCM':
        client.area.broadcast_evidence_list()
    client.send_ooc('Logged in as a moderator.')
    logger.log_mod(f'Logged in as moderator ({login_name}).', client)


def ooc_cmd_refresh(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) > 0:
        raise ClientError('This command does not take in any arguments!')
    else:
        try:
            client.server.refresh()
            logger.log_mod('Reloaded server.', client)
            client.send_ooc('You have reloaded the server.')
        except ServerError:
            raise


def ooc_cmd_online(client, _):
    client.send_player_count()


def ooc_cmd_mods(client, arg):
    client.send_area_info(-1, True)


def ooc_cmd_unmod(client, arg):
    client.is_mod = False
    client.mod_profile_name = None
    if client.area.evidence_mod == 'HiddenCM':
        client.area.broadcast_evidence_list()
    client.send_ooc('you\'re not a mod now')


def ooc_cmd_ooc_mute(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
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
    client.send_ooc('Muted {} existing client(s).'.format(
        len(targets)))


def ooc_cmd_ooc_unmute(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError(
            'You must specify a target. Use /ooc_unmute <OOC-name>.')
    targets = client.server.client_manager.get_ooc_muted_clients()
    if not targets:
        raise ArgumentError('Targets not found. Use /ooc_unmute <OOC-name>.')
    for target in targets:
        target.is_ooc_muted = False
    client.send_ooc('Unmuted {} existing client(s).'.format(
        len(targets)))
