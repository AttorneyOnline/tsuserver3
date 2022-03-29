from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError

from . import mod_only

__all__ = [
    "ooc_cmd_disemvowel",
    "ooc_cmd_undisemvowel",
    "ooc_cmd_shake",
    "ooc_cmd_unshake",
]


@mod_only()
def ooc_cmd_disemvowel(client, arg):
    """
    Remove all vowels from a user's IC chat.
    Usage: /disemvowel <id>
    """
    if len(arg) == 0:
        raise ArgumentError("You must specify a target.")
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False
        )
    except Exception:
        raise ArgumentError("You must specify a target. Use /disemvowel <id>.")
    if targets:
        for c in targets:
            database.log_area("disemvowel", client, client.area, target=c)
            c.disemvowel = True
        client.send_ooc(f"Disemvowelled {len(targets)} existing client(s).")
    else:
        client.send_ooc("No targets found.")


@mod_only()
def ooc_cmd_undisemvowel(client, arg):
    """
    Give back the freedom of vowels to a user.
    Usage: /undisemvowel <id>
    """
    if len(arg) == 0:
        raise ArgumentError("You must specify a target.")
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False
        )
    except Exception:
        raise ArgumentError(
            "You must specify a target. Use /undisemvowel <id>.")
    if targets:
        for c in targets:
            database.log_area("undisemvowel", client, client.area, target=c)
            c.disemvowel = False
        client.send_ooc(f"Undisemvowelled {len(targets)} existing client(s).")
    else:
        client.send_ooc("No targets found.")


@mod_only()
def ooc_cmd_shake(client, arg):
    """
    Scramble the words in a user's IC chat.
    Usage: /shake <id>
    """
    if len(arg) == 0:
        raise ArgumentError("You must specify a target.")
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False
        )
    except Exception:
        raise ArgumentError("You must specify a target. Use /shake <id>.")
    if targets:
        for c in targets:
            database.log_area("shake", client, client.area, target=c)
            c.shaken = True
        client.send_ooc(f"Shook {len(targets)} existing client(s).")
    else:
        client.send_ooc("No targets found.")


@mod_only()
def ooc_cmd_unshake(client, arg):
    """
    Give back the freedom of coherent grammar to a user.
    Usage: /unshake <id>
    """
    if len(arg) == 0:
        raise ArgumentError("You must specify a target.")
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False
        )
    except Exception:
        raise ArgumentError("You must specify a target. Use /unshake <id>.")
    if targets:
        for c in targets:
            database.log_area("unshake", client, client.area, target=c)
            c.shaken = False
        client.send_ooc(f"Unshook {len(targets)} existing client(s).")
    else:
        client.send_ooc("No targets found.")
