import random

import asyncio
import arrow
import datetime
import pytimeparse

from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ServerError, ArgumentError

from . import mod_only
from .. import commands

__all__ = [
    'ooc_cmd_roll',
    'ooc_cmd_rollp',
    'ooc_cmd_notecard',
    'ooc_cmd_notecard_clear',
    'ooc_cmd_notecard_reveal',
    'ooc_cmd_notecard_check',
    'ooc_cmd_vote',
    'ooc_cmd_vote_clear',
    'ooc_cmd_vote_reveal',
    'ooc_cmd_vote_check',
    'ooc_cmd_rolla_reload',
    'ooc_cmd_rolla_set',
    'ooc_cmd_rolla',
    'ooc_cmd_coinflip',
    'ooc_cmd_8ball',
    'ooc_cmd_timer'
]


def rtd(arg):
    DICE_MAX = 11037
    NUMDICE_MAX = 20
    MODIFIER_LENGTH_MAX = 12 #Change to a higher at your own risk
    ACCEPTABLE_IN_MODIFIER = '1234567890+-*/().r'
    MAXDIVZERO_ATTEMPTS = 10
    MAXACCEPTABLETERM = DICE_MAX*10 #Change to a higher number at your own risk

    special_calculation = False
    args = arg.split(' ')
    arg_length = len(args)
    
    if arg != '':
        if arg_length == 2:
            dice_type, modifiers = args
            if len(modifiers) > MODIFIER_LENGTH_MAX:
                raise ArgumentError('The given modifier is too long to compute. Please try a shorter one')
        elif arg_length == 1:
            dice_type, modifiers = arg, ''
        else:
             raise ArgumentError('This command takes one or two arguments. Use /roll [<num of rolls>]d[<max>] [modifiers]')

        dice_type = dice_type.split('d')
        if len(dice_type) == 1:
            dice_type.insert(0,1)
        if dice_type[0] == '':
            dice_type[0] = '1'
            
        try:
            num_dice,chosen_max = int(dice_type[0]),int(dice_type[1])
        except ValueError:
            raise ArgumentError('Expected integer value for number of rolls and max value of dice')

        if not 1 <= num_dice <= NUMDICE_MAX: 
            raise ArgumentError('Number of rolls must be between 1 and {}'.format(NUMDICE_MAX))
        if not 1 <= chosen_max <= DICE_MAX:
            raise ArgumentError('Dice value must be between 1 and {}'.format(DICE_MAX))
            
        for char in modifiers:
            if char not in ACCEPTABLE_IN_MODIFIER:
                raise ArgumentError('Expected numbers and standard mathematical operations in modifier')
            if char == 'r':
                special_calculation = True
        if '**' in modifiers: #Exponentiation manually disabled, it can be pretty dangerous
            raise ArgumentError('Expected numbers and standard mathematical operations in modifier')
    else:
        num_dice,chosen_max,modifiers = 1,6,'' #Default

    roll = ''
    Sum = 0
    
    for i in range(num_dice):
        divzero_attempts = 0
        while True:
            raw_roll = str(random.randint(1, chosen_max))
            if modifiers == '':
                aux_modifier = ''
                mid_roll = int(raw_roll)
            else:
                if special_calculation:
                    aux_modifier = modifiers.replace('r',raw_roll)+'='
                elif modifiers[0].isdigit():
                    aux_modifier = raw_roll+"+"+modifiers+'='
                else:
                    aux_modifier = raw_roll+modifiers+'='
                
                #Prevent any terms from reaching past MAXACCEPTABLETERM in order to prevent server lag due to potentially frivolous dice rolls
                aux = aux_modifier[:-1]
                for i in "+-*/()":
                    aux = aux.replace(i,"!")
                aux = aux.split('!')
                for i in aux:
                    try:
                        if i != '' and round(float(i)) > MAXACCEPTABLETERM:
                            raise ArgumentError("Given mathematical formula takes numbers past the server's computation limit")
                    except ValueError:
                        raise ArgumentError('Given mathematical formula has a syntax error and cannot be computed')
                        
                try: 
                    mid_roll = round(eval(aux_modifier[:-1])) #By this point it should be 'safe' to run eval
                except SyntaxError:
                    raise ArgumentError('Given mathematical formula has a syntax error and cannot be computed')
                except TypeError: #Deals with inputs like 3(r-1)
                    raise ArgumentError('Given mathematical formula has a syntax error and cannot be computed')
                except ZeroDivisionError:
                    divzero_attempts += 1
                    if divzero_attempts == MAXDIVZERO_ATTEMPTS:
                        raise ArgumentError('Given mathematical formula produces divisions by zero too often and cannot be computed')
                    continue
            break

        final_roll = mid_roll #min(chosen_max,max(1,mid_roll))
        Sum += final_roll
        if final_roll != mid_roll:
            final_roll = "|"+str(final_roll) #This visually indicates the roll was capped off due to exceeding the acceptable roll range
        else:
            final_roll = str(final_roll)
        if modifiers != '':
            roll += str(raw_roll+':')
        roll += str(aux_modifier+final_roll) + ', '
    roll = roll[:-2]
    if num_dice > 1:
        roll = '(' + roll + ')'
    
    return roll, num_dice, chosen_max, modifiers, Sum


