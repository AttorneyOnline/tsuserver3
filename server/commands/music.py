from server import logger
from server.exceptions import ClientError, ServerError, ArgumentError

__all__ = [
    'ooc_cmd_currentmusic',
    'ooc_cmd_jukebox_toggle',
    'ooc_cmd_jukebox_skip',
    'ooc_cmd_jukebox',
    'ooc_cmd_play',
    'ooc_cmd_blockdj',
    'ooc_cmd_unblockdj'
]


def ooc_cmd_currentmusic(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    if client.area.current_music == '':
        raise ClientError('There is no music currently playing.')
    if client.is_mod:
        client.send_ooc(
            'The current music is {} and was played by {} ({}).'.format(
                client.area.current_music, client.area.current_music_player,
                client.area.current_music_player_ipid))
    else:
        client.send_ooc(
            'The current music is {} and was played by {}.'.format(
                client.area.current_music, client.area.current_music_player))


def ooc_cmd_jukebox_toggle(client, arg):
    if not client.is_mod and not client in client.area.owners:
        raise ClientError('You must be authorized to do that.')
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    client.area.jukebox = not client.area.jukebox
    client.area.jukebox_votes = []
    client.area.broadcast_ooc('{} [{}] has set the jukebox to {}.'.format(
        client.char_name, client.id, client.area.jukebox))


def ooc_cmd_jukebox_skip(client, arg):
    if not client.is_mod and not client in client.area.owners:
        raise ClientError('You must be authorized to do that.')
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    if not client.area.jukebox:
        raise ClientError('This area does not have a jukebox.')
    if len(client.area.jukebox_votes) == 0:
        raise ClientError(
            'There is no song playing right now, skipping is pointless.')
    client.area.start_jukebox()
    if len(client.area.jukebox_votes) == 1:
        client.area.broadcast_ooc(
            '{} [{}] has forced a skip, restarting the only jukebox song.'.
            format(client.char_name, client.id))
    else:
        client.area.broadcast_ooc(
            '{} [{}] has forced a skip to the next jukebox song.'.format(
                client.char_name, client.id))
    logger.log_server(
        '[{}][{}]Skipped the current jukebox song.'.format(
            client.area.abbreviation, client.char_name), client)


def ooc_cmd_jukebox(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    if not client.area.jukebox:
        raise ClientError('This area does not have a jukebox.')
    if len(client.area.jukebox_votes) == 0:
        client.send_ooc('The jukebox has no songs in it.')
    else:
        total = 0
        songs = []
        voters = dict()
        chance = dict()
        message = ''

        for current_vote in client.area.jukebox_votes:
            if songs.count(current_vote.name) == 0:
                songs.append(current_vote.name)
                voters[current_vote.name] = [current_vote.client]
                chance[current_vote.name] = current_vote.chance
            else:
                voters[current_vote.name].append(current_vote.client)
                chance[current_vote.name] += current_vote.chance
            total += current_vote.chance

        for song in songs:
            message += '\n- ' + song + '\n'
            message += '-- VOTERS: '

            first = True
            for voter in voters[song]:
                if first:
                    first = False
                else:
                    message += ', '
                message += voter.char_name + ' [' + str(voter.id) + ']'
                if client.is_mod:
                    message += '(' + str(voter.ipid) + ')'
            message += '\n'

            if total == 0:
                message += '-- CHANCE: 100'
            else:
                message += '-- CHANCE: ' + str(
                    round(chance[song] / total * 100))

        client.send_ooc(
            f'The jukebox has the following songs in it:{message}')


def ooc_cmd_play(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a song.')
    client.area.play_music(arg, client.char_id, -1)
    client.area.add_music_playing(client, arg)
    logger.log_server(
        '[{}][{}]Changed music to {}.'.format(client.area.abbreviation,
                                              client.char_name, arg),
        client)


def ooc_cmd_blockdj(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /blockdj <id>.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must enter a number. Use /blockdj <id>.')
    if not targets:
        raise ArgumentError('Target not found. Use /blockdj <id>.')
    for target in targets:
        target.is_dj = False
        target.send_ooc(
            'A moderator muted you from changing the music.')
        logger.log_mod(
            'BlockDJ\'d {} [{}]({}).'.format(target.char_name, target.id,
                                             target.ip), client)
        target.area.remove_jukebox_vote(target, True)
    client.send_ooc('blockdj\'d {}.'.format(
        targets[0].char_name))


def ooc_cmd_unblockdj(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /unblockdj <id>.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must enter a number. Use /unblockdj <id>.')
    if not targets:
        raise ArgumentError('Target not found. Use /blockdj <id>.')
    for target in targets:
        target.is_dj = True
        target.send_ooc(
            'A moderator unmuted you from changing the music.')
        logger.log_mod(
            'UnblockDJ\'d {} [{}]({}).'.format(target.char_name,
                                               target.id, target.ip),
            client)
    client.send_ooc('Unblockdj\'d {}.'.format(
        targets[0].char_name))
