import random

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
	'ooc_cmd_nat20',
	'ooc_cmd_smellanto',
	'ooc_cmd_broadcast'
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



def ooc_cmd_notecard_reveal(client, arg):
    """
    Reveal all notecards and their owners.
    Usage: /notecard_reveal
    """
    if not client in client.area.owners:
        raise ClientError('Only CM can reveal notecards.')
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
    max_roll = ability_dice['max'] if 'max' in ability_dice else 6
    roll = random.randint(1, max_roll)
    ability = ability_dice[roll] if roll in ability_dice else "Nothing happens"
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
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    coin = ['yes', 'no', 'maybe', 'I dont know', 'perhaps', 'please do not', 'try again', 'you shouldn\'t ask that', 'god no']
    flip = random.choice(coin)
    client.area.broadcast_ooc('The magic 8 ball says {}.'.format(flip))
    database.log_room('8ball', client, client.area)

@mod_only()
def ooc_cmd_nat20(client, arg):
    """
    Roll a die. The result is shown publicly.
    Usage: /roll [max value] [rolls]
    """
    if len(arg) != 0:
        raise ArgumentError(
                'This command takes no arguments')
    else:
        client.area.broadcast_ooc('{} rolled 20 out of 20.'.format(
            client.char_name))

@mod_only()
def ooc_cmd_smellanto(client, arg):
    """
    Roll a die. The result is shown publicly.
    Usage: /roll [max value] [rolls]
    """
    if len(arg) != 0:
        raise ArgumentError(
                'This command takes no arguments')
    else:
        client.area.broadcast_ooc('smellanto')

@mod_only()
def ooc_cmd_broadcast(client, arg):
    """
    Roll a die. The result is shown publicly.
    Usage: /roll [max value] [rolls]
    """
    if len(arg) == 0:
        raise ArgumentError(
                'This command takes arguments')
    else:
        client.area.broadcast_ooc(arg)