def ooc_cmd_roll(client, arg):
    """
    Roll a die. The result is shown publicly.
    Example: /roll 2d6 +5 would roll two 6-sided die and add 5 to every result.
    Rolls a 1d6 if blank
    X is the number of dice, Y is the maximum value on the die.
    Usage: /rollp [value/XdY] ["+5"/"-5"/"*5"/"/5"]
    """
    roll, num_dice, chosen_max, _modifiers, Sum = rtd(arg)

    client.area.broadcast_ooc(f'{client.showname} rolled {roll} out of {chosen_max}.' + (f'\nThe total sum is {Sum}.' if num_dice > 1 else ''))
    database.log_area('roll', client, client.area, message=f'{roll} out of {chosen_max}')


def ooc_cmd_rollp(client, arg):
    """
    Roll a die privately. Same as /roll but the result is only shown to you and the CMs.
    Example: /roll 2d6 +5 would roll two 6-sided die and add 5 to every result.
    Rolls a 1d6 if blank
    X is the number of dice, Y is the maximum value on the die.
    Usage: /rollp [value/XdY] ["+5"/"-5"/"*5"/"/5"]
    """
    roll, num_dice, chosen_max, _modifiers, Sum = rtd(arg)

    client.send_ooc(f'[Hidden] You rolled {roll} out of {chosen_max}.' + (f'\nThe total sum is {Sum}.' if num_dice > 1 else ''))
    for c in client.area.owners:
        c.send_ooc(f'[{client.area.id}]{client.showname} secretly rolled {roll} out of {chosen_max}.')

    database.log_area('rollp', client, client.area, message=f'{roll} out of {chosen_max}')


def ooc_cmd_notecard(client, arg):
    """
    Write a notecard that can only be revealed by a CM.
    Usage: /notecard <message>
    """
    if len(arg) == 0:
        if client.char_name in client.area.cards:
            client.send_ooc(f'Your current notecard is {client.area.cards[client.char_name]}. Usage: /notecard <message>')
        else:
            client.send_ooc('No notecard found. Usage: /notecard <message>')
        return
    client.area.cards[client.char_name] = arg
    client.area.broadcast_ooc('{} wrote a note card.'.format(
        client.showname))
    database.log_area('notecard', client, client.area)


@mod_only(area_owners=True)
def ooc_cmd_notecard_clear(client, arg):
    """
    Clear all notecards as a CM.
    Usage: /notecard_clear
    """
    client.area.cards.clear()
    client.area.broadcast_ooc(f'[{client.id}] {client.showname} has cleared all the note cards in this area.')
    database.log_area('notecard_clear', client, client.area)


@mod_only(area_owners=True)
def ooc_cmd_notecard_reveal(client, arg):
    """
    Reveal all notecards and their owners.
    Usage: /notecard_reveal
    """
    if len(client.area.cards) == 0:
        raise ClientError('There are no cards to reveal in this area.')
    msg = 'Note cards have been revealed:'
    for card_owner, card_msg in client.area.cards.items():
        msg += f'\n{card_owner}: {card_msg}'
    client.area.broadcast_ooc(msg)
    client.send_ooc('Use /notecard_clear for clearing.')
    database.log_area('notecard_reveal', client, client.area)


@mod_only(area_owners=True)
def ooc_cmd_notecard_check(client, arg):
    """
    Check all notecards and their owners privately with a message telling others you've done so.
    Usage: /notecard_check
    """
    if len(client.area.cards) == 0:
        raise ClientError('There are no cards to check in this area.')
    client.area.broadcast_ooc(f'[{client.id}] {client.showname} has checked the notecards in this area.')
    msg = 'Note cards in this area:'
    for card_owner, card_msg in client.area.cards.items():
        msg += f'\n{card_owner}: {card_msg}'
    client.send_ooc(msg)
    client.send_ooc('Use /notecard_clear for clearing, or /notecard_reveal to reveal the results publicly.')
    database.log_area('notecard_check', client, client.area)


