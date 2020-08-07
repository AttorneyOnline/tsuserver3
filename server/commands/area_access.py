from server.exceptions import ClientError, ArgumentError, AreaError
from . import mod_only

__all__ = [
    'ooc_cmd_area_lock',
    'ooc_cmd_area_spectate',
    'ooc_cmd_area_unlock',
    'ooc_cmd_lock',
    'ooc_cmd_unlock',
    'ooc_cmd_link',
    'ooc_cmd_unlink',
    'ooc_cmd_links',
    'ooc_cmd_onelink',
    'ooc_cmd_oneunlink',
    'ooc_cmd_link_lock',
    'ooc_cmd_link_unlock',
    'ooc_cmd_link_hide',
    'ooc_cmd_link_unhide',
    'ooc_cmd_link_pos',
    'ooc_cmd_link_peekable',
    'ooc_cmd_link_unpeekable',
    'ooc_cmd_link_evidence',
    'ooc_cmd_unlink_evidence',
]


def ooc_cmd_area_lock(client, arg):
    """
    Prevent users from joining the current area.
    Usage: /area_lock
    """
    args = arg.split()
    if len(args) == 0:
        args = [client.area.id]

    try:
        area_list = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)
            area = client.area.area_manager.get_area_by_id(target_id)

            if not client.is_mod and not client in area.owners:
                if not area.locking_allowed and not str(target_id) in client.keys:
                    client.send_ooc(f'You don\'t have the keys to {area.name}.')
                    continue
                if not client.can_access_area(area):
                    client.send_ooc(f'You have the keys to {area.name} but it is not accessible from your area.')
                    continue
            if area.is_locked == client.area.Locked.LOCKED:
                client.send_ooc(f'Area {area.name} is already locked.')
                continue
            area.lock()
            area_list.append(area.id)
        if len(area_list) > 0:
            client.send_ooc(f'Locked areas {area_list}.')
    except ValueError:
        raise ArgumentError('Target must be an abbreviation or number.')
    except (ClientError, AreaError):
        raise


def ooc_cmd_area_spectate(client, arg):
    """
    Allow users to join the current area, but only as spectators.
    Usage: /area_spectate
    """
    args = arg.split()
    if len(args) == 0:
        args = [client.area.id]

    try:
        area_list = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)
            area = client.area.area_manager.get_area_by_id(target_id)

            if not client.is_mod and not client in area.owners:
                if not area.locking_allowed and not str(target_id) in client.keys:
                    client.send_ooc(f'You don\'t have the keys to {area.name}.')
                    continue
                if not client.can_access_area(area):
                    client.send_ooc(f'You have the keys to {area.name} but it is not accessible from your area.')
                    continue
            if area.is_locked == client.area.Locked.SPECTATABLE:
                client.send_ooc(f'Area {area.name} is already spectatable.')
                continue
            area.spectator()
            area_list.append(area.id)
        if len(area_list) > 0:
            client.send_ooc(f'Made areas {area_list} spectatable.')
    except ValueError:
        raise ArgumentError('Target must be an abbreviation or number.')
    except (ClientError, AreaError):
        raise


def ooc_cmd_area_unlock(client, arg):
    """
    Allow anyone to freely join the current area.
    Usage: /area_unlock
    """
    args = arg.split()
    if len(args) == 0:
        args = [client.area.id]

    try:
        area_list = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)
            area = client.area.area_manager.get_area_by_id(target_id)

            if not client.is_mod and not client in area.owners:
                if not area.locking_allowed and not str(target_id) in client.keys:
                    client.send_ooc(f'You don\'t have the keys to {area.name}.')
                    continue
                if not client.can_access_area(area):
                    client.send_ooc(f'You have the keys to {area.name} but it is not accessible from your area.')
                    continue
            if area.is_locked == client.area.Locked.FREE:
                client.send_ooc(f'Area {area.name} is already unlocked.')
                continue
            area.unlock()
            area_list.append(area.id)
        if len(area_list) > 0:
            client.send_ooc(f'Unlocked areas {area_list}.')
    except ValueError:
        raise ArgumentError('Target must be an abbreviation or number.')
    except (ClientError, AreaError):
        raise


def ooc_cmd_lock(client, arg):
    """
    Context-sensitive function to lock area(s) and/or area link(s).
    Usage: /lock - lock current area. /lock [id] - lock target area. /lock !5 - lock the link from current area to area 5.
    Multiple targets may be passed.
    """
    if arg == '':
        arg = str(client.area.id)
    args = arg.split()
    areas = args.copy()
    links = []
    for a in args:
        if not a.startswith('!'):
            continue
        areas.remove(a)
        links.append(a[1:])
    if len(areas) > 0:
        areas = ' '.join(areas)
        ooc_cmd_area_lock(client, areas)
    if len(links) > 0:
        links = ' '.join(links)
        print(links)
        ooc_cmd_link_lock(client, links)


