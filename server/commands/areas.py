import os

from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError, AreaError

from . import mod_only

__all__ = [
    'ooc_cmd_bg',
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
    'ooc_cmd_getafk',
    # Hub system [TO BE MOVED]
    'ooc_cmd_save_hub',
    'ooc_cmd_load_hub',
    'ooc_cmd_list_hubs',
    # Area Creation system
    'ooc_cmd_area_create',
    'ooc_cmd_area_remove',
    'ooc_cmd_area_rename',
    'ooc_cmd_area_swap',
    'ooc_cmd_area_pref',
    # Area links system
    'ooc_cmd_area_link',
    'ooc_cmd_area_unlink',
    'ooc_cmd_area_links',
    'ooc_cmd_link_lock',
    'ooc_cmd_link_unlock',
    'ooc_cmd_link_hide',
    'ooc_cmd_link_unhide',
    'ooc_cmd_link_pos',
    # pos stuff
    'ooc_cmd_pos_lock',
    'ooc_cmd_pos_lock_clear',
    # hehehe
    'ooc_cmd_peek',
    'ooc_cmd_area_move_delay',
    'ooc_cmd_hub_move_delay',
]


def ooc_cmd_bg(client, arg):
    """
    Set the background of a room.
    Usage: /bg <background>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify a name. Use /bg <background>.')
    if not client.is_mod and client.area.bg_lock == "true":
        raise AreaError("This area's background is locked")
    try:
        client.area.change_background(arg)
    except AreaError:
        raise
    client.area.broadcast_ooc(
        f'{client.char_name} changed the background to {arg}.')
    database.log_room('bg', client, client.area, message=arg)


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
        for area in client.server.area_manager.areas:
            if (args[0].isdigit() and area.id == int(args[0])) or area.abbreviation.lower() == args[0].lower() or area.name.lower() == arg.lower():
                client.change_area(area)
                return
        raise AreaError('Targeted area not found!')
    except ValueError:
        raise ArgumentError('Area ID must be a name, abbreviation or a number.')
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


@mod_only(area_owners=True)
def ooc_cmd_area_lock(client, arg):
    """
    Prevent users from joining the current area.
    Usage: /area_lock
    """
    if not client.area.locking_allowed and not client.is_mod:
        client.send_ooc('Area locking is disabled in this area.')
    elif client.area.is_locked == client.area.Locked.LOCKED:
        client.send_ooc('Area is already locked.')
    client.area.lock()


@mod_only(area_owners=True)
def ooc_cmd_area_spectate(client, arg):
    """
    Allow users to join the current area, but only as spectators.
    Usage: /area_spectate
    """
    if not client.area.locking_allowed and not client.is_mod:
        client.send_ooc('Area locking is disabled in this area.')
    elif client.area.is_locked == client.area.Locked.SPECTATABLE:
        client.send_ooc('Area is already spectatable.')
    client.area.spectator()


@mod_only(area_owners=True)
def ooc_cmd_area_unlock(client, arg):
    """
    Allow anyone to freely join the current area.
    Usage: /area_unlock
    """
    if client.area.is_locked == client.area.Locked.FREE:
        raise ClientError('Area is already unlocked.')
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


@mod_only()
def ooc_cmd_save_hub(client, arg):
    """
    Save the current Hub in the server's storage/hubs/<name>.yaml file.
    Usage: /save_hub <name>
    """
    if len(arg) < 3:
        client.send_ooc("Filename must be at least 3 symbols long!")
        return

    try:
        path = 'storage/hubs'
        num_files = len([f for f in os.listdir(
            path) if os.path.isfile(os.path.join(path, f))])
        if (num_files >= 1000): #yikes
            raise AreaError('Server storage full! Please contact the server host to resolve this issue.')
        arg = f'{path}/{arg}.yaml'
        client.server.area_manager.save_areas(arg)
        client.send_ooc(f'Saving as {arg}...')
    except AreaError:
        raise


@mod_only()
def ooc_cmd_load_hub(client, arg):
    """
    Load Hub data from the server's storage/hubs/<name>.yaml file.
    Usage: /load_hub <name>
    """
    try:
        path = 'storage/hubs'
        arg = f'{path}/{arg}.yaml'
        client.server.area_manager.load_areas(arg)
        client.server.area_manager.send_arup_players()
        client.server.area_manager.send_arup_status()
        client.server.area_manager.send_arup_cms()
        client.server.area_manager.send_arup_lock()
        client.send_ooc(f'Loading {arg}...')
    except AreaError:
        raise
    


@mod_only()
def ooc_cmd_list_hubs(client, arg):
    """
    Show all the available hubs for loading in the storage/hubs/ folder.
    Usage: /list_hubs
    """
    text = 'Available hubs:'
    for F in os.listdir('storage/hubs/'):
        if F.lower().endswith('.yaml'):
            text += '\n- {}'.format(F[:-5])

    client.send_ooc(text)


@mod_only()
def ooc_cmd_area_create(client, arg):
    """
    Create a new area.
    Usage: /area_create [name]
    """
    area = client.server.area_manager.create_area()
    if arg != '':
        area.name = arg
    client.server.area_manager.broadcast_area_list()
    client.send_ooc(f'New area created! ({area.name})')


@mod_only()
def ooc_cmd_area_remove(client, arg):
    """
    Remove specified area by Area ID.
    Usage: /area_remove <aid>
    """
    args = arg.split()

    if len(args) == 1:
        try:
            area = client.server.area_manager.get_area_by_id(int(args[0]))
            name = area.name
            client.server.area_manager.remove_area(area)
            client.server.area_manager.broadcast_area_list()
            client.send_ooc(f'Area {name} removed!')
        except ValueError:
            raise ArgumentError('Area ID must be a number.')
        except (AreaError, ClientError):
            raise
    else:
        raise ArgumentError('Invalid number of arguments. Use /area_remove <aid>.')

@mod_only()
def ooc_cmd_area_rename(client, arg):
    """
    Rename area you are currently in to <name>.
    Usage: /area_rename <name>
    """
    if arg != '':
        try:
            client.area.rename_area(arg)
        except ValueError:
            raise ArgumentError('Area ID must be a number.')
        except (AreaError, ClientError):
            raise
    else:
        raise ArgumentError('Invalid number of arguments. Use /area_rename <name>.')

@mod_only()
def ooc_cmd_area_swap(client, arg):
    """
    Swap areas by Area IDs <aid1> and <aid2>.
    Usage: /area_rename <aid1> <aid2>
    """
    args = arg.split()
    if len(args) != 2:
        raise ClientError("You must specify 2 numbers.")
    try:
        area1 = client.server.area_manager.get_area_by_id(int(args[0]))
        area2 = client.server.area_manager.get_area_by_id(int(args[1]))
        client.server.area_manager.swap_area(area1, area2)
        client.send_ooc(f'Area {area1.name} has been swapped with Area {area2.name}!')
    except ValueError:
        raise ArgumentError('Area IDs must be a number.')
    except (AreaError, ClientError):
        raise

@mod_only(area_owners=True)
def ooc_cmd_area_pref(client, arg):
    """
    Toggle a preference on/off for an area.
    Usage:  /area_pref - display list of prefs
            /area_pref <pref> - toggle pref on/off
            /area_pref <pref> <on/true|off/false> - set pref to on or off
    """
    cm_allowed = [
        # 'bg_lock',
        'locking_allowed',
        'iniswap_allowed',
        'showname_changes_allowed',
        'shouts_allowed',
        'jukebox',
        'non_int_pres_only',
        'blankposting_allowed',
    ]

    if len(arg) == 0:
        msg = 'Current preferences:'
        for attri in client.area.__dict__.keys():
            value = getattr(client.area, attri)
            if not(type(value) is bool):
                continue
            mod = '[mod] ' if not (attri in cm_allowed) else ''
            msg += f'\n* {mod}{attri}={value}'
        client.send_ooc(msg)
        return

    args = arg.split()
    if len(args) > 2:
        raise ArgumentError("Usage: /area_pref | /area_pref <pref> | /area_pref <pref> <on|off>")

    try:
        attri = getattr(client.area, args[0].lower())
        if not (type(attri) is bool):
            raise ArgumentError("Preference is not a boolean.")
        if not client.is_mod and not (args[0] in cm_allowed):
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
        setattr(client.area, args[0], tog)
        database.log_room(args[0], client, client.area, message=f'Setting preference to {tog}')
    except ValueError:
        raise ArgumentError('Invalid input.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_area_link(client, arg):
    """
    Set up a one-way link from your current area with a targeted area(s).
    Usage:  /area_link <aid> [aid(s)]
    """
    args = arg.split()
    if len(args) <= 0:
        ooc_cmd_area_links(client, arg)
        return
    try:
        links = []
        for aid in args:
            try:
                target_id = client.server.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)

            client.area.link(target_id)
            links.append(target_id)
        links = ', '.join(str(l) for l in links)
        client.send_ooc(f'Area {client.area.name} has been linked with {links}.')
    except ValueError:
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise


def ooc_cmd_area_links(client, arg):
    """
    Display this area's information about area links.
    Usage:  /area_links
    """
    links = ''
    for key, value in client.area.links.items():
        hidden = ''
        if value["hidden"] == True:
            # Can't see hidden links
            if not client.is_mod and not client in client.area.owners:
                continue
            hidden = ' [H]'

        try:
            area_name = f' - "{client.server.area_manager.get_area_by_id(int(key)).name}"'
        except:
            area_name = ''

        locked = ''
        if value["locked"] == True:
            locked = ' [L]'

        target_pos = value["target_pos"]
        if target_pos != '':
            target_pos = f', pos: {target_pos}'
        links += f'{key}{area_name}{locked}{hidden}{target_pos}\n'

    client.send_ooc(f'Current area links are: \n{links}')


@mod_only(area_owners=True)
def ooc_cmd_area_unlink(client, arg):
    """
    Remove a one-way link from your current area with a targeted area(s).
    Usage:  /area_unlink <aid> [aid(s)]
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /area_unlink <aid>')
    try:
        links = []
        for aid in args:
            try:
                target_id = client.server.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)

            try:
                client.area.unlink(target_id)
                links.append(target_id)
            except:
                continue
        links = ', '.join(str(l) for l in links)
        client.send_ooc(f'Area {client.area.name} has been unlinked with {links}.')
    except ValueError:
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_link_lock(client, arg):
    """
    Lock the path leading to target area(s).
    Usage:  /link_lock <aid> [aid(s)]
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /link_lock <aid>')
    try:
        links = []
        for aid in args:
            try:
                target_id = client.server.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)

            client.area.links[str(target_id)]["locked"] = True
            links.append(target_id)
        links = ', '.join(str(l) for l in links)
        client.send_ooc(f'Area {client.area.name} links {links} locked.')
    except (ValueError, KeyError):
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_link_unlock(client, arg):
    """
    Unlock the path leading to target area(s).
    Usage:  /link_unlock <aid> [aid(s)]
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /link_unlock <aid>')
    try:
        links = []
        for aid in args:
            try:
                target_id = client.server.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)

            client.area.links[str(target_id)]["locked"] = False
            links.append(target_id)
        links = ', '.join(str(l) for l in links)
        client.send_ooc(f'Area {client.area.name} links {links} unlocked.')
    except (ValueError, KeyError):
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_link_hide(client, arg):
    """
    Hide the path leading to target area(s).
    Usage:  /link_hide <aid> [aid(s)]
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /link_hide <aid>')
    try:
        links = []
        for aid in args:
            try:
                target_id = client.server.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)

            client.area.links[str(target_id)]["hidden"] = True
            links.append(target_id)
        links = ', '.join(str(l) for l in links)
        client.send_ooc(f'Area {client.area.name} links {links} hidden.')
    except (ValueError, KeyError):
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_link_unhide(client, arg):
    """
    Unhide the path leading to target area(s).
    Usage:  /link_unhide <aid> [aid(s)]
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /link_unhide <aid>')
    try:
        links = []
        for aid in args:
            try:
                target_id = client.server.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)

            client.area.links[str(target_id)]["hidden"] = False
            links.append(target_id)
        links = ', '.join(str(l) for l in links)
        client.send_ooc(f'Area {client.area.name} links {links} hidden.')
    except (ValueError, KeyError):
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_link_pos(client, arg):
    """
    Set the link's targeted pos when using it. Leave blank to reset.
    Usage:  /link_pos <aid> [pos]
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /link_unhide <aid>')
    try:
        try:
            target_id = client.server.area_manager.get_area_by_abbreviation(args[0]).id
        except:
            target_id = int(args[0])

        pos = args[1:]
        client.area.links[str(target_id)]["target_pos"] = pos
        client.send_ooc(f'Area {client.area.name} link {target_id}\'s target pos set to "{pos}".')
    except (ValueError, KeyError):
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise


def ooc_cmd_pos_lock(client, arg):
    """
    Lock current area's available positions into a list of pos.
    Usage:  /pos_lock <pos> [pos]
    Use /pos_lock_clear to make the list empty.
    """
    if not arg:
        if len(client.area.pos_lock) > 0:
            pos = ' '.join(str(l) for l in client.area.pos_lock)
            client.send_ooc(f'Pos_lock is currently "{pos}".')
        else:
            client.send_ooc('No pos lock set.')
        return

    if not client.is_mod and (client not in client.area.owners):
        raise ClientError('You must be authorized to do that.')

    args = arg.split()
    args = sorted(set(args),key=args.index) #remove duplicates while preserving order
    for pos in args:
        if len(pos) < 3:
            raise ClientError('Position names may not be shorter than 3 symbols!')
    #     if pos not in ('def', 'pro', 'hld', 'hlp', 'jud', 'wit', 'sea', 'jur'):
    #         raise ClientError('Invalid pos.')
       
    client.area.pos_lock = args
    pos = ' '.join(str(l) for l in client.area.pos_lock)
    client.area.broadcast_ooc(f'Locked pos into {pos}.')
    client.area.send_command('SD', '*'.join(pos)) #set that juicy pos dropdown


@mod_only(area_owners=True)
def ooc_cmd_pos_lock_clear(client, arg):
    """
    Clear the current area's position lock and make all positions available.
    Usage:  /pos_lock_clear
    """
    client.area.pos_lock.clear()
    client.area.broadcast_ooc('Position lock cleared.')


def ooc_cmd_peek(client, arg):
    """
    Peek into a room to see if there's people in it or if it's locked.
    Usage:  /peek <id>
    """
    args = arg.split()
    if len(args) == 0:
        raise ArgumentError('You need to input an accessible area name or ID to peek into it!')

    try:
        area = None
        for _area in client.server.area_manager.areas:
            if (args[0].isdigit() and _area.id == int(args[0])) or _area.abbreviation.lower() == args[0].lower() or _area.name.lower() == arg.lower():
                area = _area
                break
        if area == None:
            raise ClientError('Target area not found.')

        sorted_clients = []
        for c in area.clients:
            if not c.hidden and not c in area.owners and not c.is_mod: #pure IC
                sorted_clients.append(c)

        allowed = client.is_mod or client in area.owners or client in client.area.owners
        if len(client.area.links) > 0:
            if not str(area.id) in client.area.links and not allowed:
                raise ClientError('That area is inaccessible from your area!')

            if str(area.id) in client.area.links:
                # Get that link reference
                link = client.area.links[str(area.id)]

                # Our path is locked :(
                if link["locked"] and not allowed:
                    raise ClientError('That path is locked - cannot access area!')

        if area.is_locked == area.Locked.LOCKED and not client.is_mod and not client.id in area.invite_list:
            raise ClientError('That area is locked!')

        _sort = [c.char_name for c in sorted(sorted_clients, key=lambda x: x.char_name)]

        # this would be nice to be a separate "make human readable list" func
        if len(_sort) == 2:
            sorted_clients = ' and '.join(_sort)
        elif len(_sort) > 2:
            sorted_clients = ', '.join(_sort[:-1])
            sorted_clients = "{} and {}".format(sorted_clients, _sort[-1])
        elif len(_sort) == 1:
            sorted_clients = _sort[0]

        if len(sorted_clients) <= 0:
            sorted_clients = 'nobody'

        client.area.broadcast_ooc(f'[{client.id}] {client.char_name} peeks into [{area.id}] {area.name}...')
        client.send_ooc(f'There\'s {sorted_clients} in [{area.id}] {area.name}.')
    except ValueError:
        raise ArgumentError('Area ID must be a number or name.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_area_move_delay(client, arg):
    """
    Set the area's move delay to a value in seconds. Can be negative.
    Delay must be from -1800 to 1800 in seconds or empty to check.
    Usage: /area_move_delay [delay]
    """
    args = arg.split()
    try:
        if len(args) > 0:
            move_delay = min(1800, max(-1800, int(args[0]))) # Move delay is limited between -1800 and 1800
            client.area.move_delay = move_delay
            client.send_ooc(f'Set {client.area.name} movement delay to {move_delay}.')
        else:
            client.send_ooc(f'Current move delay for {client.area.name} is {client.area.move_delay}.')
    except ValueError:
        raise ArgumentError('Delay must be an integer between -1800 and 1800.')
    except (AreaError, ClientError):
        raise


@mod_only()
def ooc_cmd_hub_move_delay(client, arg):
    """
    Set the hub's move delay to a value in seconds. Can be negative.
    Delay must be from -1800 to 1800 in seconds or empty to check.
    Usage: /hub_move_delay [delay]
    """
    args = arg.split()
    try:
        if len(args) > 0:
            move_delay = min(1800, max(-1800, int(args[0]))) # Move delay is limited between -1800 and 1800
            client.area.area_manager.move_delay = move_delay
            client.send_ooc(f'Set {client.area.name} movement delay to {move_delay}.')
        else:
            client.send_ooc(f'Current move delay for {client.area.name} is {client.area.area_manager.move_delay}.')
    except ValueError:
        raise ArgumentError('Delay must be an integer between -1800 and 1800.')
    except (AreaError, ClientError):
        raise