def ooc_cmd_vote(client, arg):
    """
    Cast a vote for a particular user that can only be revealed by a CM.
    Usage: /vote <id>
    """
    args = arg.split()
    if len(args) == 0:
        raise ArgumentError('Please provide a client ID. Usage: /vote <id>.')
    if client.char_name in [y for x in client.area.votes.values() for y in x]:
        raise ArgumentError('You already cast your vote! Wait on the CM to /vote_clear.')
    target = client.server.client_manager.get_targets(client, TargetType.ID,
                                                            int(args[0]), False)[0]
    client.area.votes.setdefault(target.char_name, []).append(client.char_name)
    client.area.broadcast_ooc(f'[{client.id}] {client.showname} cast a vote.')
    database.log_area('vote', client, client.area)


@mod_only(area_owners=True)
def ooc_cmd_vote_clear(client, arg):
    """
    Clear all votes as a CM.
    Include [char_folder] (case-sensitive) to only clear a specific voter.
    Usage: /vote_clear [char_folder]
    """
    if arg != "":
        for value in client.area.votes.values():
            if arg in value:
                value.remove(arg)
                client.area.broadcast_ooc(f"[{client.id}] {client.showname} has cleared {arg}'s vote.")
                return
        raise ClientError(f'No vote was cast by {arg}! (This is case-sensitive - are you sure you spelt the voter character folder right?)')
    client.area.votes.clear()
    client.area.broadcast_ooc(f'[{client.id}] {client.showname} has cleared all the votes in this area.')
    database.log_area('vote_clear', client, client.area)


def get_vote_results(votes):
    # Sort the votes, starting from the least votes ending with the most votes. Note that x[1] is a list of voters, hence the len().
    votes = sorted(votes.items(), key = lambda x: len(x[1]))
    msg = ""
    # Iterating through the votes...
    for key, value in votes:
        # Create a comma-separated list of people who voted for this person
        voters = ', '.join(value)
        num = len(value)
        s = 's' if num > 1 else ''
        msg += f'\n{num} vote{s} for {key} - voted by {voters}.'

    # Get the maximum amount of votes someone received
    mx = len(votes[len(votes)-1][1])
    # Determine a list of winners - usually it's just one winner, but there's multiple if it's a tie.
    winners = [k for k, v in votes if len(v) == mx]

    # If we have a tie...
    if len(winners) > 1:
        # Create a comma-separated list of winners
        tied = ', '.join(winners)
        # Display.
        msg += f'\n{tied} have tied for most votes.'
    else:
        # Display the sole winner.
        msg += f'\n{winners[0]} has most votes.'
    return msg


@mod_only(area_owners=True)
def ooc_cmd_vote_reveal(client, arg):
    """
    Reveal the number of votes, the voters and those with the highest amount of votes.
    Usage: /vote_reveal
    """
    if len(client.area.votes) == 0:
        raise ClientError('There are no votes to reveal in this area.')
    msg = 'Votes have been revealed:'
    msg += get_vote_results(client.area.votes)
    client.area.broadcast_ooc(msg)
    client.send_ooc('Use /vote_clear for clearing.')
    database.log_area('vote_reveal', client, client.area)


@mod_only(area_owners=True)
def ooc_cmd_vote_check(client, arg):
    """
    Check the number of votes, the voters and those with the highest amount of votes privately with a message telling others you've done so.
    Usage: /vote_check
    """
    if len(client.area.votes) == 0:
        raise ClientError('There are no votes to check in this area.')
    client.area.broadcast_ooc(f'[{client.id}] {client.showname} has checked the votes in this area.')
    msg = 'Votes in this area:'
    msg += get_vote_results(client.area.votes)
    client.send_ooc(msg)
    client.send_ooc('Use /vote_clear for clearing, or /vote_reveal to reveal the results publicly.')
    database.log_area('vote_check', client, client.area)


@mod_only()
def ooc_cmd_rolla_reload(client, arg):
    """
    Reload ability dice sets from a configuration file.
    Usage: /rolla_reload
    """
    rolla_reload(client.area)
    client.send_ooc('Reloaded ability dice configuration.')
    database.log_area('rolla_reload', client, client.area)


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
        client.showname, roll, max_roll, ability))
    database.log_area('rolla', client, client.area,
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
        client.showname, flip))
    database.log_area('coinflip', client, client.area, message=flip)


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
    client.area.broadcast_ooc(f'{client.showname} asked the 8ball - "{arg}", and it responded: "{rolla(ability_dice)[2]}".')

