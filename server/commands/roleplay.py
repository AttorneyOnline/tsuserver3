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
    'ooc_cmd_notecard_check',
    'ooc_cmd_rolla_reload',
    'ooc_cmd_rolla_set',
    'ooc_cmd_rolla',
    'ooc_cmd_coinflip',
    'ooc_cmd_8ball'
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
    roll, num_dice, chosen_max, modifiers, Sum = rtd(arg)

    client.area.broadcast_ooc(f'{client.showname} rolled {roll} out of {chosen_max}.\nThe total sum is {Sum}.')
    database.log_room('roll', client, client.area, message=f'{roll} out of {chosen_max}')


def ooc_cmd_rollp(client, arg):
    """
    Roll a die privately. Same as /roll but the result is only shown to you and the CMs.
    Example: /roll 2d6 +5 would roll two 6-sided die and add 5 to every result.
    Rolls a 1d6 if blank
    X is the number of dice, Y is the maximum value on the die.
    Usage: /rollp [value/XdY] ["+5"/"-5"/"*5"/"/5"]
    """
    roll, num_dice, chosen_max, modifiers, Sum = rtd(arg)

    client.send_ooc(f'[Hidden] You rolled {roll} out of {chosen_max}.\nThe total sum is {Sum}.')

    client.area.broadcast_ooc(f'{client.showname} rolled in secret.')
    for c in client.area.owners:
        c.send_ooc(f'[{client.area.id}]{client.showname} secretly rolled {roll} out of {chosen_max}.')

    database.log_room('rollp', client, client.area, message=f'{roll} out of {chosen_max}')


def ooc_cmd_notecard(client, arg):
    """
    Write a notecard that can only be revealed by a CM.
    Usage: /notecard <message>
    """
    if len(arg) == 0:
        raise ArgumentError('You must specify the contents of the note card.')
    client.area.cards[client.char_name] = arg
    client.area.broadcast_ooc('{} wrote a note card.'.format(
        client.showname))
    database.log_room('notecard', client, client.area)


def ooc_cmd_notecard_clear(client, arg):
    """
    Erase a notecard.
    Usage: /notecard_clear
    """
    try:
        del client.area.cards[client.char_name]
        client.area.broadcast_ooc('{} erased their note card.'.format(
            client.showname))
        database.log_room('notecard_clear', client, client.area)
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


@mod_only(area_owners=True)
def ooc_cmd_notecard_check(client, arg):
    """
    Check all notecards and their owners privately with a message telling others you've done so.
    Usage: /notecard_check
    """
    if len(client.area.cards) == 0:
        raise ClientError('There are no cards to check in this area.')
    msg = 'Note cards in this area:\n'
    for card_owner, card_msg in client.area.cards.items():
        msg += f'{card_owner}: {card_msg}\n'
    client.send_ooc(msg)
    client.area.broadcast_ooc(f'[{client.id}] {client.showname} has checked the notecards in this area.')
    database.log_room('notecard_check', client, client.area)


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
        client.showname, roll, max_roll, ability))
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
        client.showname, flip))
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
    client.area.broadcast_ooc('{} asked a question: "{}" and the answer is: "{}".'.format(
        client.showname, arg, rolla(ability_dice)[2]))
        