def ooc_cmd_unlock(client, arg):
    """
    Context-sensitive function to unlock area(s) and/or area link(s).
    Usage: /unlock - unlock current area. /unlock [id] - unlock target area. /unlock !5 - unlock the link from current area to area 5.
    Multiple targets may be passed.
    """
    if arg == '':
        arg = str(client.area.id)
    args = arg.split()
    areas = args.copy()
    links = []
    for a in args:
        if not a.startswith('!'):
            continue
        areas.remove(a)
        links.append(a[1:])
    if len(areas) > 0:
        areas = ' '.join(areas)
        ooc_cmd_area_unlock(client, areas)
    if len(links) > 0:
        links = ' '.join(links)
        ooc_cmd_link_unlock(client, links)


@mod_only(area_owners=True)
def ooc_cmd_link(client, arg):
    """
    Set up a two-way link from your current area with targeted area(s).
    Usage:  /link <id(s)>
    """
    args = arg.split()
    if len(args) <= 0:
        ooc_cmd_links(client, arg)
        return
    try:
        links = []
        for aid in args:
            try:
                area = client.area.area_manager.get_area_by_abbreviation(aid)
                target_id = area.id
            except:
                area = client.area.area_manager.get_area_by_id(int(aid))
                target_id = area.id

            client.area.link(target_id)
            # Connect the target area to us
            area.link(client.area.id)
            links.append(target_id)
        links = ', '.join(str(l) for l in links)
        client.send_ooc(f'Area {client.area.name} has been linked with {links} (two-way).')
    except ValueError:
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise

@mod_only(area_owners=True)
def ooc_cmd_unlink(client, arg):
    """
    Remove a two-way link from your current area with targeted area(s).
    Usage:  /unlink <id(s)>
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /unlink <aid>')
    try:
        links = []
        for aid in args:
            try:
                area = client.area.area_manager.get_area_by_abbreviation(aid)
                target_id = area.id
            except:
                area = client.area.area_manager.get_area_by_id(int(aid))
                target_id = area.id

            try:
                client.area.unlink(target_id)
                # Disconnect the target area from us
                area.unlink(client.area.id)
                links.append(target_id)
            except:
                continue
        links = ', '.join(str(l) for l in links)
        client.send_ooc(f'Area {client.area.name} has been unlinked with {links} (two-way).')
    except ValueError:
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise


def ooc_cmd_links(client, arg):
    """
    Display this area's information about area links.
    Usage:  /links
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
            area_name = f' - "{client.area.area_manager.get_area_by_id(int(key)).name}"'
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
def ooc_cmd_onelink(client, arg):
    """
    Set up a one-way link from your current area with targeted area(s).
    Usage:  /onelink <id(s)>
    """
    args = arg.split()
    if len(args) <= 0:
        ooc_cmd_links(client, arg)
        return
    try:
        links = []
        for aid in args:
            try:
                area = client.area.area_manager.get_area_by_abbreviation(aid)
                target_id = area.id
            except:
                area = client.area.area_manager.get_area_by_id(int(aid))
                target_id = area.id

            client.area.link(target_id)
            links.append(target_id)
        links = ', '.join(str(l) for l in links)
        client.send_ooc(f'Area {client.area.name} has been linked with {links} (one-way).')
    except ValueError:
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_oneunlink(client, arg):
    """
    Remove a one-way link from your current area with targeted area(s).
    Usage:  /oneunlink <id(s)>
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /oneunlink <aid>')
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)

            try:
                client.area.unlink(target_id)
                links.append(target_id)
            except:
                continue
        links = ', '.join(str(l) for l in links)
        client.send_ooc(f'Area {client.area.name} has been unlinked with {links} (one-way).')
    except ValueError:
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise

def ooc_cmd_link_lock(client, arg):
    """
    Lock the path leading to target area(s).
    Usage:  /link_lock <id(s)>
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /link_lock <aid>')
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)
            if not client.is_mod and not client in client.area.owners:
                if not f'{client.area.id}-{target_id}' in client.keys:
                    client.send_ooc(f'You don\'t have the keys to the link {client.area.id}-{target_id}.')
                    continue
            client.area.links[str(target_id)]["locked"] = True
            links.append(target_id)
        if len(links) > 0:
            links = ', '.join(str(l) for l in links)
            client.send_ooc(f'Area {client.area.name} links {links} locked.')
    except (ValueError, KeyError):
        raise ArgumentError('Area ID must be a number or abbreviation and the link must exist.')
    except (AreaError, ClientError):
        raise


