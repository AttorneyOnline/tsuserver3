from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError, AreaError

from . import mod_only

__all__ = [
    'ooc_cmd_bg',
    'ooc_cmd_bglock',
    'ooc_cmd_allow_iniswap',
    'ooc_cmd_allow_blankposting',
    'ooc_cmd_force_nonint_pres',
    'ooc_cmd_status',
    'ooc_cmd_area',
    'ooc_cmd_getarea',
    'ooc_cmd_getareas',
    'ooc_cmd_area_lock',
    'ooc_cmd_area_spectate',
    'ooc_cmd_area_unlock',
    'ooc_cmd_invite',
    'ooc_cmd_uninvite',
    'ooc_cmd_area_kick',
    'ooc_cmd_getafk'
]


def ooc_cmd_bg(client, arg):
    """
    Set the background of a room.
    Usage: /bg <background>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a name. Use /bg <background>.')
    if not client.is_mod and client.area.bg_lock == "true":
        raise AreaError("This area's background is locked!")
    elif not client.area.can_send_message(client):
        raise AreaError("You are not permitted to change the background in this area!")
    try:
        client.area.change_background(arg)
    except AreaError:
        raise
    client.area.broadcast_ooc(
        f'{client.char_name} changed the background to {arg}.')
    database.log_room('bg', client, client.area, message=arg)


@mod_only()
def ooc_cmd_bglock(client, arg):
    """
    Toggle whether or not non-moderators are allowed to change
    the background of a room.
    Usage: /bglock
    """
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    # XXX: Okay, what?
    if client.area.bg_lock == "true":
        client.area.bg_lock = "false"
    else:
        client.area.bg_lock = "true"
    client.area.broadcast_ooc(
        '{} [{}] has set the background lock to {}.'.format(
            client.char_name, client.id, client.area.bg_lock))
    database.log_room('bglock', client, client.area, message=client.area.bg_lock)


@mod_only()
def ooc_cmd_allow_iniswap(client, arg):
    """
    Toggle whether or not users are allowed to swap INI files in character
    folders to allow playing as a character other than the one chosen in
    the character list.
    Usage: /allow_iniswap
    """
    client.area.iniswap_allowed = not client.area.iniswap_allowed
    answer = 'allowed' if client.area.iniswap_allowed else 'forbidden'
    client.send_ooc(f'Iniswap is {answer}.')
    database.log_room('iniswap', client, client.area, message=client.area.iniswap_allowed)


@mod_only(area_owners=True)
def ooc_cmd_allow_blankposting(client, arg):
    """
    Toggle whether or not in-character messages purely consisting of spaces
    are allowed.
    Usage: /allow_blankposting
    """
    client.area.blankposting_allowed = not client.area.blankposting_allowed
    answer = 'allowed' if client.area.blankposting_allowed else 'forbidden'
    client.area.broadcast_ooc(
        '{} [{}] has set blankposting in the area to {}.'.format(
            client.char_name, client.id, answer))
    database.log_room('blankposting', client, client.area, message=client.area.blankposting_allowed)


@mod_only(area_owners=True)
def ooc_cmd_force_nonint_pres(client, arg):
    """
    Toggle whether or not all pre-animations lack a delay before a
    character begins speaking.
    Usage: /force_nonint_pres
    """
    client.area.non_int_pres_only = not client.area.non_int_pres_only
    answer = 'non-interrupting only' if client.area.non_int_pres_only else 'non-interrupting or interrupting as you choose'
    client.area.broadcast_ooc(
        '{} [{}] has set pres in the area to be {}.'.format(
            client.char_name, client.id, answer))
    database.log_room('force_nonint_pres', client, client.area, message=client.area.non_int_pres_only)


def ooc_cmd_status(client, arg):
    """
    Show or modify the current status of a room.
    Usage: /status <idle|rp|casing|looking-for-players|lfp|recess|gaming>
    """
    if len(arg) == 0:
        client.send_ooc(f'Current status: {client.area.status}')
    else:
        try:
            client.area.change_status(arg)
            client.area.broadcast_ooc('{} changed status to {}.'.format(
                client.char_name, client.area.status))
            database.log_room('status', client, client.area, message=arg)
        except AreaError:
            raise


def ooc_cmd_area(client, arg):
    """
    List areas, or go to another area/room.
    Usage: /area [id] or /area [name]
    """
    args = arg.split()
    if len(args) == 0:
        client.send_area_list()
        return

    try:
        area = client.server.area_manager.get_area_by_id(int(args[0]))
        client.change_area(area)
    except:
        try:
            area = client.server.area_manager.get_area_by_name(arg)
            client.change_area(area)
        except ValueError:
            raise ArgumentError('Area ID must be a name or a number.')
        except (AreaError, ClientError):
            raise


def ooc_cmd_getarea(client, arg):
    """
    Show information about the current area.
    Usage: /getarea
    """
    client.send_area_info(client.area.id, False)


def ooc_cmd_getareas(client, arg):
    """
    Show information about all areas.
    Usage: /getareas
    """
    client.send_area_info(-1, False)


def ooc_cmd_getafk(client, arg):
    """
    Show currently AFK-ing players in the current area or in all areas.
    Usage: /getafk [all]
    """
    if arg == 'all':
        arg = -1
    elif len(arg) == 0:
        arg = client.area.id
    else:
        raise ArgumentError('There is only one optional argument [all].')
    client.send_area_info(arg, False, afk_check=True)


def ooc_cmd_area_lock(client, arg):
    """
    Prevent users from joining the current area.
    Usage: /area_lock
    """
    if not client.area.locking_allowed:
        client.send_ooc('Area locking is disabled in this area.')
    elif client.area.is_locked == client.area.Locked.LOCKED:
        client.send_ooc('Area is already locked.')
    elif client in client.area.owners:
        client.area.lock()
    else:
        raise ClientError('Only CM can lock the area.')


def ooc_cmd_area_spectate(client, arg):
    """
    Allow users to join the current area, but only as spectators.
    Usage: /area_spectate
    """
    if not client.area.locking_allowed:
        client.send_ooc('Area locking is disabled in this area.')
    elif client.area.is_locked == client.area.Locked.SPECTATABLE:
        client.send_ooc('Area is already spectatable.')
    elif client in client.area.owners:
        client.area.spectator()
    else:
        raise ClientError('Only CM can make the area spectatable.')


def ooc_cmd_area_unlock(client, arg):
    """
    Allow anyone to freely join the current area.
    Usage: /area_unlock
    """
    if client.area.is_locked == client.area.Locked.FREE:
        raise ClientError('Area is already unlocked.')
    elif not client in client.area.owners:
        raise ClientError('Only CM can unlock area.')
    client.area.unlock()
    client.send_ooc('Area is unlocked.')


@mod_only(area_owners=True)
def ooc_cmd_invite(client, arg):
    """
    Allow a particular user to join a locked or spectator-only area.
    Usage: /invite <id>
    """
    if not arg:
        raise ClientError('You must specify a target. Use /invite <id>')
    elif client.area.is_locked == client.area.Locked.FREE:
        raise ClientError('Area isn\'t locked.')
    try:
        c = client.server.client_manager.get_targets(client, TargetType.ID,
                                                     int(arg), False)[0]
        client.area.invite_list[c.id] = None
        client.send_ooc('{} is invited to your area.'.format(
            c.char_name))
        c.send_ooc(
            f'You were invited and given access to {client.area.name}.')
        database.log_room('invite', client, client.area, target=c)
    except:
        raise ClientError('You must specify a target. Use /invite <id>')


@mod_only(area_owners=True)
def ooc_cmd_uninvite(client, arg):
    """
    Revoke an invitation for a particular user.
    Usage: /uninvite <id>
    """
    if client.area.is_locked == client.area.Locked.FREE:
        raise ClientError('Area isn\'t locked.')
    elif not arg:
        raise ClientError('You must specify a target. Use /uninvite <id>')
    arg = arg.split(' ')
    targets = client.server.client_manager.get_targets(client, TargetType.ID,
                                                       int(arg[0]), True)
    if targets:
        try:
            for c in targets:
                client.send_ooc(
                    "You have removed {} from the whitelist.".format(
                        c.char_name))
                c.send_ooc(
                    "You were removed from the area whitelist.")
                database.log_room('uninvite', client, client.area, target=c)
                if client.area.is_locked != client.area.Locked.FREE:
                    client.area.invite_list.pop(c.id)
        except AreaError:
            raise
        except ClientError:
            raise
    else:
        client.send_ooc("No targets found.")


@mod_only()
def ooc_cmd_area_kick(client, arg):
    """
    Remove a user from the current area and move them to another area.
    Usage: /area_kick <id> [destination]
    """
    if client.area.is_locked == client.area.Locked.FREE:
        raise ClientError('Area isn\'t locked.')
    if not arg:
        raise ClientError(
            'You must specify a target. Use /area_kick <id> [destination #]')
    arg = arg.split(' ')
    if arg[0] == 'afk':
        trgtype = TargetType.AFK
        argi = arg[0]
    else:
        trgtype = TargetType.ID
        argi = int(arg[0])
    targets = client.server.client_manager.get_targets(client, trgtype,
                                                       argi, False)
    if targets:
        try:
            for c in targets:
                if len(arg) == 1:
                    area = client.server.area_manager.get_area_by_id(int(0))
                    output = 0
                else:
                    try:
                        area = client.server.area_manager.get_area_by_id(
                            int(arg[1]))
                        output = arg[1]
                    except AreaError:
                        raise
                client.send_ooc(
                    "Attempting to kick {} to area {}.".format(
                        c.char_name, output))
                c.change_area(area)
                c.send_ooc(
                    f"You were kicked from the area to area {output}.")
                database.log_room('area_kick', client, client.area, target=c, message=output)
                if client.area.is_locked != client.area.Locked.FREE:
                    client.area.invite_list.pop(c.id)
        except AreaError:
            raise
        except ClientError:
            raise
    else:
        client.send_ooc("No targets found.")
