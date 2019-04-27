from server import logger
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError

__all__ = [
    'ooc_cmd_disemvowel',
    'ooc_cmd_undisemvowel',
    'ooc_cmd_shake',
    'ooc_cmd_unshake'
]


def ooc_cmd_disemvowel(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must specify a target. Use /disemvowel <id>.')
    if targets:
        for c in targets:
            logger.log_mod(f'Disemvowelling {c.ip}.', client)
            c.disemvowel = True
        client.send_ooc(f'Disemvowelled {len(targets)} existing client(s).')
    else:
        client.send_ooc('No targets found.')


def ooc_cmd_undisemvowel(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError(
            'You must specify a target. Use /undisemvowel <id>.')
    if targets:
        for c in targets:
            logger.log_mod(f'Undisemvowelling {c.ip}.', client)
            c.disemvowel = False
        client.send_ooc(f'Undisemvowelled {len(targets)} existing client(s).')
    else:
        client.send_ooc('No targets found.')


def ooc_cmd_shake(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must specify a target. Use /shake <id>.')
    if targets:
        for c in targets:
            logger.log_mod(f'Shaking {c.ip}.', client)
            c.shaken = True
        client.send_ooc(f'Shook {len(targets)} existing client(s).')
    else:
        client.send_ooc('No targets found.')


def ooc_cmd_unshake(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must specify a target. Use /unshake <id>.')
    if targets:
        for c in targets:
            logger.log_mod(f'Unshaking {c.ip}.', client)
            c.shaken = False
        client.send_ooc(f'Unshook {len(targets)} existing client(s).')
    else:
        client.send_ooc('No targets found.')
