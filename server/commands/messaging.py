from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError, AreaError

from . import mod_only

__all__ = [
    "ooc_cmd_g",
    "ooc_cmd_h",
    "ooc_cmd_m",
    "ooc_cmd_announce",
    "ooc_cmd_toggleglobal",
    "ooc_cmd_need",
    "ooc_cmd_toggleadverts",
    "ooc_cmd_pm",
    "ooc_cmd_mutepm",
]


def message_areas_cm(client, areas, message):
    for a in areas:
        if client not in a.owners:
            client.send_ooc(f"You are not a CM in {a.name}!")
            return
        name = f"[CM] {client.name}"
        a.send_command("CT", name, message)
        a.send_owner_command("CT", name, message)
        database.log_area("chat.cm", client, a, message=message)


def ooc_cmd_g(client, arg):
    """
    Broadcast a server-wide message.
    Usage: /g <message>
    """
    if client.muted_global:
        raise ClientError("Global chat toggled off.")
    if len(arg) == 0:
        raise ArgumentError("You can't send an empty message.")
    client.server.broadcast_global(client, arg, client.is_mod)
    database.log_area("chat.global", client, client.area, message=arg)


def ooc_cmd_h(client, arg):
    """
    Broadcast a hub-wide message.
    Usage: /h <message>
    """
    if len(arg) == 0:
        raise ArgumentError("You can't send an empty message.")
    prefix = ""
    if client.is_mod:
        prefix = "[M]"
    elif client in client.area.area_manager.owners:
        prefix = "[GM]"

    name = f"{prefix}{client.name}"
    for area in client.area.area_manager.areas:
        area.send_command("CT", f"<dollar>HUB|{name}", arg, "0")
    database.log_area("chat.hub", client, client.area, message=arg)


@mod_only()
def ooc_cmd_m(client, arg):
    """
    Send a message to all online moderators.
    Usage: /m <message>
    """
    if len(arg) == 0:
        raise ArgumentError("You can't send an empty message.")
    client.server.send_modchat(client, arg)
    database.log_area("chat.mod", client, client.area, message=arg)


@mod_only()
def ooc_cmd_announce(client, arg):
    """
    Make a server-wide announcement.
    Usage: /announce <message>
    """
    if len(arg) == 0:
        raise ArgumentError("Can't send an empty message.")
    client.server.send_all_cmd_pred(
        "CT",
        client.server.config["hostname"],
        f"=== Announcement ===\r\n{arg}\r\n==================",
        "1",
    )
    database.log_area("chat.announce", client, client.area, message=arg)


def ooc_cmd_toggleglobal(client, arg):
    """
    Mute global chat.
    Usage: /toggleglobal
    """
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.muted_global = not client.muted_global
    glob_stat = "on"
    if client.muted_global:
        glob_stat = "off"
    client.send_ooc(f"Global chat turned {glob_stat}.")


@mod_only(area_owners=True)
def ooc_cmd_need(client, arg):
    """
    Broadcast a server-wide advertisement for your role-play or case.
    Usage: /need <message>
    """
    if client.muted_adverts:
        raise ClientError("You have advertisements muted.")
    if len(arg) == 0:
        raise ArgumentError("You must specify what you need.")
    client.server.broadcast_need(client, arg)
    database.log_area("chat.announce.need", client, client.area, message=arg)


def ooc_cmd_toggleadverts(client, arg):
    """
    Mute advertisements.
    Usage: /toggleadverts
    """
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.muted_adverts = not client.muted_adverts
    adv_stat = "on"
    if client.muted_adverts:
        adv_stat = "off"
    client.send_ooc(f"Advertisements turned {adv_stat}.")


def ooc_cmd_pm(client, arg):
    """
    Send a private message to another online user. These messages are not
    logged by the server owner.
    Usage: /pm <id|ooc-name|char-name> <message>
    """
    args = arg.split()
    key = ""
    msg = None
    if len(args) < 2:
        raise ArgumentError(
            'Not enough arguments. use /pm <target> <message>. Target should be ID, OOC-name or char-name. Use /getarea for getting info like "[ID] char-name".'
        )
    targets = client.server.client_manager.get_targets(
        client, TargetType.CHAR_NAME, arg, True
    )
    key = TargetType.CHAR_NAME
    if len(targets) == 0 and args[0].isdigit():
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(args[0]), False
        )
        key = TargetType.ID
    if len(targets) == 0:
        targets = client.server.client_manager.get_targets(
            client, TargetType.OOC_NAME, arg, True
        )
        key = TargetType.OOC_NAME
    if len(targets) == 0:
        raise ArgumentError("No targets found.")
    try:
        if key == TargetType.ID:
            msg = " ".join(args[1:])
        else:
            if key == TargetType.CHAR_NAME:
                msg = arg[len(targets[0].char_name) + 1:]
            if key == TargetType.OOC_NAME:
                msg = arg[len(targets[0].name) + 1:]
    except Exception:
        raise ArgumentError(
            "Not enough arguments. Use /pm <target> <message>.")
    c = targets[0]
    if c.pm_mute:
        raise ClientError("This user muted all pm conversation")
    else:
        if c.is_mod:
            c.send_ooc(
                "PM from {} (ID: {}, IPID: {}) in {} ({}): {}".format(
                    client.name,
                    client.id,
                    client.ipid,
                    client.area.name,
                    client.showname,
                    msg,
                )
            )
        else:
            c.send_ooc(
                "PM from {} (ID: {}) in {} ({}): {}".format(
                    client.name, client.id, client.area.name, client.showname, msg
                )
            )
        client.send_ooc("PM sent to {}. Message: {}".format(args[0], msg))


def ooc_cmd_mutepm(client, arg):
    """
    Mute private messages.
    Usage: /mutepm
    """
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.pm_mute = not client.pm_mute
    client.send_ooc(
        "You stopped receiving PMs" if client.pm_mute else "You are now receiving PMs"
    )
