import random

import asyncio
import arrow
import datetime
import pytimeparse

from server import database
from server.exceptions import ClientError, ServerError, ArgumentError

from . import mod_only

__all__ = [
    'ooc_cmd_roll',
    'ooc_cmd_rollp',
    'ooc_cmd_notecard',
    'ooc_cmd_notecard_clear',
    'ooc_cmd_notecard_reveal',
    'ooc_cmd_rolla_reload',
    'ooc_cmd_rolla_set',
    'ooc_cmd_rolla',
    'ooc_cmd_coinflip',
    'ooc_cmd_8ball',
    'ooc_cmd_timer'
]


def ooc_cmd_roll(client, arg):
    """
    Roll a die. The result is shown publicly.
    Usage: /roll [max value] [rolls]
    """
    roll_max = 11037
    if len(arg) != 0:
        try:
            val = list(map(int, arg.split(' ')))
            if not 1 <= val[0] <= roll_max:
                raise ArgumentError(
                    f'Roll value must be between 1 and {roll_max}.')
        except ValueError:
            raise ArgumentError(
                'Wrong argument. Use /roll [<max>] [<num of rolls>]')
    else:
        val = [6]
    if len(val) == 1:
        val.append(1)
    if len(val) > 2:
        raise ArgumentError(
            'Too many arguments. Use /roll [<max>] [<num of rolls>]')
    if val[1] > 20 or val[1] < 1:
        raise ArgumentError('Num of rolls must be between 1 and 20')
    roll = ''
    for _ in range(val[1]):
        roll += str(random.randint(1, val[0])) + ', '
    roll = roll[:-2]
    if val[1] > 1:
        roll = '(' + roll + ')'
    client.area.broadcast_ooc('{} rolled {} out of {}.'.format(
        client.char_name, roll, val[0]))
    database.log_room('roll', client, client.area, message=f'{roll} out of {val[0]}')


def ooc_cmd_rollp(client, arg):
    """
    Roll a die privately.
    Usage: /roll [max value] [rolls]
    """
    roll_max = 11037
    if len(arg) != 0:
        try:
            val = list(map(int, arg.split(' ')))
            if not 1 <= val[0] <= roll_max:
                raise ArgumentError(
                    f'Roll value must be between 1 and {roll_max}.')
        except ValueError:
            raise ArgumentError(
                'Wrong argument. Use /rollp [<max>] [<num of rolls>]')
    else:
        val = [6]
    if len(val) == 1:
        val.append(1)
    if len(val) > 2:
        raise ArgumentError(
            'Too many arguments. Use /rollp [<max>] [<num of rolls>]')
    if val[1] > 20 or val[1] < 1:
        raise ArgumentError('Num of rolls must be between 1 and 20')
    roll = ''
    for _ in range(val[1]):
        roll += str(random.randint(1, val[0])) + ', '
    roll = roll[:-2]
    if val[1] > 1:
        roll = '(' + roll + ')'
    client.send_ooc('{} rolled {} out of {}.'.format(
        client.char_name, roll, val[0]))

    client.area.broadcast_ooc('{} rolled in secret.'.format(
        client.char_name))
    for c in client.area.owners:
        c.send_ooc('[{}]{} secretly rolled {} out of {}.'.format(
            client.area.abbreviation, client.char_name, roll, val[0]))

    database.log_room('rollp', client, client.area, message=f'{roll} out of {val[0]}')


