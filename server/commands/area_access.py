from server.exceptions import ClientError, ArgumentError, AreaError
from . import mod_only

__all__ = [
    "ooc_cmd_area_lock",
    "ooc_cmd_area_unlock",
    "ooc_cmd_area_mute",
    "ooc_cmd_area_unmute",
    "ooc_cmd_lock",
    "ooc_cmd_unlock",
    "ooc_cmd_link",
    "ooc_cmd_unlink",
    "ooc_cmd_links",
    "ooc_cmd_onelink",
    "ooc_cmd_oneunlink",
    "ooc_cmd_link_lock",
    "ooc_cmd_link_unlock",
    "ooc_cmd_link_hide",
    "ooc_cmd_link_unhide",
    "ooc_cmd_link_pos",
    "ooc_cmd_link_peekable",
    "ooc_cmd_link_unpeekable",
    "ooc_cmd_link_evidence",
    "ooc_cmd_unlink_evidence",
    "ooc_cmd_pw",
    "ooc_cmd_setpw",
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
                target_id = client.area.area_manager.get_area_by_abbreviation(
                    aid).id
            except Exception:
                target_id = int(aid)
            area = client.area.area_manager.get_area_by_id(target_id)

            if not client.is_mod and client not in area.owners:
                if not str(target_id) in client.keys:
                    if area.locking_allowed and area != client.area:
                        client.send_ooc(
                            "You can only lock that area from within!")
                        continue
                    if not area.locking_allowed:
                        client.send_ooc(
                            f"You don't have the keys to {area.name}.")
                        continue
                if not client.can_access_area(area):
                    client.send_ooc(
                        f"You have the keys to {area.name} but it is not accessible from your area."
                    )
                    continue
                if (
                    str(area.id) in client.area.links
                    and client.area.links[str(area.id)]["locked"]
                ):
                    client.send_ooc(
                        f"You have the keys to {area.name} but the path is locked."
                    )
                    continue
            if area.locked:
                client.send_ooc(f"Area {area.name} is already locked.")
                continue
            area.lock()
            area_list.append(area.id)
        if len(area_list) > 0:
            client.send_ooc(f"Locked areas {area_list}.")
    except ValueError:
        raise ArgumentError("Target must be an abbreviation or number.")
    except (ClientError, AreaError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_area_mute(client, arg):
    """
    Makes this area impossible to speak for normal users unlesss /invite is used.
    Usage: /area_mute
    """
    args = arg.split()
    if len(args) == 0:
        args = [client.area.id]

    try:
        area_list = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(
                    aid).id
            except Exception:
                target_id = int(aid)
            area = client.area.area_manager.get_area_by_id(target_id)
            if not client.is_mod and client not in area.owners:
                client.send_ooc(f"You don't own area [{area.id}] {area.name}.")
                continue

            if area.muted:
                client.send_ooc(
                    f"Area [{area.id}] {area.name} is already muted.")
                continue
            area.mute()
            area.broadcast_ooc("This area is now muted.")
            area_list.append(area.id)
        if len(area_list) > 0:
            client.send_ooc(f"Made areas {area_list} muted.")
    except ValueError:
        raise ArgumentError("Target must be an abbreviation or number.")
    except (ClientError, AreaError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_area_unmute(client, arg):
    """
    Undo the effects of /area_mute.
    Usage: /area_unmute
    """
    args = arg.split()
    if len(args) == 0:
        args = [client.area.id]

    try:
        area_list = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(
                    aid).id
            except Exception:
                target_id = int(aid)
            area = client.area.area_manager.get_area_by_id(target_id)
            if not client.is_mod and client not in area.owners:
                client.send_ooc(f"You don't own area [{area.id}] {area.name}.")
                continue

            if not area.muted:
                client.send_ooc(
                    f"Area [{area.id}] {area.name} is already unmuted.")
                continue
            area.unmute()
            area.broadcast_ooc("This area is no longer muted.")
            area_list.append(area.id)
        if len(area_list) > 0:
            client.send_ooc(f"Made areas {area_list} unmuted.")
    except ValueError:
        raise ArgumentError("Target must be an abbreviation or number.")
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
                target_id = client.area.area_manager.get_area_by_abbreviation(
                    aid).id
            except Exception:
                target_id = int(aid)
            area = client.area.area_manager.get_area_by_id(target_id)

            if not client.is_mod and client not in area.owners:
                if not str(target_id) in client.keys:
                    if area.locking_allowed and area != client.area:
                        client.send_ooc(
                            "You can only unlock that area from within!")
                        continue
                    if not area.locking_allowed:
                        client.send_ooc(
                            "You don't have the keys to {area.name}.")
                        continue
                if not client.can_access_area(area):
                    client.send_ooc(
                        f"You have the keys to {area.name} but it is not accessible from your area."
                    )
                    continue
                if (
                    str(area.id) in client.area.links
                    and client.area.links[str(area.id)]["locked"]
                ):
                    client.send_ooc(
                        f"You have the keys to {area.name} but the path is locked."
                    )
                    continue
            if not area.locked:
                client.send_ooc(f"Area {area.name} is already unlocked.")
                continue
            area.unlock()
            area_list.append(area.id)
        if len(area_list) > 0:
            client.send_ooc(f"Unlocked areas {area_list}.")
    except ValueError:
        raise ArgumentError("Target must be an abbreviation or number.")
    except (ClientError, AreaError):
        raise


def ooc_cmd_lock(client, arg):
    """
    Context-sensitive function to lock area(s) and/or area link(s).
    Usage: /lock - lock current area. /lock [id] - lock target area. /lock !5 - lock the link from current area to area 5.
    Multiple targets may be passed.
    """
    if arg == "":
        arg = str(client.area.id)
    args = arg.split()
    areas = args.copy()
    links = []
    for a in args:
        if not a.startswith("!"):
            continue
        areas.remove(a)
        links.append(a[1:])
    if len(areas) > 0:
        areas = " ".join(areas)
        ooc_cmd_area_lock(client, areas)
    if len(links) > 0:
        links = " ".join(links)
        print(links)
        ooc_cmd_link_lock(client, links)


def ooc_cmd_unlock(client, arg):
    """
    Context-sensitive function to unlock area(s) and/or area link(s).
    Usage: /unlock - unlock current area. /unlock [id] - unlock target area. /unlock !5 - unlock the link from current area to area 5.
    Multiple targets may be passed.
    """
    if arg == "":
        arg = str(client.area.id)
    args = arg.split()
    areas = args.copy()
    links = []
    for a in args:
        if not a.startswith("!"):
            continue
        areas.remove(a)
        links.append(a[1:])
    if len(areas) > 0:
        areas = " ".join(areas)
        ooc_cmd_area_unlock(client, areas)
    if len(links) > 0:
        links = " ".join(links)
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
            except Exception:
                area = client.area.area_manager.get_area_by_id(int(aid))
                target_id = area.id

            if not client.is_mod and client not in area.owners:
                client.send_ooc(f"You don't own area [{area.id}] {area.name}.")
                continue

            client.area.link(target_id)
            # Connect the target area to us
            area.link(client.area.id)
            links.append(target_id)
        links = ", ".join(str(link) for link in links)
        client.send_ooc(
            f"Area {client.area.name} has been linked with {links} (two-way)."
        )
        client.area.broadcast_area_list()
        area.broadcast_area_list()
    except ValueError:
        raise ArgumentError("Area ID must be a number or abbreviation.")
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
        raise ArgumentError("Invalid number of arguments. Use /unlink <aid>")
    try:
        links = []
        for aid in args:
            try:
                area = client.area.area_manager.get_area_by_abbreviation(aid)
                target_id = area.id
            except Exception:
                area = client.area.area_manager.get_area_by_id(int(aid))
                target_id = area.id

            if not client.is_mod and client not in area.owners:
                client.send_ooc(f"You don't own area [{area.id}] {area.name}.")
                continue

            try:
                client.area.unlink(target_id)
                # Disconnect the target area from us
                area.unlink(client.area.id)
                links.append(target_id)
            except Exception:
                continue
        links = ", ".join(str(link) for link in links)
        client.send_ooc(
            f"Area {client.area.name} has been unlinked with {links} (two-way)."
        )
        client.area.broadcast_area_list()
        area.broadcast_area_list()
    except ValueError:
        raise ArgumentError("Area ID must be a number or abbreviation.")
    except (AreaError, ClientError):
        raise


def ooc_cmd_links(client, arg):
    """
    Display this area's information about area links.
    Usage:  /links
    """
    links = ""
    for key, value in sorted(client.area.links.items(), key=lambda x: int(x[0])):
        hidden = ""
        if value["hidden"] is True:
            # Can't see hidden links
            if not client.is_mod and client not in client.area.owners:
                continue
            hidden = "📦"

        if len(value["evidence"]) > 0 and not (client.hidden_in in value["evidence"]):
            # Can't see hidden links
            if not client.is_mod and client not in client.area.owners:
                continue
            evi_list = ", ".join(str(evi + 1) for evi in value["evidence"])
            hidden = f"📦:{evi_list}"

        try:
            area_name = f' - "{client.area.area_manager.get_area_by_id(int(key)).name}"'
        except Exception:
            area_name = ""

        locked = ""
        if value["locked"] is True:
            locked = "🚧"
        if value["password"] != "":
            locked = "🔑"

        target_pos = value["target_pos"]
        if target_pos != "":
            target_pos = f", pos: {target_pos}"
        links += f"\n!{key}{area_name}{locked}{hidden}{target_pos}"

    client.send_ooc(f"Current area links are: {links}")


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
            except Exception:
                area = client.area.area_manager.get_area_by_id(int(aid))
                target_id = area.id

            if not client.is_mod and client not in area.owners:
                client.send_ooc(f"You don't own area [{area.id}] {area.name}.")
                continue

            client.area.link(target_id)
            links.append(target_id)
        links = ", ".join(str(link) for link in links)
        client.send_ooc(
            f"Area {client.area.name} has been linked with {links} (one-way)."
        )
        client.area.broadcast_area_list()
    except ValueError:
        raise ArgumentError("Area ID must be a number or abbreviation.")
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
        raise ArgumentError(
            "Invalid number of arguments. Use /oneunlink <aid>")
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(
                    aid).id
            except Exception:
                target_id = int(aid)

            try:
                client.area.unlink(target_id)
                links.append(target_id)
            except Exception:
                continue
        links = ", ".join(str(link) for link in links)
        client.send_ooc(
            f"Area {client.area.name} has been unlinked with {links} (one-way)."
        )
        client.area.broadcast_area_list()
    except ValueError:
        raise ArgumentError("Area ID must be a number or abbreviation.")
    except (AreaError, ClientError):
        raise


def ooc_cmd_link_lock(client, arg):
    """
    Lock the path leading to target area(s).
    Usage:  /link_lock <id(s)>
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError(
            "Invalid number of arguments. Use /link_lock <aid>")
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(
                    aid).id
            except Exception:
                target_id = int(aid)
            if not client.is_mod and client not in client.area.owners:
                if f"{client.area.id}-{target_id}" not in client.keys:
                    client.send_ooc(
                        f"You don't have the keys to the link {client.area.id}-{target_id}."
                    )
                    continue
                target_area = client.area.area_manager.get_area_by_id(
                    target_id)
                if (
                    f"{target_id}-{client.area.id}" in client.keys
                    and str(client.area.id) in target_area.links
                ):  # Treat it as a single door/path if we have the keys both ways
                    target_area.links[str(client.area.id)]["locked"] = True
                    client.send_ooc(
                        f"Locked {client.area.id}-{target_id} both ways.")
            client.area.links[str(target_id)]["locked"] = True
            links.append(target_id)
        if len(links) > 0:
            links = ", ".join(str(link) for link in links)
            client.send_ooc(f"Area {client.area.name} links {links} locked.")
    except (ValueError, KeyError):
        raise ArgumentError(
            "Area ID must be a number or abbreviation and the link must exist."
        )
    except (AreaError, ClientError):
        raise


def ooc_cmd_link_unlock(client, arg):
    """
    Unlock the path leading to target area(s).
    Usage:  /link_unlock <id(s)>
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError(
            "Invalid number of arguments. Use /link_unlock <aid>")
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(
                    aid).id
            except Exception:
                target_id = int(aid)
            if not client.is_mod and client not in client.area.owners:
                if f"{client.area.id}-{target_id}" not in client.keys:
                    client.send_ooc(
                        f"You don't have the keys to the link {client.area.id}-{target_id}."
                    )
                    continue
                target_area = client.area.area_manager.get_area_by_id(
                    target_id)
                if (
                    f"{target_id}-{client.area.id}" in client.keys
                    and str(client.area.id) in target_area.links
                ):  # Treat it as a single door/path if we have the keys both ways
                    target_area.links[str(client.area.id)]["locked"] = False
                    client.send_ooc(
                        f"Unlocked {client.area.id}-{target_id} both ways.")
            client.area.links[str(target_id)]["locked"] = False
            links.append(target_id)
        if len(links) > 0:
            links = ", ".join(str(link) for link in links)
            client.send_ooc(f"Area {client.area.name} links {links} unlocked.")
    except (ValueError, KeyError):
        raise ArgumentError(
            "Area ID must be a number or abbreviation and the link must exist."
        )
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
        raise ArgumentError(
            "Invalid number of arguments. Use /link_hide <aid>")
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(
                    aid).id
            except Exception:
                target_id = int(aid)

            client.area.links[str(target_id)]["hidden"] = True
            links.append(target_id)
        if len(links) > 0:
            links = ", ".join(str(link) for link in links)
            client.send_ooc(f"Area {client.area.name} links {links} hidden.")
    except (ValueError, KeyError):
        raise ArgumentError("Area ID must be a number or abbreviation.")
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
        raise ArgumentError(
            "Invalid number of arguments. Use /link_unhide <aid>")
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(
                    aid).id
            except Exception:
                target_id = int(aid)

            client.area.links[str(target_id)]["hidden"] = False
            links.append(target_id)
        if len(links) > 0:
            links = ", ".join(str(link) for link in links)
            client.send_ooc(f"Area {client.area.name} links {links} revealed.")
    except (ValueError, KeyError):
        raise ArgumentError("Area ID must be a number or abbreviation.")
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
        raise ArgumentError(
            "Invalid number of arguments. Use /link_unhide <aid>")
    try:
        try:
            target_id = client.area.area_manager.get_area_by_abbreviation(
                args[0]).id
        except Exception:
            target_id = int(args[0])

        pos = args[1:]
        client.area.links[str(target_id)]["target_pos"] = pos
        client.send_ooc(
            f'Area {client.area.name} link {target_id}\'s target pos set to "{pos}".'
        )
    except (ValueError, KeyError):
        raise ArgumentError("Area ID must be a number or abbreviation.")
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
        raise ArgumentError(
            "Invalid number of arguments. Use /link_peekable <aid>")
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(
                    aid).id
            except Exception:
                target_id = int(aid)

            client.area.links[str(target_id)]["can_peek"] = True
            links.append(target_id)
        if len(links) > 0:
            links = ", ".join(str(link) for link in links)
            client.send_ooc(
                f"Area {client.area.name} links {links} are now peekable.")
    except (ValueError, KeyError):
        raise ArgumentError("Area ID must be a number or abbreviation.")
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
        raise ArgumentError(
            "Invalid number of arguments. Use /link_unpeekable <aid>")
    try:
        links = []
        for aid in args:
            try:
                target_id = client.area.area_manager.get_area_by_abbreviation(
                    aid).id
            except Exception:
                target_id = int(aid)

            client.area.links[str(target_id)]["can_peek"] = False
            links.append(target_id)
        if len(links) > 0:
            links = ", ".join(str(link) for link in links)
            client.send_ooc(
                f"Area {client.area.name} links {links} are no longer peekable."
            )
    except (ValueError, KeyError):
        raise ArgumentError("Area ID must be a number or abbreviation.")
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
        raise ArgumentError(
            "Invalid number of arguments. Use /link_evidence <id> [evi_id(s)]"
        )
    link = None
    evidences = []
    try:
        link = client.area.links[args[0]]
        if len(args) > 1:
            for evi_id in args[1:]:
                evi_id = int(evi_id) - 1
                client.area.evi_list.evidences[
                    evi_id
                ]  # Test if we can access target evidence
                evidences.append(evi_id)
    except IndexError:
        raise ArgumentError("Evidence not found.")
    except (ValueError, KeyError):
        raise ArgumentError("Area ID must be a number.")
    except (AreaError, ClientError):
        raise
    else:
        if len(evidences) > 0:
            link["evidence"] = evidences

        if len(link["evidence"]) > 0:
            evi_list = ", ".join(str(evi + 1) for evi in link["evidence"])
            client.send_ooc(
                f"Area {client.area.name} link {args[0]} associated evidence IDs: {evi_list}."
            )
        else:
            client.send_ooc(
                f"Area {client.area.name} link {args[0]} has no associated evidence."
            )


@mod_only(area_owners=True)
def ooc_cmd_unlink_evidence(client, arg):
    """
    Unlink evidence from links.
    Pass evidence ID's which you can see by mousing over evidence.
    Usage:  /unlink_evidence <aid> [evi_id(s)]
    """
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError(
            "Invalid number of arguments. Use /unlink_evidence <aid> [evi_id(s)]"
        )
    link = None
    evidences = []
    try:
        link = client.area.links[args[0]]
        if len(args) > 1:
            for evi_id in args[1:]:
                evi_id = int(evi_id) - 1
                evidences.append(evi_id)
    except (ValueError, KeyError):
        raise ArgumentError("Area ID must be a number.")
    except (AreaError, ClientError):
        raise
    else:
        if len(evidences) > 0:
            link["evidence"] = link["evidence"] - evidences
            evi_list = ", ".join(str(evi + 1) for evi in evidences)
            client.send_ooc(
                f"Area {client.area.name} link {args[0]} is now unlinked from evidence IDs: {evi_list}."
            )
        else:
            link["evidence"] = []
            client.send_ooc(
                f"Area {client.area.name} link {args[0]} associated evidences cleared."
            )


def ooc_cmd_pw(client, arg):
    """
    Enter a passworded area. Password is case-sensitive and must match the set password exactly, otherwise it will fail.
    You will move into the target area as soon as the correct password is provided.
    Leave password empty if you own the area and want to check its current password.
    Usage:  /pw <id> [password]
    """
    link = None
    password = ""
    if arg == "":
        if not client.is_mod and not (client in client.area.owners):
            raise ArgumentError(
                "You are not allowed to see this area's password. Use /pw <id> [password]"
            )
        aid = client.area.id
    else:
        args = arg.split()
        aid = args[0]
        if aid in client.area.links:
            link = client.area.links[aid]
        if len(args) > 1:
            password = args[1]

    try:
        area = client.area.area_manager.get_area_by_id(int(aid))
        if password == "":
            if client.is_mod or client in client.area.owners:
                if link is not None and link["password"] != "":
                    client.send_ooc(
                        f'Link {client.area.id}-{area.id} password is: {link["password"]}'
                    )
                else:
                    client.send_ooc(
                        f"Area [{area.id}] {area.name} password is: {area.password}"
                    )
            else:
                raise ClientError(
                    "You must provide a password. Use /pw <id> [password]"
                )
        else:
            client.change_area(area, password=password)
    except ValueError:
        raise ArgumentError("Area ID must be a number.")
    except (AreaError, ClientError):
        raise


@mod_only(area_owners=True)
def ooc_cmd_setpw(client, arg):
    """
    Context-sensitive function to set a password area(s) and/or area link(s).
    Pass area id, or link id from current area using !, e.g. 5 vs !5.
    Leave [password] blank to clear the password.
    Usage:  /setpw <id> [password]
    """
    args = arg.split()
    if len(args) == 0:
        raise ArgumentError(
            "Invalid number of arguments. Use /setpw <id> [password]")

    try:
        password = ""
        link = None
        area = client.area
        if args[0].startswith("!"):
            num = args[0][1:]
            if num in client.area.links:
                link = client.area.links[num]
                area = client.area.area_manager.get_area_by_id(int(num))
            else:
                raise ArgumentError(
                    "Targeted link does not exist in current area.")
        else:
            area = client.area.area_manager.get_area_by_id(int(args[0]))
        if len(args) > 1:
            password = args[1]
        if not client.is_mod and not (client in area.owners):
            raise ClientError("You do not own that area!")
        if link is not None:
            link["password"] = password
            client.send_ooc(
                f"Link {client.area.id}-{area.id} password set to: {password}"
            )
        else:
            area.password = password
            client.send_ooc(
                f"Area [{area.id}] {area.name} password set to: {password}")
    except ValueError:
        raise ArgumentError(
            "Area ID must be a number, or a link ID must start with ! e.g. 5 vs !5."
        )
    except (AreaError, ClientError):
        raise