def ooc_cmd_timer(client, arg):
    """
    Manage a countdown timer in the current area. Note that timer of ID `0` is hub-wide. All other timer ID's are local to area.
    Anyone can check ongoing timers, their status and time left using `/timer <id>`, so `/timer 0`.
    `[time]` can be formated as `10m5s` for 10 minutes 5 seconds, `1h30m` for 1 hour 30 minutes, etc.
    You can optionally add or subtract time, like so: `/timer 0 +5s` to add `5` seconds to timer id `0`.
    `start` starts the previously set timer, so `/timer 0 start`.
    `pause` OR `stop` pauses the timer that's currently running, so `/timer 0 pause`.
    `unset` OR `hide` hides the timer for it to no longer show up, so `/timer 0 hide`.
    Usage:
    /timer <id> [+][time]
    /timer <id> start
    /timer <id> <pause|stop>
    /timer <id> hide
    /timer <id> /
    """

    arg = arg.split()
    if len(arg) < 1:
        msg = 'Currently active timers:'
        # Hub timer
        timer = client.area.area_manager.timer
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
    timer_id = int(arg[0])
    if timer_id < 0 or timer_id > 20:
        raise ArgumentError('Invalid ID. Usage: /timer <id>')
    if timer_id == 0:
        timer = client.area.area_manager.timer
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

    if not (client in client.area.owners) and not client.is_mod:
        raise ArgumentError('Only CMs or GMs can modify timers. Usage: /timer <id>')
    if timer_id == 0 and not (client in client.area.area_manager.owners) and not client.is_mod:
        raise ArgumentError('Only GMs can set hub-wide timer ID 0. Usage: /timer <id>')

    duration = pytimeparse.parse(''.join(arg[1:]))
    if duration is not None:
        if timer.set:
            if timer.started:
                if not (arg[1] == '+' or arg[1][0] == '+' or duration < 0):
                    timer.target = arrow.get()
                timer.target = timer.target.shift(seconds=duration)
                timer.static = timer.target - arrow.get()
            else:
                if not (arg[1] == '+' or arg[1][0] == '+' or duration < 0):
                    timer.static = datetime.timedelta(0)
                timer.static += datetime.timedelta(seconds=duration)
        else:
            timer.static = datetime.timedelta(seconds=abs(duration))
            timer.set = True
            if timer_id == 0:
                client.area.area_manager.send_command('TI', timer_id, 2)
            else:
                client.area.send_command('TI', timer_id, 2)

    if not timer.set:
        raise ArgumentError(f'Timer {timer_id} is not set in this area.')

    if arg[1] == 'start' and not timer.started:
        timer.target = timer.static + arrow.get()
        timer.started = True
        client.send_ooc(f'Starting timer {timer_id}.')
    elif arg[1] in ('pause', 'stop') and timer.started:
        timer.static = timer.target - arrow.get()
        timer.started = False
        client.send_ooc(f'Stopping timer {timer_id}.')
    elif arg[1] in ('unset', 'hide'):
        timer.set = False
        timer.started = False
        timer.static = None
        timer.target = None
        client.send_ooc(f'Timer {timer_id} unset and hidden.')
        if timer_id == 0:
            client.area.area_manager.send_command('TI', timer_id, 3)
        else:
            client.area.send_command('TI', timer_id, 3)
    elif arg[1][0] == '/':
        full = ' '.join(arg[1:])[1:]
        if full == '':
            txt = f'Timer {timer_id} commands:'
            for command in timer.commands:
                txt += f'  \n/{command}'
            txt += '\nThey will be called once the timer expires.'
            client.send_ooc(txt)
            return
        if full.lower() == 'clear':
            timer.commands.clear()
            client.send_ooc(f'Clearing all commands for Timer {timer_id}.')
            return

        cmd = full.split(' ')[0]
        called_function = f'ooc_cmd_{cmd}'
        if len(client.server.command_aliases) > 0 and not hasattr(commands, called_function):
            if cmd in client.server.command_aliases:
                called_function = f'ooc_cmd_{client.server.command_aliases[cmd]}'
        if not hasattr(commands, called_function):
            client.send_ooc(f'[Timer {timer_id}] Invalid command: {cmd}. Use /help to find up-to-date commands.')
            return
        timer.commands.append(full)
        client.send_ooc(f'Adding command to Timer {timer_id}: /{full}')
        return

    # Send static time if applicable
    if timer.set:
        s = int(not timer.started)
        static_time = int(timer.static.total_seconds()) * 1000
        if timer_id == 0:
            client.area.area_manager.send_command('TI', timer_id, s, static_time)
        else:
            client.area.send_command('TI', timer_id, s, static_time)
        client.send_ooc(f'Timer {timer_id} is at {timer.static}')

        if timer_id == 0:
            timer.hub = client.area.area_manager
        else:
            timer.area = client.area

        timer.caller = client
        if timer.schedule:
            timer.schedule.cancel()
        if timer.started:
            timer.schedule = asyncio.get_event_loop().call_later(
                int(timer.static.total_seconds()), timer.timer_expired)
