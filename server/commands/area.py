from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError, AreaError

import time
import math

from . import mod_only

__all__ = [
    'ooc_cmd_bg',
    'ooc_cmd_bglock',
    'ooc_cmd_area',
    'ooc_cmd_getarea',
    'ooc_cmd_getareas',
    'ooc_cmd_lock',
    'ooc_cmd_unlock',
    'ooc_cmd_area_kick',
    'ooc_cmd_getafk'
]


def ooc_cmd_bg(client, arg):
    """
    Set the background of a room.
    Usage: /bg <background>
    """
    if client.hub.status.lower().startswith('rp-strict') and not client.is_mod and not client.is_gm:
        raise AreaError(
            'Hub is {} - only the GM or mods can change /bg.'.format(client.hub.status))
    if len(arg) == 0:
        raise ArgumentError('You must specify a name. Use /bg <background>.')
    if not client.is_mod and client.area.bg_lock == True:
        raise AreaError("This area's background is locked")
    try:
        client.area.change_background(arg, client.is_mod)
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
    if client.area.bg_lock == True:
        client.area.bg_lock = False
    else:
        client.area.bg_lock = True
    client.area.broadcast_ooc(
        f'{client.char_name} [{client.id}] has set the background lock to {client.area.bg_lock}.')
    database.log_room('bglock', client, client.area, message=client.area.bg_lock)


def ooc_cmd_area(client, arg):
    """
    List areas, or go to another area/room.
    Usage: /area [id]
    """
    if client.blinded:
        raise ClientError('You can\'t use /area while blinded!')

    args = arg.split()
    if len(args) == 0:
        client.send_area_list()
        return

    allowed = client.is_gm or client.is_mod or client.char_name == "Spectator"
    rpmode = not allowed and client.hub.rpmode
    try:
        area = client.hub.get_area_by_id_or_name(' '.join(args[0:]))

        if area == client.area:
            raise ClientError("You are already in specified area!")

        if not allowed:
            if area != client.area and rpmode and len(client.area.accessible) > 0 and area.id not in client.area.accessible:
                raise AreaError(
                    'Area ID not accessible from your current area!')
            if client.area.is_locked and client.area.locked_by != client:
                client.area.broadcast_ooc("[{}] {} tried to leave to [{}] {} but it is locked!".format(
                    client.id, client.get_char_name(), area.id, area.name))
                return
            if area.is_locked:
                area.broadcast_ooc("Someone tried to enter from [{}] {} but it is locked!".format(client.area.id, client.area.name))
                raise ClientError(
                    "That area is locked and anyone inside was alerted someone tried to enter!")
            
            if area.max_players > 0:
                players = len([x for x in area.clients if (not x.is_gm and not x.is_mod and x.get_char_name() != "Spectator")])
                if players >= area.max_players:
                    area.broadcast_ooc("Someone tried to enter from [{}] {} but it is full!".format(client.area.id, client.area.name))
                    raise ClientError("That area is full and anyone inside was alerted someone tried to enter!")
            elif area.max_players == 0:
                raise ClientError("That area cannot be accessed by normal means!")

            delay = client.area.time_until_move(client)
            if delay > 0:
                sec = int(math.ceil(delay * 0.001))
                raise ClientError("You need to wait {} seconds until you can move again.".format(sec))

            client.last_move_time = round(time.time() * 1000.0)

        #Changing area of your own accord should stop following as well
        if client.following != None:
            try:
                c = client.server.client_manager.get_targets(
                    client, TargetType.ID, int(client.following), False)[0]
                client.send_ooc(
                    'You are no longer following [{}] {}.'.format(c.id, c.get_char_name(True)))
                client.following = None
            except:
                client.following = None

        client.change_area(area)
    except ValueError:
        raise ArgumentError('Area ID must be a number.')
    except (AreaError, ClientError):
        raise


def ooc_cmd_getarea(client, arg):
    """
    Show information about the current area.
    Usage: /getarea
    """
    if client.blinded:
        raise ArgumentError('You are blinded - you cannot use this command!')
    allowed = client.is_gm or client.is_mod or client.get_char_name() == "Spectator"
    ID = client.area.id
    if len(arg) > 0:
        if not allowed:
            raise ClientError('You must be authorized to /getarea <id>.')
        ID = int(arg)
    client.send_area_info(ID, client.hub.rpmode and not allowed)


def ooc_cmd_getareas(client, arg):
    """
    Show information about all areas.
    Usage: /getareas
    """
    if client.blinded:
        raise ArgumentError('You are blinded - you cannot use this command!')
    allowed = client.is_gm or client.is_mod or client.get_char_name() == "Spectator"
    if client.hub.rpmode and not allowed:
        raise AreaError('Hub is {} - /getareas functionality disabled.'.format(client.hub.status))
    client.send_area_info(-1)