def ooc_cmd_notecard(client, arg):
    """
    Write a notecard that can only be revealed by a CM.
    Usage: /notecard <message>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify the contents of the note card.')
    client.area.cards[client.char_name] = arg
    client.area.broadcast_ooc('{} wrote a note card.'.format(
        client.char_name))
    database.log_room('notecard', client, client.area)


def ooc_cmd_notecard_clear(client, arg):
    """
    Erase a notecard.
    Usage: /notecard_clear
    """
    try:
        del client.area.cards[client.char_name]
        client.area.broadcast_ooc('{} erased their note card.'.format(
            client.char_name))
        database.log_room('notecard_erase', client, client.area)
    except KeyError:
        raise ClientError('You do not have a note card.')


@mod_only(area_owners=True)
def ooc_cmd_notecard_reveal(client, arg):
    """
    Reveal all notecards and their owners.
    Usage: /notecard_reveal
    """
    if len(client.area.cards) == 0:
        raise ClientError('There are no cards to reveal in this area.')
    msg = 'Note cards have been revealed.\n'
    for card_owner, card_msg in client.area.cards.items():
        msg += f'{card_owner}: {card_msg}\n'
    client.area.cards.clear()
    client.area.broadcast_ooc(msg)
    database.log_room('notecard_reveal', client, client.area)


@mod_only()
def ooc_cmd_rolla_reload(client, arg):
    """
    Reload ability dice sets from a configuration file.
    Usage: /rolla_reload
    """
    rolla_reload(client.area)
    client.send_ooc('Reloaded ability dice configuration.')
    database.log_room('rolla_reload', client, client.area)


def rolla_reload(area):
    try:
        import yaml
        with open('config/dice.yaml', 'r') as dice:
            area.ability_dice = yaml.safe_load(dice)
    except:
        raise ServerError(
            'There was an error parsing the ability dice configuration. Check your syntax.'
        )


def ooc_cmd_rolla_set(client, arg):
    """
    Choose the set of ability dice to roll.
    Usage: /rolla_set <name>
    """
    if not hasattr(client.area, 'ability_dice'):
        rolla_reload(client.area)
    available_sets = ', '.join(client.area.ability_dice.keys())
    if len(arg) == 0:
        raise ArgumentError(
            f'You must specify the ability set name.\nAvailable sets: {available_sets}'
        )
    elif arg not in client.area.ability_dice:
        raise ArgumentError(
            f'Invalid ability set \'{arg}\'.\nAvailable sets: {available_sets}'
        )
    client.ability_dice_set = arg
    client.send_ooc(f"Set ability set to {arg}.")


def rolla(ability_dice):
    max_roll = ability_dice['max'] if 'max' in ability_dice else 6
    roll = random.randint(1, max_roll)
    ability = ability_dice[roll] if roll in ability_dice else "Nothing happens."
    return (roll, max_roll, ability)


def ooc_cmd_rolla(client, arg):
    """
    Roll a specially labeled set of dice (ability dice).
    Usage: /rolla
    """
    if not hasattr(client.area, 'ability_dice'):
        rolla_reload(client.area)
    if not hasattr(client, 'ability_dice_set'):
        raise ClientError(
            'You must set your ability set using /rolla_set <name>.')
    ability_dice = client.area.ability_dice[client.ability_dice_set]
    roll, max_roll, ability = rolla(ability_dice)
    client.area.broadcast_ooc('{} rolled a {} (out of {}): {}.'.format(
        client.char_name, roll, max_roll, ability))
    database.log_room('rolla', client, client.area,
                        message=f'{roll} out of {max_roll}: {ability}')


def ooc_cmd_coinflip(client, arg):
    """
    Flip a coin. The result is shown publicly.
    Usage: /coinflip
    """
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    coin = ['heads', 'tails']
    flip = random.choice(coin)
    client.area.broadcast_ooc('{} flipped a coin and got {}.'.format(
        client.char_name, flip))
    database.log_room('coinflip', client, client.area, message=flip)


def ooc_cmd_8ball(client, arg):
    """
    Answers a question. The result is shown publicly.
    Usage: /8ball <question>
    """
    
    arg = arg.strip()
    if len(arg) == 0:
        raise ArgumentError('You need to ask a question')
    rolla_reload(client.area)
    ability_dice = client.area.ability_dice['8ball']
    client.area.broadcast_ooc('{} asked a question: {} and the answer is: {}.'.format(
        client.char_name, arg, rolla(ability_dice)[2]))

def ooc_cmd_timer(client, arg):
    """
    Manage a countdown timer in the current area. Note that timer of ID 0 is global.
    All other timer IDs are local to the area (valid IDs are 1 - 4).
    Usage:
    /timer <id> [+/-][time]
        Set the timer's time, optionally adding or subtracting time. If the timer had
        not been previously set up, it will be shown paused.
    /timer <id> start
    /timer <id> <pause|stop>
    /timer <id> hide
    """

    arg = arg.split()
    if len(arg) < 1:
        msg = 'Currently active timers:'
        # Global timer
        timer = client.server.area_manager.timer
        if timer.set:
            if timer.started:
                msg += f'\nTimer 0 is at {timer.target - arrow.get()}'
            else:
                msg += f'\nTimer 0 is at {timer.static}'
        # Area timers
        for timer_id, timer in enumerate(client.area.timers):
            if timer.set:
                if timer.started:
                    msg += f'\nTimer {timer_id+1} is at {timer.target - arrow.get()}'
                else:
                    msg += f'\nTimer {timer_id+1} is at {timer.static}'
        client.send_ooc(msg)
        return

    # TI packet specification:
    # TI#TimerID#Type#Value#%
    # TimerID = from 0 to 4 (5 possible timers total)
    # Type 0 = start/resume/sync timer at time
    # Type 1 = pause timer at time
    # Type 2 = show timer
    # Type 3 = hide timer
    # Value = Time to set on the timer

    try:
        timer_id = int(arg[0])
    except:
        raise ArgumentError('Invalid ID. Usage: /timer <id>')

    if timer_id < 0 or timer_id > 4:
        raise ArgumentError('Invalid ID. Usage: /timer <id>')
    if timer_id == 0:
        timer = client.server.area_manager.timer
    else:
        timer = client.area.timers[timer_id-1]

    if len(arg) < 2:
        if timer.set:
            if timer.started:
                client.send_ooc(f'Timer {timer_id} is at {timer.target - arrow.get()}')
            else:
                client.send_ooc(f'Timer {timer_id} is at {timer.static}')
        else:
            client.send_ooc(f'Timer {timer_id} is unset.')
        return

    if client not in client.area.owners and not client.is_mod:
        raise ArgumentError('Only CMs or mods can modify timers. Usage: /timer <id>')
    if timer_id == 0 and not client.is_mod:
        raise ArgumentError('Only mods can set the global timer. Usage: /timer <id>')

    duration = pytimeparse.parse(''.join(arg[1:]))
    if duration is not None:
        if timer.set:
            if timer.started:
                if not (arg[1] == '+' or duration < 0):
                    timer.target = arrow.get()
                timer.target = timer.target.shift(seconds=duration)
                timer.static = timer.target - arrow.get()
            else:
                if not (arg[1] == '+' or duration < 0):
                    timer.static = datetime.timedelta(0)
                timer.static += datetime.timedelta(seconds=duration)
        else:
            timer.static = datetime.timedelta(seconds=abs(duration))
            timer.set = True
            if timer_id == 0:
                client.server.send_all_cmd_pred('TI', timer_id, 2)
            else:
                client.area.send_command('TI', timer_id, 2)

    if not timer.set:
        raise ArgumentError(f'Timer {timer_id} is not set in this area.')
    elif arg[1] == 'start':
        timer.target = timer.static + arrow.get()
        timer.started = True
        client.send_ooc(f'Starting timer {timer_id}.')
        database.log_room('timer.start', client, client.area, message=str(timer_id))
    elif arg[1] in ('pause', 'stop'):
        timer.static = timer.target - arrow.get()
        timer.started = False
        client.send_ooc(f'Stopping timer {timer_id}.')
        database.log_room('timer.stop', client, client.area, message=str(timer_id))
    elif arg[1] in ('unset', 'hide'):
        timer.set = False
        timer.started = False
        timer.static = None
        timer.target = None
        client.send_ooc(f'Timer {timer_id} unset and hidden.')
        database.log_room('timer.hide', client, client.area, message=str(timer_id))
        if timer_id == 0:
            client.server.send_all_cmd_pred('TI', timer_id, 3)
        else:
            client.area.send_command('TI', timer_id, 3)

    # Send static time if applicable
    if timer.set:
        s = int(not timer.started)
        static_time = int(timer.static.total_seconds()) * 1000

        if timer_id == 0:
            client.server.send_all_cmd_pred('TI', timer_id, s, static_time)
        else:
            client.area.send_command('TI', timer_id, s, static_time)

        client.send_ooc(f'Timer {timer_id} is at {timer.static}')

        target = client.area
        if timer_id == 0:
            target = client.server.area_manager

        def timer_expired():
            if timer.schedule:
                timer.schedule.cancel()
            # Area was destroyed at some point
            if target is None or timer is None:
                return
            target.broadcast_ooc(f'Timer {timer_id} has expired.')
            timer.static = datetime.timedelta(0)
            timer.started = False
            database.log_room('timer.expired', None, target, message=str(timer_id))

        if timer.schedule:
            timer.schedule.cancel()
        if timer.started:
            timer.schedule = asyncio.get_event_loop().call_later(
                int(timer.static.total_seconds()), timer_expired)
