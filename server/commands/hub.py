from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError, AreaError

from . import mod_only

__all__ = [
    'ooc_cmd_toggle',
]


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


@mod_only(area_owners=True)
def ooc_cmd_toggle(client, arg):
    """
    Toggle a preference on/off for a hub.
    Usage:  /toggle - display list of prefs
            /toggle <pref> - switch pref on/off
            /toggle <pref> <on/true|off/false> - set pref to on or off
    """
    gm_allowed = ['showname_changes_allowed', 'shouts_allowed',
                'noninterrupting_pres', 'iniswap_allowed',
                'blankposting_allowed']
    
    if len(arg) == 0:
        bools = [x for x in client.hub.__dict__.keys() if type(getattr(client.hub, x)) is bool]
        msg = 'Possible preferences:'
        for attri in bools:
            mod = '[mod]' if not (attri in gm_allowed) else ''
            msg += f'\n{attri} {mod}'
        client.send_ooc(msg)
        return

    args = arg.split()
    if len(args) > 2:
        raise ArgumentError("Usage: /toggle | /toggle <pref> | /toggle <pref> <on|off>")

    try:
        attri = getattr(client.hub, args[0].lower())
        if not (type(attri) is bool):
            raise ArgumentError("Preference is not a boolean.")
        if not client.is_mod and not (attri in gm_allowed):
            raise ClientError("You need to be a mod to modify this preference.")
        tog = not attri
        if len(args) > 1:
            if args[1].lower() in ('on', 'true'):
                tog = True
            elif args[1].lower() in ('off', 'false'):
                tog = False
            else:
                raise ArgumentError("Invalid argument: {}".format(arg))
        client.send_ooc(f'Setting preference {args[0]} to {tog}...')
        setattr(client.hub, args[0], tog)
        database.log_room(args[0], client, client.area, message=f'Setting preference to {tog}')
    except:
        client.send_ooc('Variable doesn\'t exist!')
