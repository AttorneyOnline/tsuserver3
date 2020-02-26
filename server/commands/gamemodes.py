from server.exceptions import ClientError, ServerError, ArgumentError, AreaError
from . import mod_only

from server.gamemodes import GamemodeYTTD

__all__ = [
    'ooc_cmd_yttd',
    'ooc_cmd_join',
    'ooc_cmd_unjoin',
    'ooc_cmd_vote',
]

@mod_only(area_owners=True)
def ooc_cmd_yttd(client, arg):
    """
    >yttd
    starts the YTTD game mode in the area
    """
    if client.area.gamemode:
        client.area.gamemode.round_end()
        del client.area.gamemode
    GamemodeYTTD(client.area)
    client.area.gamemode.start_building()

def ooc_cmd_join(client, arg):
    """
    SIGNUP
    Usage: /join
    """
    if not client.area.gamemode:
        raise AreaError('There is no gamemode.')
    client.area.gamemode.join(client)

def ooc_cmd_unjoin(client, arg):
    """
    UNSIGNUP
    Usage: /unjoin
    """
    if not client.area.gamemode:
        raise AreaError('There is no gamemode.')
    client.area.gamemode.unjoin(client)

def ooc_cmd_vote(client, arg):
    """
    Vote for the user during the trial voting time.
    Usage: /vote <id>
    """
    if not client.area.gamemode:
        raise AreaError('There is no gamemode.')
    client.area.gamemode.vote(client, arg)