def ooc_cmd_lock(client, arg):
    """
    Prevent users from joining the current or target area(s).
    Usage:  /lock
            /lock <id1> <id2>
    """
    args = []
    if arg == 'all':
        for area in client.hub.areas:
            args.append(area.id)
    elif len(arg) == 0:
        args = [client.area.id]
    else:
        try:
            args = [int(s) for s in str(arg).split(' ')]
        except:
            raise ArgumentError('Invalid argument!')

    allowed = client.is_gm or client.is_mod
    if not allowed:
        args = [args[0]] #only one singular number so client can't lock a bunch of areas in one fell swoop

    i = 0
    for area in client.hub.areas:
        if area.id in args:
            if not area.locking_allowed:
                client.send_host_message(
                    f'Area locking is disabled in area {area.id}.')
                continue
            if not allowed:
                if not (area.id in client.assigned_areas):
                    raise ClientError('Only GM or mods can lock this area.')
                if not (client.area == area) and len(client.area.accessible) > 0 and not (area.id in client.area.accessible):
                    raise ClientError('That area is inaccessible from your current area.')
            if area.is_locked:
                client.send_host_message(
                    f'Area {area.id} is already locked.')
                continue
            
            area.lock()
            i += 1
    client.send_host_message(f'Locked {i} areas.')


def ooc_cmd_unlock(client, arg):
    """
    Allow anyone to freely join the current area.
    Usage:  /unlock
            /unlock <id1> <id2>
    """
    args = []
    if arg == 'all':
        for area in client.hub.areas:
            args.append(area.id)
    elif len(arg) == 0:
        args = [client.area.id]
    else:
        try:
            args = [int(s) for s in str(arg).split(' ')]
        except:
            raise ArgumentError('Invalid argument!')

    allowed = client.is_gm or client.is_mod
    if not allowed:
        args = [args[0]] #only one singular number so client can't lock a bunch of areas in one fell swoop

    i = 0
    for area in client.hub.areas:
        if area.id in args:
            if not area.locking_allowed:
                client.send_ooc(
                    f'Area locking is disabled in area {area.id}.')
                continue
            if not allowed:
                if not (area.id in client.assigned_areas):
                    raise ClientError('Only GM or mods can lock this area.')
                if not (client.area == area) and len(client.area.accessible) > 0 and not (area.id in client.area.accessible):
                    raise ClientError('That area is inaccessible from your current area.')
            if not area.is_locked:
                continue
            
            area.unlock()
            i += 1
    client.send_ooc(f'Unlocked {i} areas.')


def ooc_cmd_lockin(client, arg):
    """
    Lock current area until you leave it.
    Usage: /lockin
    """
    if client.hub.status.lower().startswith('rp-strict') and not client.is_mod and not client.is_gm:
        raise AreaError(
            'Hub is {} - /lockin is disabled.'.format(client.hub.status))

    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")

    if not client.area.locking_allowed:
        raise AreaError(
            'Area locking is disabled in area {}.'.format(client.area.id))
    if client.area.is_locked:
        if client.area.locked_by != client:
            raise AreaError('You are unable to unlock this area!')
        client.area.unlock()
    else:
        client.area.lock(client)
    client.send_host_message('This area will be unlocked when you leave.')


@mod_only(area_owners=True)
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
    # arg = arg.split(' ')
    # if arg[0] == 'afk':
    #     trgtype = TargetType.AFK
    #     argi = arg[0]
    # else:
    #     trgtype = TargetType.ID
    #     argi = int(arg[0])
    # targets = client.server.client_manager.get_targets(client, trgtype,
    #                                                    argi, False)
    arg = arg.split()
    targets = client.server.client_manager.get_targets(client, TargetType.ID, int(arg[0]), False)
    output = [0, 0]
    if targets:
        try:
            for c in targets:
                if len(arg) == 1:
                    area = client.hub.get_area_by_id(0)
                else:
                    try:
                        if len(arg) > 2 and client.is_mod:
                            hub = client.server.hub_manager.get_hub_by_id(int(arg[2]))
                            output[1] = arg[2]
                        else:
                            hub = client.hub
                            output[1] = client.hub.id
                        area = hub.get_area_by_id(int(arg[1]))
                        output[0] = arg[1]
                    except AreaError:
                        raise
                client.send_ooc(
                    "Attempting to kick {} to area {}.".format(
                        c.char_name, output))
                c.change_area(area, True)
                c.send_ooc(
                    f"You were kicked from the area to area {output}.")
                database.log_room('area_kick', client, client.area, target=c, message=output)
        except AreaError:
            raise
        except ClientError:
            raise
    else:
        client.send_ooc("No targets found.")


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