def ooc_cmd_link_unlock(client, arg):
    """
    Unlock the path leading to target area(s).
    Usage:  /link_unlock <id(s)>
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /link_unlock <aid>')
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)
            if not client.is_mod and not client in client.area.owners:
                if not f'{client.area.id}-{target_id}' in client.keys:
                    client.send_ooc(f'You don\'t have the keys to the link {client.area.id}-{target_id}.')
                    continue
            client.area.links[str(target_id)]["locked"] = False
            links.append(target_id)
        if len(links) > 0:
            links = ', '.join(str(l) for l in links)
            client.send_ooc(f'Area {client.area.name} links {links} unlocked.')
    except (ValueError, KeyError):
        raise ArgumentError('Area ID must be a number or abbreviation and the link must exist.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_link_hide(client, arg):
    """
    Hide the path leading to target area(s).
    Usage:  /link_hide <id(s)>
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /link_hide <aid>')
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)

            client.area.links[str(target_id)]["hidden"] = True
            links.append(target_id)
        if len(links) > 0:
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
    Usage:  /link_unhide <id(s)>
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /link_unhide <aid>')
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)

            client.area.links[str(target_id)]["hidden"] = False
            links.append(target_id)
        if len(links) > 0:
            links = ', '.join(str(l) for l in links)
            client.send_ooc(f'Area {client.area.name} links {links} revealed.')
    except (ValueError, KeyError):
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_link_pos(client, arg):
    """
    Set the link's targeted pos when using it. Leave blank to reset.
    Usage:  /link_pos <id> [pos]
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /link_unhide <aid>')
    try:
        try:
            target_id = client.area.area_manager.get_area_by_abbreviation(args[0]).id
        except:
            target_id = int(args[0])

        pos = args[1:]
        client.area.links[str(target_id)]["target_pos"] = pos
        client.send_ooc(f'Area {client.area.name} link {target_id}\'s target pos set to "{pos}".')
    except (ValueError, KeyError):
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_link_peekable(client, arg):
    """
    Make the path(s) leading to target area(s) /peek-able.
    Usage:  /link_peekable <id(s)>
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /link_peekable <aid>')
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)

            client.area.links[str(target_id)]["can_peek"] = True
            links.append(target_id)
        if len(links) > 0:
            links = ', '.join(str(l) for l in links)
            client.send_ooc(f'Area {client.area.name} links {links} are now peekable.')
    except (ValueError, KeyError):
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_link_unpeekable(client, arg):
    """
    Make the path(s) leading to target area(s) no longer /peek-able.
    Usage:  /link_unpeekable <id(s)>
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /link_unpeekable <aid>')
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(aid).id
            except:
                target_id = int(aid)

            client.area.links[str(target_id)]["can_peek"] = False
            links.append(target_id)
        if len(links) > 0:
            links = ', '.join(str(l) for l in links)
            client.send_ooc(f'Area {client.area.name} links {links} are no longer peekable.')
    except (ValueError, KeyError):
        raise ArgumentError('Area ID must be a number or abbreviation.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_link_evidence(client, arg):
    """
    Make specific link only accessible from evidence ID(s).
    Pass evidence ID's which you can see by mousing over evidence, or blank to see current evidences.
    Usage:  /link_evidence <id> [evi_id(s)]
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /link_evidence <aid>')
    try:
        link = client.area.links[args[0]]
        if len(args) > 1:
            evidences = []
            for evi_id in args[1:]:
                evi_id = int(evi_id)-1
                evidences.append(client.area.evi_list.evidences[evi_id].name)
                link["evidence"].append(evi_id)
            evidences = ', '.join(f'\'{l}\'' for l in evidences)
            client.send_ooc(f'Area {client.area.name} link {args[0]} can now only be accessed from {evidences}.')
        else:
            evidences = ', '.join([f'\'{client.area.evi_list.evidences[evi].name}\'' for evi in link["evidence"]])
            client.send_ooc(f'Area {client.area.name} link {args[0]} associated evidences: {evidences}.')
    except IndexError:
        raise ArgumentError('Evidence not found.')
    except (ValueError, KeyError):
        raise ArgumentError('Area ID must be a number.')
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_unlink_evidence(client, arg):
    """
    Unlink evidence from links.
    Pass evidence ID's which you can see by mousing over evidence.
    Usage:  /unlink_evidence <aid> [evi_id(s)]
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Invalid number of arguments. Use /unlink_evidence <aid>')
    try:
        link = client.area.links[args[0]]
        if len(args) > 1:
            evidences = []
            for evi_id in args:
                evi_id = int(evi_id)-1
                link["evidence"].remove(evi_id)
            evidences = ', '.join(str(l) for l in link["evidence"])
            client.send_ooc(f'Area {client.area.name} link {args[0]} is now unlinked from evidence IDs {evidences}.')
        else:
            link["evidence"].clear()
            client.send_ooc(f'Area {client.area.name} link {args[0]} associated evidences cleared.')
    except (ValueError, KeyError):
        raise ArgumentError('Area ID must be a number.')
    except (AreaError, ClientError):
        raise