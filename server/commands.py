# tsuserver3, an Attorney Online server
#
# Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import random
import hashlib
import string
import time

from server.constants import TargetType
import re
import os

from server import logger
from server.constants import TargetType
from server.exceptions import ClientError, ServerError, ArgumentError, AreaError
from server.pastebin_api import paste_it

# possible keys: ip, OOC, id, cname, ipid, hdid

# def ooc_cmd_a(client, arg):
#     if len(arg) == 0:
#         raise ArgumentError('You must specify an area.')
#     arg = arg.split(' ')

#     try:
#         area = client.server.hub_manager.get_area_by_id(int(arg[0]))
#     except AreaError:
#         raise

#     message_areas_cm(client, [area], ' '.join(arg[1:]))


# def ooc_cmd_s(client, arg):
#     areas = []
#     for a in client.server.area_manager.areas:
#         if client in a.owners:
#             areas.append(a)
#     if not areas:
#         client.send_host_message('You aren\'t a CM in any area!')
#         return
#     message_areas_cm(client, areas, arg)


# def message_areas_cm(client, areas, message):
#     for a in areas:
#         if not client in a.owners:
#             client.send_host_message('You are not a CM in {}!'.format(a.name))
#             return
#         a.send_command('CT', client.name, message)
#         a.send_owner_command('CT', client.name, message)


def ooc_cmd_switch(client, arg):
    if len(arg) == 0:
        raise ArgumentError('You must specify a character name.')
    try:
        cid = client.server.get_char_id_by_name(arg)
    except ServerError:
        raise
    try:
        client.change_character(cid)
    except ClientError:
        raise
    client.send_host_message('Character changed.')


def ooc_cmd_bg(client, arg):
    if client.hub.status.lower().startswith('rp-strict') and not client.is_mod and not client.is_cm:
        raise AreaError(
            'Hub is {} - only the CM or mods can change /bg.'.format(client.hub.status))
    if len(arg) == 0:
        raise ArgumentError('You must specify a name. Use /bg <background>.')
    if not client.is_mod and not client.is_cm and client.area.bg_lock == True:
        raise AreaError("This area's background is locked")
    try:
        client.area.change_background(arg, client.is_mod)
    except AreaError:
        raise
    client.area.send_host_message('[{}]{} changed the background to {}.'.format(client.id, client.get_char_name(True), arg))
    logger.log_server('Changed background to {}'.format(arg), client)

def ooc_cmd_bglock(client,arg):
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    if client.area.bg_lock  == True:
        client.area.bg_lock = False
    else:
        client.area.bg_lock = True
    client.area.send_host_message('A mod has set the background lock to {}.'.format(client.area.bg_lock))
    logger.log_server('Changed bglock to {}'.format(client.area.bg_lock), client)

def ooc_cmd_evidence_mod(client, arg):
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')
    if not arg:
        client.send_host_message('current evidence mod: {}'.format(client.area.evidence_mod))
        return
    if arg in ['FFA', 'Mods', 'CM', 'HiddenCM']:
        if arg == client.area.evidence_mod:
            client.send_host_message('current evidence mod: {}'.format(client.area.evidence_mod))
            return
        if client.area.evidence_mod == 'HiddenCM':
            for i in range(len(client.area.evi_list.evidences)):
                client.area.evi_list.evidences[i].pos = 'all'
        client.area.evidence_mod = arg
        client.send_host_message('current evidence mod: {}'.format(client.area.evidence_mod))
        return
    else:
        raise ArgumentError('Wrong Argument. Use /evidence_mod <MOD>. Possible values: FFA, CM, Mods, HiddenCM')
        return

def ooc_cmd_allow_iniswap(client, arg):
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')
    client.hub.iniswap_allowed = not client.hub.iniswap_allowed
    answer = {True: 'allowed', False: 'forbidden'}
    client.send_host_message('iniswap is {}.'.format(answer[client.hub.iniswap_allowed]))
    return

def ooc_cmd_allow_blankposting(client, arg):
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')
    client.hub.blankposting_allowed = not client.hub.blankposting_allowed
    answer = {True: 'allowed', False: 'forbidden'}
    client.hub.send_host_message(
        '{} [{}] has set blankposting in the hub to {}.'.format(client.name, client.id,
                                                                 answer[client.hub.blankposting_allowed]))
    return

def ooc_cmd_allow_shownames(client, arg):
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')
    client.hub.showname_changes_allowed = not client.hub.showname_changes_allowed
    answer = {True: 'allowed', False: 'forbidden'}
    client.hub.send_host_message(
        '{} [{}] has set showname changing in the hub to {}.'.format(client.name, client.id,
                                                                 answer[client.hub.showname_changes_allowed]))
    return

def ooc_cmd_allow_shouts(client, arg):
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')
    client.hub.shouts_allowed = not client.hub.shouts_allowed
    answer = {True: 'allowed', False: 'forbidden'}
    client.hub.send_host_message('{} [{}] has set interjections in the hub to {}.'.format(client.name, client.id,
                                                                                answer[client.hub.non_int_pres_only]))
    return

def ooc_cmd_force_nonint_pres(client, arg):
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')
    client.hub.non_int_pres_only = not client.hub.non_int_pres_only
    answer = {True: 'non-interrupting only', False: 'non-interrupting or interrupting as you choose'}
    client.hub.send_host_message('{} [{}] has set pres in the hub to be {}.'.format(client.name, client.id,
                                                                                      answer[
                                                                                          client.hub.non_int_pres_only]))
    return

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
    
    return roll, num_dice, chosen_max, modifiers
    
def ooc_cmd_roll(client, arg):
    roll, num_dice, chosen_max, modifiers = rtd(arg)

    client.area.send_host_message('[{}]{} rolled {} out of {}.'.format(
        client.id, client.get_char_name(True), roll, chosen_max))
    client.hub.send_to_cm('RollLog', '[{}][{}]{} used /roll and got {} out of {}.'.format(
        client.area.id, client.id, client.get_char_name(True), roll, chosen_max), client)
    logger.log_server('Used /roll and got {} out of {}.'.format(roll, chosen_max), client)
    
def ooc_cmd_rollp(client, arg):
    roll, num_dice, chosen_max, modifiers = rtd(arg)

    client.send_host_message('[Hidden] You rolled {} out of {}.'.format(roll, chosen_max))
    client.hub.send_to_cm('RollLog', '[A{}][ID{}]{} used /rollp and got {} out of {}.'.format(client.area.id, client.id, client.get_char_name(True), roll, chosen_max), client)
    logger.log_server('Used /rollp and got {} out of {}.'.format(roll, chosen_max), client)

def ooc_cmd_currentmusic(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    if client.area.current_music == '':
        raise ClientError('There is no music currently playing.')
    if client.is_mod:
        client.send_host_message('The current music is {} and was played by {} ({}).'.format(client.area.current_music,
                                                                                             client.area.current_music_player,
                                                                                             client.area.current_music_player_ipid))
    else:
        client.send_host_message('The current music is {} and was played by {}.'.format(client.area.current_music,
                                                                                        client.area.current_music_player))

def ooc_cmd_coinflip(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    coin = ['heads', 'tails']
    flip = random.choice(coin)
    client.area.send_host_message(
        '[{}]{} flipped a coin and got {}.'.format(client.id, client.get_char_name(True), flip))
    client.hub.send_to_cm('RollLog', '[A{}][ID{}]{} used /coinflip and got {}.'.format(
        client.area.id, client.id, client.get_char_name(True), flip), client)
    logger.log_server('Used /coinflip and got {}.'.format(flip), client)


def ooc_cmd_motd(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.send_motd()


def ooc_cmd_pos(client, arg):
    if client.area.pos_lock:
        raise ClientError('Positions are locked in this area.')
    if len(arg) == 0:
        client.change_position()
        client.send_host_message('Position reset.')
    else:
        try:
            client.change_position(arg)
        except ClientError:
            raise
        client.area.broadcast_evidence_list()
        client.send_host_message('Position changed.')


def ooc_cmd_poslock(client, arg):
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')
    if not arg:
        client.send_host_message(
            'Poslock is currently {}.'.format(client.area.pos_lock))
        return
    if arg == 'clear':
        client.area.pos_lock = None
        client.area.send_host_message('Position lock cleared.')
        return
    if arg not in ('def', 'pro', 'hld', 'hlp', 'jud', 'wit'):
        raise ClientError('Invalid pos.')
    client.area.pos_lock = arg
    client.area.send_host_message('Locked pos into {}.'.format(arg))

def ooc_cmd_forcepos(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if client.area.pos_lock:
        raise ClientError('Positions are locked in this area.')

    args = arg.split()

    if len(args) < 1:
        raise ArgumentError(
            'Not enough arguments. Use /forcepos <pos> <target>. Target should be ID, OOC-name or char-name. Use /getarea for getting info like "[ID] char-name".')

    targets = []

    pos = args[0]
    if len(args) > 1:
        targets = client.server.client_manager.get_targets(
            client, TargetType.CHAR_NAME, " ".join(args[1:]), True)
        if len(targets) == 0 and args[1].isdigit():
            targets = client.server.client_manager.get_targets(
                client, TargetType.ID, int(arg[1]), True)
        if len(targets) == 0:
            targets = client.server.client_manager.get_targets(
                client, TargetType.OOC_NAME, " ".join(args[1:]), True)
        if len(targets) == 0:
            raise ArgumentError('No targets found.')
    else:
        for c in client.area.clients:
            targets.append(c)

    for t in targets:
        try:
            t.change_position(pos)
            t.area.broadcast_evidence_list()
            t.send_host_message('Forced into /pos {}.'.format(pos))
        except ClientError:
            raise

    client.area.send_host_message(
        '{} forced {} client(s) into /pos {}.'.format(client.name, len(targets), pos))
    logger.log_server('Used /forcepos {} for {} client(s).'.format(pos, len(targets)), client)


def ooc_cmd_help(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    help_url = 'https://github.com/Crystalwarrior/KFO-Server/blob/master/README.md'
    help_msg = 'Available commands, source code and issues can be found here: {}'.format(help_url)
    client.send_host_message(help_msg)


def ooc_cmd_kick(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /kick <ipid> [reason]')
    args = list(arg.split(' '))
    raw_ipid = args[0]
    try:
        ipid = int(raw_ipid)
    except:
        raise ClientError('{} does not look like a valid IPID.'.format(raw_ipid))
    targets = client.server.client_manager.get_targets(client, TargetType.IPID, ipid, False)
    if targets:
        reason = ' '.join(args[1:])
        if reason == '':
            reason = 'N/A'
        for c in targets:
            logger.log_server('Kicked {} [{}]({}) (reason: {}).'.format(c.get_char_name(), c.id, c.ipid, reason), client)
            logger.log_mod('Kicked {} [{}]({}) (reason: {}).'.format(c.get_char_name(), c.id, c.ipid, reason), client)
            client.send_host_message("{} was kicked.".format(c.get_char_name()))
            c.send_command('KK', reason)
            c.disconnect()
    else:
        client.send_host_message("No targets with the IPID {} were found.".format(ipid))

#It's "KickMySelf", t-totally.
def ooc_cmd_kms(client, arg):
    targets = client.server.client_manager.get_targets(client, TargetType.IPID, client.ipid, False)
    for target in targets:
        if target != client:
            target.disconnect()
    client.send_host_message('Kicked other instances of client.')

def ooc_cmd_ban(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /ban <ipid> [reason]')
    args = list(arg.split(' '))
    raw_ipid = args[0]
    try:
        ipid = int(raw_ipid)
    except:
        raise ClientError('{} does not look like a valid IPID.'.format(raw_ipid))
    try:
        client.server.ban_manager.add_ban(ipid)
    except ServerError:
        raise
    if ipid != None:
        targets = client.server.client_manager.get_targets(client, TargetType.IPID, ipid, False)
        if targets:
            reason = ' '.join(args[1:])
            if reason == '':
                reason = 'N/A'
            for c in targets:
                c.send_command('KB', reason)
                c.disconnect()
            client.send_host_message('{} clients were kicked.'.format(len(targets)))
        client.send_host_message('{} was banned.'.format(ipid))
        logger.log_server('Banned {} (reason: {}).'.format(ipid, reason), client)
        logger.log_mod('Banned {} (reason: {}).'.format(ipid, reason), client)


def ooc_cmd_unban(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /unban <ipid> <ipid> ...')
    args = list(arg.split(' '))
    client.send_host_message('Attempting to unban {} IPIDs.'.format(len(args)))
    for raw_ipid in args:
        try:
            client.server.ban_manager.remove_ban(int(raw_ipid))
        except:
            raise ClientError('{} does not look like a valid IPID.'.format(raw_ipid))
        logger.log_server('Unbanned {}.'.format(raw_ipid), client)
        logger.log_mod('Unbanned {}.'.format(raw_ipid), client)
        client.send_host_message('Unbanned {}'.format(raw_ipid))


def ooc_cmd_play(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a song.')
    client.area.play_music(arg, client.char_id, -1)
    # client.area.add_music_playing(client, arg)
    logger.log_server('Changed music to {}.'.format(arg), client)


def ooc_cmd_mute(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /mute <ipid>.')
    args = list(arg.split(' '))
    client.send_host_message('Attempting to mute {} IPIDs.'.format(len(args)))
    for raw_ipid in args:
        if raw_ipid.isdigit():
            ipid = int(raw_ipid)
            clients = client.server.client_manager.get_targets(client, TargetType.IPID, ipid, False)
            if (clients):
                msg = 'Muted the IPID ' + str(ipid) + '\'s following clients:'
                for c in clients:
                    c.is_muted = True
                    logger.log_server('Muted {} [{}]({}).'.format(c.get_char_name(), c.id, c.ipid), client)
                    logger.log_mod('Muted {} [{}]({}).'.format(c.get_char_name(), c.id, c.ipid), client)
                    msg += ' ' + c.get_char_name() + ' [' + str(c.id) + '],'
                msg = msg[:-1]
                msg += '.'
                client.send_host_message('{}'.format(msg))
            else:
                client.send_host_message("No targets found. Use /mute <ipid> <ipid> ... for mute.")
        else:
            client.send_host_message('{} does not look like a valid IPID.'.format(raw_ipid))


def ooc_cmd_unmute(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    args = list(arg.split(' '))
    client.send_host_message('Attempting to unmute {} IPIDs.'.format(len(args)))
    for raw_ipid in args:
        if raw_ipid.isdigit():
            ipid = int(raw_ipid)
            clients = client.server.client_manager.get_targets(client, TargetType.IPID, ipid, False)
            if (clients):
                msg = 'Unmuted the IPID ' + str(ipid) + '\'s following clients::'
                for c in clients:
                    c.is_muted = False
                    logger.log_server('Unmuted {} [{}]({}).'.format(c.get_char_name(), c.id, c.ipid), client)
                    logger.log_mod('Unmuted {} [{}]({}).'.format(c.get_char_name(), c.id, c.ipid), client)
                    msg += ' ' + c.get_char_name() + ' [' + str(c.id) + '],'
                msg = msg[:-1]
                msg += '.'
                client.send_host_message('{}'.format(msg))
            else:
                client.send_host_message("No targets found. Use /unmute <ipid> <ipid> ... for unmute.")
        else:
            client.send_host_message('{} does not look like a valid IPID.'.format(raw_ipid))

def ooc_cmd_iclogs(client, arg):
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')

    args = arg.split()
    area = client.area

    if len(args) == 0:
        args = [10]

    if args[0] == "link":
        client.send_host_message("Fetching pastebin for full IC log...")
        logs = '[{}] IC logs for area [{}] {} in hub [{}] {}'.format(time.strftime(
            "%d-%b-%y|%H:%M:%S UTC", area.record_start), area.id, area.name, client.hub.id, client.hub.name)
        for line in area.recorded_messages:
            logs += '\n{}'.format(line)
        #print(logs)
        try:
            paste = paste_it()
            link = paste.create_paste(logs, 'IC logs for area [{}] {} in hub [{}] {}'.format(
                area.id, area.name, client.hub.id, client.hub.name))
            client.send_host_message('Success! Pastebin: {}'.format(link))
        except:
            raise ArgumentError('Failed...')

    if len(args) > 1:
        try:
            area = client.hub.get_area_by_id(int(args[1]))
        except:
            raise ArgumentError('Invalid area! Try /iclogs [num_lines OR "link"] [area_id]')

    try:
        lines = int(args[0])
        if lines > 50:
            lines = 50
        if lines < 0:
            raise
        i = 0
        for line in area.recorded_messages[-lines:]:
            if i >= lines:
                break
            client.send_host_message(line)
            i += 1
        if i == 0:
            client.send_host_message('Error: logs are empty!')
            return
        client.send_host_message('Displaying last {} IC messages in area [{}] {} of hub {}.'.format(i, area.id, area.name, client.hub.id))
    except:
        raise ArgumentError(
            'Bad number of lines! Try /iclogs [num_lines OR "link"] [area_id]')

def ooc_cmd_login(client, arg):
    if len(arg) == 0:
        raise ArgumentError('You must specify the password.')
    try:
        client.auth_mod(arg)
    except ClientError:
        raise
    if client.area.evidence_mod == 'HiddenCM':
        client.area.broadcast_evidence_list()
    client.send_host_message('Logged in as a moderator.')
    logger.log_server('Logged in as moderator.', client)
    logger.log_mod('Logged in as moderator.', client)


def ooc_cmd_g(client, arg):
    if client.muted_global:
        raise ClientError('Global chat toggled off.')
    if len(arg) == 0:
        raise ArgumentError("You can't send an empty message.")
    client.server.broadcast_global(client, arg)
    logger.log_server('[GLOBAL] "{}"'.format(arg), client)

def ooc_cmd_h(client, arg):
    if len(arg) == 0:
        raise ArgumentError("You can't send an empty message.")

    if client.hub.is_ooc_muted and not client.is_cm and not client.is_mod:
        client.send_host_message("OOC is muted in this hub!")
        return

    cm = ''
    if client.is_cm:
        cm = '[CM]'
    elif client.is_mod:
        cm = '[MOD]'

    # name = client.get_char_name()
    # if client.hidden:
    #     name = 'HIDDEN'
    #     cm = ''

    client.hub.send_command('CT', '~H{}[{}]'.format(cm, client.name), arg)
    logger.log_server('[HUB] "{}"'.format(arg), client)

def ooc_cmd_gm(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if client.muted_global:
        raise ClientError('You have the global chat muted.')
    if len(arg) == 0:
        raise ArgumentError("Can't send an empty message.")
    client.server.broadcast_global(client, arg, True)
    logger.log_server('[GLOBAL-MOD] "{}"'.format(arg), client)
    logger.log_mod('[GLOBAL-MOD] "{}"'.format(arg), client)


def ooc_cmd_m(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError("You can't send an empty message.")
    client.server.send_modchat(client, arg)
    logger.log_server('[MODCHAT] "{}"'.format(arg), client)
    logger.log_mod('[MODCHAT] "{}"'.format(arg), client)


def ooc_cmd_lm(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError("Can't send an empty message.")
    client.area.send_command('CT', '{}[MOD][{}]'
                             .format(client.server.config['hostname'], client.get_char_name()), arg)
    logger.log_server('[LOCAL-MOD] "{}"'.format(arg), client)
    logger.log_mod('[LOCAL-MOD] "{}"'.format(arg), client)


def ooc_cmd_announce(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError("Can't send an empty message.")
    client.server.send_all_cmd_pred('CT', '{}'.format(client.server.config['hostname']),
                                    '=== Announcement ===\r\n{}\r\n=================='.format(arg), '1')
    logger.log_server('[ANNOUNCEMENT] "{}"'.format(arg), client)
    logger.log_mod('[ANNOUNCEMENT] "{}"'.format(arg), client)


def ooc_cmd_toggleglobal(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.muted_global = not client.muted_global
    glob_stat = 'on'
    if client.muted_global:
        glob_stat = 'off'
    client.send_host_message('Global chat turned {}.'.format(glob_stat))

def ooc_cmd_toggleooc(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')
    client.hub.is_ooc_muted = not client.hub.is_ooc_muted
    glob_stat = 'on'
    if client.hub.is_ooc_muted:
        glob_stat = 'off'
    client.hub.send_host_message('OOC chat turned {}.'.format(glob_stat))

def ooc_cmd_need(client, arg):
    if client.muted_adverts:
        raise ClientError('You have advertisements muted.')
    if len(arg) == 0:
        raise ArgumentError("You must specify what you need.")
    client.server.broadcast_need(client, arg)
    logger.log_server('[NEED]{}.'.format(arg), client)
    
def ooc_cmd_toggleadverts(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.muted_adverts = not client.muted_adverts
    adv_stat = 'on'
    if client.muted_adverts:
        adv_stat = 'off'
    client.send_host_message('Advertisements turned {}.'.format(adv_stat))


def ooc_cmd_doc(client, arg):
    if len(arg) == 0:
        client.send_host_message('Document: {}'.format(client.hub.doc))
        logger.log_server('Requested document. Link: {}'.format(client.hub.doc))
    else:
        if client.hub.status.lower().startswith('rp-strict') and not client.is_cm:
            raise AreaError(
                'Hub is {} - only the CM can change /doc.'.format(client.hub.status))
        client.hub.change_doc(arg)
        client.hub.send_host_message('[{}]{} changed the doc link.'.format(client.id, client.get_char_name(True)))
        logger.log_server('Changed document to: {}'.format(arg))

def ooc_cmd_desc(client, arg):
    if len(arg) == 0:
        client.send_host_message('Area Description: {}'.format(client.area.desc))
        logger.log_server('Requested description: {}'.format(client.area.desc))
    else:
        if client.hub.status.lower().startswith('rp-strict') and not client.is_cm:
            raise AreaError(
                'Hub is {} - only the CM can change /desc for this area.'.format(client.hub.status))
        client.area.desc = arg
        client.area.send_host_message('[{}]{} changed the area description.'.format(client.id, client.get_char_name(True)))
        logger.log_server('Changed document to: {}'.format(arg))

def ooc_cmd_descadd(client, arg):
    if len(arg) == 0:
        raise ArgumentError('You must specify a string. Use /descadd <str>.')

    if client.hub.status.lower().startswith('rp-strict') and not client.is_cm:
        raise AreaError(
            'Hub is {} - only the CM can change /descadd for this area.'.format(client.hub.status))
    client.area.desc += arg
    client.area.send_host_message('[{}]{} added to the area description.'.format(
        client.id, client.get_char_name(True)))
    logger.log_server('Changed document to: {}'.format(arg))

def ooc_cmd_cleardoc(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    client.area.send_host_message('[{}]{} cleared the doc link.'.format(
        client.id, client.get_char_name(True)))
    logger.log_server('Cleared document. Old link: {}'.format(client.hub.doc), client)
    client.hub.change_doc()


def ooc_cmd_status(client, arg):
    if len(arg) == 0:
        client.send_host_message('Current status: {}'.format(client.hub.status))
    else:
        if not client.is_cm and not client.is_mod:
            raise ClientError('Only CM or mods can change status.')
        try:
            client.hub.change_status(arg)
            client.hub.send_host_message('{} changed status to {}.'.format(client.name, client.hub.status))
            logger.log_server('Changed status to {}'.format(client.hub.status))
        except AreaError:
            raise

def ooc_cmd_online(client, _):
    client.send_player_count()

def ooc_cmd_hub(client, arg):
    args = arg.split()
    if len(args) == 0:
        client.send_hub_list()
        return

    try:
        hub = client.server.hub_manager.get_hub_by_id_or_name(
            ' '.join(args[0:]))
        client.change_hub(hub)
    except ValueError:
        raise ArgumentError('Hub ID must be a number or name.')
    except (AreaError, ClientError):
        raise
        

def ooc_cmd_follow(client, arg):
    allowed = client.is_cm or client.is_mod or client.get_char_name() == "Spectator"
    if not allowed:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        try:
            c = client.server.client_manager.get_targets(client, TargetType.ID, int(client.following), False)[0]
            client.send_host_message(
                'You are currently following [{}] {}.'.format(c.id, c.get_char_name(True)))
        except:
            raise ArgumentError('You must specify a target. Use /follow <id>.')
        return
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must specify a target. Use /follow <id>.')
    if targets:
        c = targets[0]
        if client == c:
            raise ClientError('Can\'t follow yourself!')
        if client.following == c.id:
            raise ClientError(
                'Already following [{}] {}!'.format(c.id, c.get_char_name(True)))
        client.following = c.id
        client.send_host_message(
            'You are now following [{}] {}.'.format(c.id, c.get_char_name(True)))
        client.change_area(c.area)
    else:
        client.send_host_message('No targets found.')

def ooc_cmd_unfollow(client, arg):
    try:
        c = client.server.client_manager.get_targets(
            client, TargetType.ID, int(client.following), False)[0]
        client.send_host_message(
            'You are no longer following [{}] {}.'.format(c.id, c.get_char_name(True)))
        client.following = None
    except:
        client.following = None
        raise ClientError('You\'re not following anyone!')

def ooc_cmd_area(client, arg):
    args = arg.split()
    allowed = client.is_cm or client.is_mod or client.get_char_name() == "Spectator"
    rpmode = not allowed and client.hub.rpmode
    if arg.lower() in ('accessible', 'visible', 'player'):
        rpmode = True
        args.clear()
    if len(args) == 0:
        client.send_area_list(rpmode, rpmode)
        return

    try:
        area = client.hub.get_area_by_id_or_name(' '.join(args[0:]))

        if area.is_locked and not allowed:
            raise ClientError("That area is locked!")
        if area != client.area and rpmode and len(client.area.accessible) > 0 and area.id not in client.area.accessible and not allowed:
            raise AreaError(
                'Area ID not accessible from your current area!')

        #Changing area of your own accord should stop following as well
        if client.following != None:
            try:
                c = client.server.client_manager.get_targets(
                    client, TargetType.ID, int(client.following), False)[0]
                client.send_host_message(
                    'You are no longer following [{}] {}.'.format(c.id, c.get_char_name(True)))
                client.following = None
            except:
                client.following = None

        client.change_area(area)
    except ValueError:
        raise ArgumentError('Area ID must be a number or name.')
    except (AreaError, ClientError):
        raise

def ooc_cmd_a(client, arg): #a for "area"
    return ooc_cmd_area(client, arg)

def ooc_cmd_p(client, arg): #p for "pass"
    return ooc_cmd_area(client, arg)

def ooc_cmd_pass(client, arg): #p for "pass"
    return ooc_cmd_area(client, arg)

def ooc_cmd_area_add(client, arg):
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')

    if client.hub.cur_id < client.hub.max_areas:
        client.hub.create_area('Area {}'.format(client.hub.cur_id), True,
                           client.server.backgrounds[0], False, None, 'FFA', True, True, [], '')
        client.hub.send_host_message(
            'New area created! ({}/{})'.format(client.hub.cur_id, client.hub.max_areas))
    else:
        raise AreaError('Too many areas! ({}/{})'.format(client.hub.cur_id, client.hub.max_areas))
    
def ooc_cmd_area_remove(client, arg):
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')
    args = arg.split()
    if len(args) == 0:
        args = [client.area.id]

    if len(args) == 1:
        try:
            area = client.hub.get_area_by_id(int(args[0]))
            if not area.can_remove:
                raise AreaError('This area cannot be removed!')
            client.hub.send_host_message('Area {} ({}) removed! ({}/{})'.format(
                area.id, area.name, client.hub.cur_id-1, client.hub.max_areas))
            client.hub.remove_area(area)
        except ValueError:
            raise ArgumentError('Area ID must be a number.')
        except (AreaError, ClientError):
            raise
    else:
        raise ArgumentError('Invalid number of arguments. Use /area <id>.')

def ooc_cmd_rename(client, arg):
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')
    if not client.area.can_rename:
        raise ClientError('This area cannot be renamed!')

    if len(arg) == 0:
        client.area.name = 'Area {}'.format(client.area.id)
    else:
        client.area.name = arg[:24]
    
    client.area.send_host_message('Area renamed to {}.'.format(client.area.name))

def ooc_cmd_pm(client, arg):
    args = arg.split()
    key = ''
    msg = None
    if len(args) < 2:
        raise ArgumentError('Not enough arguments. use /pm <target> <message>. Target should be ID, OOC-name or char-name. Use /getarea for getting info like "[ID] char-name".')

    targets = []
    if args[0].lower()[:2] in ['cm', 'gm']:
        targets = client.hub.get_cm_list()
        key = TargetType.ID
    if len(targets) == 0:
        targets = client.server.client_manager.get_targets(client, TargetType.CHAR_NAME, arg, False)
        key = TargetType.CHAR_NAME
    if len(targets) == 0 and args[0].isdigit():
        targets = client.server.client_manager.get_targets(client, TargetType.ID, int(args[0]), False)
        key = TargetType.ID
    if len(targets) == 0:
        targets = client.server.client_manager.get_targets(client, TargetType.OOC_NAME, arg, False)
        key = TargetType.OOC_NAME
    if len(targets) == 0:
        raise ArgumentError('No targets found.')
    try:
        if key == TargetType.ID:
            msg = ' '.join(args[1:])
        else:
            if key == TargetType.CHAR_NAME:
                msg = arg[len(targets[0].get_char_name()) + 1:]
            if key == TargetType.OOC_NAME:
                msg = arg[len(targets[0].name) + 1:]
    except:
        raise ArgumentError('Not enough arguments. Use /pm <target> <message>.')
    for c in targets:
        if c.pm_mute:
            raise ClientError('User {} muted all pm conversation'.format(c.name))
        else:
            c.send_host_message('PM from [{}] {} in {} ({}): {}'.format(client.id, client.name, client.hub.name, client.get_char_name(True), msg))
            c.hub.send_to_cm('PMLog', 'PM from [{}] {} ({}) to [{}] {} in {}: {}'.format(client.id, client.name, client.get_char_name(True), c.id, c.name, client.hub.name, msg), targets)
            client.send_host_message('PM sent to [{}] {}. Message: {}'.format(c.id, c.name, msg))
 
def ooc_cmd_mutepm(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.pm_mute = not client.pm_mute
    client.send_host_message({True: 'You stopped receiving PMs', False: 'You are now receiving PMs'}[client.pm_mute])


def ooc_cmd_charselect(client, arg):
    if not arg:
        client.char_select()
    else:
        if client.is_mod:
            try:
                client.server.client_manager.get_targets(client, TargetType.ID, int(arg), False)[0].char_select()
            except:
                raise ArgumentError('Wrong arguments. Use /charselect <target\'s id>')


def ooc_cmd_reload(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    try:
        client.reload_character()
    except ClientError:
        raise
    client.send_host_message('Character reloaded.')


def ooc_cmd_randomchar(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    if len(client.charcurse) > 0:
        free_id = random.choice(client.charcurse)
    else:
        try:
            free_id = client.area.get_rand_avail_char_id()
        except AreaError:
            raise
    try:
        client.change_character(free_id)
    except ClientError:
        raise
    client.send_host_message('Randomly switched to {}'.format(client.get_char_name()))


def ooc_cmd_getarea(client, arg):
    # if client.hub.rpmode and not client.is_cm:
    #     raise AreaError('Hub is {} - /getarea functionality disabled.'.format(client.hub.status))
    if client.blinded:
        raise ArgumentError('You are blinded - you cannot use this command!')
    allowed = client.is_cm or client.is_mod or client.get_char_name() == "Spectator"
    id = client.area.id
    if len(arg) > 0:
        if not allowed:
            raise ClientError('You must be authorized to /getarea <id>.')
        id = int(arg)
    client.send_area_info(id, client.hub.rpmode and not allowed)

def ooc_cmd_hide(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must specify a target. Use /hide <id>.')
    if targets:
        c = targets[0]
        if c.hidden:
            raise ClientError(
                'Client [{}] {} already hidden!'.format(c.id, c.get_char_name(True)))
        c.hide(True)
        client.send_host_message(
            'You have hidden [{}] {} from /getarea.'.format(c.id, c.get_char_name(True)))
    else:
        client.send_host_message('No targets found.')

def ooc_cmd_unhide(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must specify a target. Use /unhide <id>.')
    if targets:
        c = targets[0]
        if not c.hidden:
            raise ClientError(
                'Client [{}] {} already revealed!'.format(c.id, c.get_char_name(True)))
        c.hide(False)
        client.send_host_message('You have revealed [{}] {} for /getarea.'.format(c.id, c.get_char_name(True)))
    else:
        client.send_host_message('No targets found.')

def ooc_cmd_blind(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must specify a target. Use /blind <id>.')
    if targets:
        c = targets[0]
        if c.blinded:
            raise ClientError(
                'Client [{}] {} already blinded!'.format(c.id, c.get_char_name(True)))
        c.blind(True)
        client.send_host_message(
            'You have blinded [{}] {} from using /getarea and seeing non-broadcasted IC messages.'.format(c.id, c.get_char_name(True)))
    else:
        client.send_host_message('No targets found.')

def ooc_cmd_unblind(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must specify a target. Use /unblind <id>.')
    if targets:
        c = targets[0]
        if not c.blinded:
            raise ClientError(
                'Client [{}] {} already unblinded!'.format(c.id, c.get_char_name(True)))
        c.blind(False)
        client.send_host_message(
            'You have revealed [{}] {} for using /getarea and seeing non-broadcasted IC messages.'.format(c.id, c.get_char_name(True)))
    else:
        client.send_host_message('No targets found.')

def ooc_cmd_getareas(client, arg):
    if client.blinded:
        raise ArgumentError('You are blinded - you cannot use this command!')
    allowed = client.is_cm or client.is_mod or client.get_char_name() == "Spectator"
    if client.hub.rpmode and not allowed:
        raise AreaError('Hub is {} - /getareas functionality disabled.'.format(client.hub.status))
    client.send_area_info(-1)


def ooc_cmd_mods(client, arg):
    #LMAO make it *actually* send mods in *hubs*
    return

def ooc_cmd_evi_swap(client, arg):
    args = arg.split(' ')
    if len(args) != 2:
        raise ClientError("You must specify 2 numbers.")
    try:
        client.area.evi_list.evidence_swap(client, int(args[0]), int(args[1]))
        client.area.broadcast_evidence_list()
    except:
        raise ClientError("You must specify 2 numbers.")

def ooc_cmd_evi_edit(client, arg):
    #<id: int>#<name: string>#<description: string>#<image: string>#%
    args = arg.split(' ')
    if len(args) < 2:
        raise ClientError("Usage: <id: int> <name: string> <description: string> <image: string>. Replace string with . (period) if you wish to keep original data.")

    try:
        ID = int(args[0])

        name = args[1]

        if len(args) >= 3:
            desc = args[2]
        else:
            desc = '.'

        if len(args) >= 4:
            image = args[3]
        else:
            image = '.'

        ebdns = client.area.evi_list.evidences[client.evi_list[ID]]
        if ebdns:
            if name == '.':
                name = ebdns.name
            if desc == '.':
                desc = ebdns.desc
            if image == '.':
                image = ebdns.image

        evi = (name, desc, image, 'all')

        client.area.evi_list.edit_evidence(client, client.evi_list[ID], evi)
        client.area.broadcast_evidence_list()
    except:
        raise ArgumentError("Error: One or more arguments invalid. Usage: <id: int> <name: string> <description: string> <image: string>. Replace string with . if you wish to keep original data.")

def ooc_cmd_cm(client, arg):
    if len(arg) > 0:
        if not client.is_cm or client.hub.master != client:
            raise ClientError('You must be the master CM to promote co-CM\'s.')
        try:
            c = client.server.client_manager.get_targets(
                client, TargetType.ID, int(arg), False)[0]
            if c == client:
                raise
            if c.is_cm:
                if c.hub.master == c:
                    c.hub.master = None
                c.is_cm = False
                client.hub.send_host_message(
                    '{} is no longer a co-CM.'.format(c.name))
                c.send_host_message(
                    'You are no longer a co-CM of hub {}.'.format(client.hub.name))
            else:
                c.is_cm = True
                client.hub.send_host_message(
                    '{} has been made a co-CM.'.format(c.name))
                c.send_host_message(
                    'You have been made a co-CM of hub {} by {}.'.format(client.hub.name, client.name))
        except:
            raise ClientError('You must specify a target. Use /cm <id>')
    else:
        if not client.hub.allow_cm:
            raise ClientError('You can\'t become a master CM in this hub')
        if not client.hub.master and (len(client.hub.get_cm_list()) <= 0 or client.is_cm):
            client.hub.master = client
            client.is_cm = True
            if client.area.evidence_mod == 'HiddenCM':
                client.area.broadcast_evidence_list()
            client.hub.send_host_message('{} is master CM in this hub now.'.format(client.name))
        else:
            raise ClientError('Master CM exists. Use /cm <id>')

def ooc_cmd_cms(client, arg):
    client.send_host_message('=CM\'s in this hub:=')
    for cm in client.hub.get_cm_list():
        m = 'co-'
        if client.hub.master == cm:
            m = 'Master '
        client.send_host_message('=>{}CM [{}] {}'.format(m, cm.id, cm.get_char_name(True)))

def ooc_cmd_uncm(client, arg):
    if client.is_cm:
        if client.hub.master == client:
            client.hub.master = None
        client.is_cm = False
        client.send_host_message(
            'You are no longer a CM of hub {}.'.format(client.hub.name))

def ooc_cmd_cmlogs(client, arg):
    logtypes = ['MoveLog', 'RollLog', 'PMLog', 'CharLog']
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError("Current logs: {}. Available log types: {}.".format(client.cm_log_type, logtypes))

    if arg == 'on':
        client.cm_log_type = ['MoveLog', 'RollLog', 'PMLog', 'CharLog']
    elif arg == 'off':
        client.cm_log_type = []
    else:
        try:
            for a in args:
                if not a in logtypes:
                    raise
                if a in client.cm_log_type:
                    client.cm_log_type.remove(a)
                else:
                    client.cm_log_type.append(a)
        except:
            raise ArgumentError("Invalid argument: {}".format(arg))

    client.send_host_message(
        'You will now see cm logs for: {}.'.format(client.cm_log_type))

def ooc_cmd_broadcast_ic(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('Only CM or mods can broadcast IC.')
    if not arg or arg == 'clear':
        client.broadcast_ic.clear()
        client.send_host_message('You have cleared the broadcast_ic list.')
    else:
        if arg == 'all':
            client.broadcast_ic.clear()
            for area in client.hub.areas:
                client.broadcast_ic.append(area.id)
        else:
            arg = arg.split()
            for a in arg:
                try:
                    client.broadcast_ic.append(int(a))
                except:
                    raise ClientError('Invalid area ID.')
        client.send_host_message('You will now broadcast IC across areas {} in this hub.'.format(client.broadcast_ic))

def ooc_cmd_area_access(client, arg):
    if not arg:
        client.send_host_message(
            'Areas that can be accessed from this area: {}.'.format(client.area.accessible))
        return

    if not client.is_cm and not client.is_mod:
        raise ClientError('Only CM or mods can set area accessibility.')

    if arg == 'clear' or arg == 'all':
        client.area.accessible.clear()
        client.send_host_message('You have cleared the area accessibility list.')
    else:
        arg = arg.split()
        for a in arg:
            a = int(a)
            try:
                if a not in client.area.accessible:
                    client.area.accessible.append(a)
            except:
                raise ClientError('Invalid area ID.')
        client.area.send_host_message(
            'Areas that can now be accessed from this area: {}.'.format(client.area.accessible))

def ooc_cmd_area_link(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('Only CM or mods can set area accessibility.')
    if not arg:
        raise ArgumentError(
            'Must provide valid args! Command usage: /area_link id1> (id2) (idx)')

    args = arg.split()
    if len(args) == 0:
        raise ArgumentError('At least one arg must be provided! Command usage: /area_link <id1> (id2) (idx)')

    # if args[0].lower() == "self":
    #     args[0] = client.area.id

    try:
        area_from = client.hub.get_area_by_id(client.area.id) #client.hub.get_area_by_id(int(args[0]))
        for a in args: #args[1:]:
            a = int(a)
            area_to = client.hub.get_area_by_id(a)
            if a not in area_from.accessible:
                area_from.accessible.append(a)
            if area_from.id not in area_to.accessible:
                area_to.accessible.append(area_from.id)
    except ValueError:
        raise ArgumentError('Area ID must be a number.')
    except (AreaError, ClientError):
        raise

    client.area.send_host_message(
        'Areas that can now be accessed from and to area [{}] {}: {}.'.format(area_from.id, area_from.name, area_from.accessible))

def ooc_cmd_area_unlink(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('Only CM or mods can set area accessibility.')
    if not arg:
        raise ArgumentError(
            'Must provide valid args! Command usage: /area_unlink <id1> (id2) (idx)')

    args = arg.split()
    if len(args) == 0:
        raise ArgumentError('At least one arg must be provided! Command usage: /area_link <id1> (id2) (idx)')

    # if args[0].lower() == "self":
    #     args[0] = client.area.id

    try:
        area_from = client.hub.get_area_by_id(client.area.id) #client.hub.get_area_by_id(int(args[0]))
        for a in args: #args[1:]:
            a = int(a)
            area_to = client.hub.get_area_by_id(a)
            if a in area_from.accessible:
                area_from.accessible.remove(a)
            if area_from.id in area_to.accessible:
                area_to.accessible.remove(area_from.id)
    except ValueError:
        raise ArgumentError('Area ID must be a number.')
    except (AreaError, ClientError):
        raise

    client.area.send_host_message(
        'Areas that can now be accessed from and to area [{}] {}: {}.'.format(area_from.id, area_from.name, area_from.accessible))

def ooc_cmd_announce_movement(client, arg):
    if len(arg.split()) > 1:
        raise ArgumentError("This command can only take one argument ('on' or 'off') or no arguments at all!")
    if arg:
        if arg == 'on':
            client.announce_movement = True
        elif arg == 'off':
            client.announce_movement = False
        else:
            raise ArgumentError("Invalid argument: {}".format(arg))
    else:
        client.announce_movement = not client.announce_movement
    stat = 'off'
    if client.announce_movement:
        stat = 'on'
    client.send_host_message('Area transfer announcements turned {}.'.format(stat))

def ooc_cmd_unmod(client, arg):
    client.is_mod = False
    if client.area.evidence_mod == 'HiddenCM':
        client.area.broadcast_evidence_list()
    client.send_host_message('you\'re not a mod now')

def ooc_cmd_lock(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('Only CM or mods can lock the area.')
    args = []
    if arg == 'all':
        for area in client.hub.areas:
            args.append(area.id)
    elif len(arg) == 0:
        args = [client.area.id]
    else:
        try:
            args = [int(s) for s in str(arg).split(' ')]
        except:
            raise ArgumentError('Invalid argument!')
    
    i = 0
    for area in client.hub.areas:
        if area.id in args:
            if not area.locking_allowed:
                client.send_host_message(
                    'Area locking is disabled in area {}.'.format(area.id))
                continue
            if area.is_locked:
                client.send_host_message(
                    'Area {} is already locked.'.format(area.id))
                continue
            
            area.lock()
            i += 1
    client.send_host_message('Locked {} areas.'.format(i))
        
def ooc_cmd_unlock(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('Only CM or mods can unlock the area.')
    args = []
    if arg == 'all':
        for area in client.hub.areas:
            args.append(area.id)
    elif len(arg) == 0:
        args = [client.area.id]
    else:
        try:
            args = [int(s) for s in str(arg).split(' ')]
        except:
            raise ArgumentError('Invalid argument!')
    
    i = 0
    for area in client.hub.areas:
        if area.id in args:
            if not area.locking_allowed:
                client.send_host_message(
                    'Area locking is disabled in area {}.'.format(area.id))
                continue
            if not area.is_locked:
                client.send_host_message(
                    'Area {} is already unlocked.'.format(area.id))
                continue
            
            area.unlock()
            i += 1
    client.send_host_message('Unlocked {} areas.'.format(i))

def ooc_cmd_area_hide(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('Only CM or mods can hide the area.')
    args = []
    if arg == 'all':
        for area in client.hub.areas:
            args.append(area.id)
    elif len(arg) == 0:
        args = [client.area.id]
    else:
        try:
            args = [int(s) for s in str(arg).split(' ')]
        except:
            raise ArgumentError('Invalid argument!')
    
    i = 0
    for area in client.hub.areas:
        if area.id in args:
            # if not area.hiding_allowed:
            #     client.send_host_message(
            #         'Area hiding is disabled in area {}.'.format(area.id))
            #     continue
            if area.is_hidden:
                client.send_host_message('Area {} is already hidden.'.format(area.id))
                continue
            
            area.hide()
            i += 1
    client.send_host_message('Hid {} areas.'.format(i))

def ooc_cmd_area_unhide(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('Only CM or mods can unhide the area.')
    args = []
    if arg == 'all':
        for area in client.hub.areas:
            args.append(area.id)
    elif len(arg) == 0:
        args = [client.area.id]
    else:
        try:
            args = [int(s) for s in str(arg).split(' ')]
        except:
            raise ArgumentError('Invalid argument!')
    
    i = 0
    for area in client.hub.areas:
        if area.id in args:
            # if not area.hiding_allowed:
            #     client.send_host_message(
            #         'Area hiding is disabled in area {}.'.format(area.id))
            #     continue
            if not area.is_hidden:
                client.send_host_message('Area {} is already unhidden.'.format(area.id))
                continue
            
            area.unhide()
            i += 1
    client.send_host_message('Unhid {} areas.'.format(i))

def ooc_cmd_savehub_legacy(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('Only CM or mods can save the hub.')
    area = client.hub.default_area()
    area.evi_list.add_evidence(client, '--HUB SAVE DATA--', client.hub.save(), '2.png', 'all')
    area.broadcast_evidence_list()
    client.send_host_message('The hub data has been saved in an evidence file in area [{}] {}.'.format(area.id, area.name))

def ooc_cmd_listhubs(client, arg):
    if not client.is_mod:
        raise ClientError('Only mods can view available hub saves.')
    
    text = 'Available hubs:'
    for F in os.listdir('storage/hubs/'):
        if F.lower().endswith('.yaml'):
            text += '\n- {}'.format(F[:-5])

    client.send_host_message(text)

def ooc_cmd_savehub(client, arg):
    if not client.is_mod:
        raise ClientError('Only mods can save the hub.')
    if arg == '':
        raise ClientError('No save name provided!')

    client.hub.yaml_dump(arg)
    client.send_host_message('The hub data has been saved on the server in a file named \'{}.yaml\'.'.format(arg))

def ooc_cmd_loadhub(client, arg):
    if not client.is_cm and not client.is_mod:
        raise ClientError('Only CM or mods can load the hub.')
    if arg == '':
        raise ClientError('No save name provided!')

    try:
        client.hub.yaml_load(arg)
        client.send_host_message("Loading hub save data \'{}.yaml\'...".format(arg))
    except:
        raise ClientError('No save of that name exists!')

def ooc_cmd_akick(client, arg):
    if not client.is_mod and not client.is_cm:
        raise ClientError('You must be authorized to do that.')
    if not arg:
        raise ClientError('You must specify a target. Use /akick <id> [destination #] [hub #]')
    arg = arg.split()
    targets = client.server.client_manager.get_targets(client, TargetType.ID, int(arg[0]), False)
    output = [0, 0]
    if targets:
        try:
            for c in targets:
                if len(arg) == 1:
                    #area = client.server.hub_manager.default_hub().get_area_by_id(0)
                    area = client.hub.get_area_by_id(0)
                else:
                    try:
                        if len(arg) > 2 and client.is_mod:
                            hub = client.server.hub_manager.get_hub_by_id(int(arg[2]))
                            output[1] = arg[2]
                        else:
                            hub = client.hub
                            output[1] = client.hub.id
                        area = hub.get_area_by_id(int(arg[1]))
                        output[0] = arg[1]
                    except AreaError:
                        raise
                client.send_host_message("Attempting to kick [{}]{} to area {} [Hub {}].".format(
                    c.id, c.get_char_name(True), output[0], output[1]))
                if c.area.is_locked:
                    c.area.invite_list.pop(c.ipid)
                if area.is_locked:
                    area.invite_list[c.ipid] = None
                c.change_area(area, True) #hidden change area regardless of announce_movement
                c.send_host_message("You were kicked from the area to area {} [Hub {}].".format(output[0], output[1]))
        except AreaError:
            raise
        except ClientError:
            raise
    else:
        client.send_host_message("No targets found.")
    
def ooc_cmd_ooc_mute(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /ooc_mute <OOC-name>.')
    targets = client.server.client_manager.get_targets(client, TargetType.OOC_NAME, arg, False)
    if not targets:
        raise ArgumentError('Targets not found. Use /ooc_mute <OOC-name>.')
    for target in targets:
        target.is_ooc_muted = True
    client.send_host_message('Muted {} existing client(s).'.format(len(targets)))


def ooc_cmd_ooc_unmute(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /ooc_unmute <OOC-name>.')
    targets = client.server.client_manager.get_ooc_muted_clients()
    if not targets:
        raise ArgumentError('Targets not found. Use /ooc_unmute <OOC-name>.')
    for target in targets:
        target.is_ooc_muted = False
    client.send_host_message('Unmuted {} existing client(s).'.format(len(targets)))


def ooc_cmd_disemvowel(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = client.server.client_manager.get_targets(client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must specify a target. Use /disemvowel <id>.')
    if targets:
        for c in targets:
            logger.log_server('Disemvowelling {}.'.format(c.get_ip()), client)
            logger.log_mod('Disemvowelling {}.'.format(c.get_ip()), client)
            c.disemvowel = True
        client.send_host_message('Disemvowelled {} existing client(s).'.format(len(targets)))
    else:
        client.send_host_message('No targets found.')


def ooc_cmd_undisemvowel(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = client.server.client_manager.get_targets(client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must specify a target. Use /undisemvowel <id>.')
    if targets:
        for c in targets:
            logger.log_server('Undisemvowelling {}.'.format(c.get_ip()), client)
            logger.log_mod('Undisemvowelling {}.'.format(c.get_ip()), client)
            c.disemvowel = False
        client.send_host_message('Undisemvowelled {} existing client(s).'.format(len(targets)))
    else:
        client.send_host_message('No targets found.')


def ooc_cmd_shake(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = client.server.client_manager.get_targets(client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must specify a target. Use /shake <id>.')
    if targets:
        for c in targets:
            logger.log_server('Shaking {}.'.format(c.get_ip()), client)
            logger.log_mod('Shaking {}.'.format(c.get_ip()), client)
            c.shaken = True
        client.send_host_message('Shook {} existing client(s).'.format(len(targets)))
    else:
        client.send_host_message('No targets found.')


def ooc_cmd_unshake(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError('You must specify a target.')
    try:
        targets = client.server.client_manager.get_targets(client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must specify a target. Use /unshake <id>.')
    if targets:
        for c in targets:
            logger.log_server('Unshaking {}.'.format(c.get_ip()), client)
            logger.log_mod('Unshaking {}.'.format(c.get_ip()), client)
            c.shaken = False
        client.send_host_message('Unshook {} existing client(s).'.format(len(targets)))
    else:
        client.send_host_message('No targets found.')


def ooc_cmd_charcurse(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError(
            'You must specify a target (an ID) and at least one character ID. Consult /charids for the character IDs.')
    elif len(arg) == 1:
        raise ArgumentError('You must specific at least one character ID. Consult /charids for the character IDs.')
    args = arg.split()
    try:
        targets = client.server.client_manager.get_targets(client, TargetType.ID, int(args[0]), False)
    except:
        raise ArgumentError('You must specify a valid target! Make sure it is a valid ID.')
    if targets:
        for c in targets:
            log_msg = ' ' + str(c.get_ip()) + ' to'
            part_msg = ' [' + str(c.id) + '] to'
            for raw_cid in args[1:]:
                try:
                    cid = int(raw_cid)
                    c.charcurse.append(cid)
                    part_msg += ' ' + str(client.server.char_list[cid]) + ','
                    log_msg += ' ' + str(client.server.char_list[cid]) + ','
                except:
                    ArgumentError('' + str(raw_cid) + ' does not look like a valid character ID.')
            part_msg = part_msg[:-1]
            part_msg += '.'
            log_msg = log_msg[:-1]
            log_msg += '.'
            c.char_select()
            logger.log_server('Charcursing' + log_msg, client)
            logger.log_mod('Charcursing' + log_msg, client)
            client.send_host_message('Charcursed' + part_msg)
    else:
        client.send_host_message('No targets found.')


def ooc_cmd_uncharcurse(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif len(arg) == 0:
        raise ArgumentError('You must specify a target (an ID).')
    args = arg.split()
    try:
        targets = client.server.client_manager.get_targets(client, TargetType.ID, int(args[0]), False)
    except:
        raise ArgumentError('You must specify a valid target! Make sure it is a valid ID.')
    if targets:
        for c in targets:
            if len(c.charcurse) > 0:
                c.charcurse = []
                logger.log_server('Uncharcursing {}.'.format(c.get_ip()), client)
                logger.log_mod('Uncharcursing {}.'.format(c.get_ip()), client)
                client.send_host_message('Uncharcursed [{}].'.format(c.id))
                c.char_select()
            else:
                client.send_host_message('[{}] is not charcursed.'.format(c.id))
    else:
        client.send_host_message('No targets found.')


def ooc_cmd_charids(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    msg = 'Here is a list of all available characters on the server:'
    for c in range(0, len(client.server.char_list)):
        msg += '\n[' + str(c) + '] ' + client.server.char_list[c]
    client.send_host_message(msg)


def ooc_cmd_blockdj(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /blockdj <id>.')
    try:
        targets = client.server.client_manager.get_targets(client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must enter a number. Use /blockdj <id>.')
    if not targets:
        raise ArgumentError('Target not found. Use /blockdj <id>.')
    for target in targets:
        target.is_dj = False
        target.send_host_message('A moderator muted you from changing the music.')
        logger.log_server('BlockDJ\'d {} [{}]({}).'.format(target.get_char_name(), target.id, target.get_ip()), client)
        logger.log_mod('BlockDJ\'d {} [{}]({}).'.format(target.get_char_name(), target.id, target.get_ip()), client)
    client.send_host_message('blockdj\'d {}.'.format(targets[0].get_char_name()))


def ooc_cmd_unblockdj(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /unblockdj <id>.')
    try:
        targets = client.server.client_manager.get_targets(client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must enter a number. Use /unblockdj <id>.')
    if not targets:
        raise ArgumentError('Target not found. Use /blockdj <id>.')
    for target in targets:
        target.is_dj = True
        target.send_host_message('A moderator unmuted you from changing the music.')
        logger.log_server('UnblockDJ\'d {} [{}]({}).'.format(target.get_char_name(), target.id, target.get_ip()),
                          client)
        logger.log_mod('UnblockDJ\'d {} [{}]({}).'.format(target.get_char_name(), target.id, target.get_ip()), client)
    client.send_host_message('Unblockdj\'d {}.'.format(targets[0].get_char_name()))


def ooc_cmd_blockwtce(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /blockwtce <id>.')
    try:
        targets = client.server.client_manager.get_targets(client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must enter a number. Use /blockwtce <id>.')
    if not targets:
        raise ArgumentError('Target not found. Use /blockwtce <id>.')
    for target in targets:
        target.can_wtce = False
        target.send_host_message('A moderator blocked you from using judge signs.')
        logger.log_server('BlockWTCE\'d {} [{}]({}).'.format(target.get_char_name(), target.id, target.get_ip()),
                          client)
        logger.log_mod('BlockWTCE\'d {} [{}]({}).'.format(target.get_char_name(), target.id, target.get_ip()), client)
    client.send_host_message('blockwtce\'d {}.'.format(targets[0].get_char_name()))


def ooc_cmd_unblockwtce(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /unblockwtce <id>.')
    try:
        targets = client.server.client_manager.get_targets(client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must enter a number. Use /unblockwtce <id>.')
    if not targets:
        raise ArgumentError('Target not found. Use /unblockwtce <id>.')
    for target in targets:
        target.can_wtce = True
        target.send_host_message('A moderator unblocked you from using judge signs.')
        logger.log_server('UnblockWTCE\'d {} [{}]({}).'.format(target.get_char_name(), target.id, target.get_ip()),
                          client)
        logger.log_mod('UnblockWTCE\'d {} [{}]({}).'.format(target.get_char_name(), target.id, target.get_ip()), client)
    client.send_host_message('unblockwtce\'d {}.'.format(targets[0].get_char_name()))

def ooc_cmd_rolla_reload(client, arg):
    if not client.is_mod:
        raise ClientError('You must be a moderator to load the ability dice configuration.')
    rolla_reload(client.area)
    client.send_host_message('Reloaded ability dice configuration.')


def rolla_reload(area):
    try:
        import yaml
        with open('config/dice.yaml', 'r') as dice:
            area.ability_dice = yaml.load(dice)
    except:
        raise ServerError('There was an error parsing the ability dice configuration. Check your syntax.')


def ooc_cmd_rolla_set(client, arg):
    if not hasattr(client.area, 'ability_dice'):
        rolla_reload(client.area)
    available_sets = ', '.join(client.area.ability_dice.keys())
    if len(arg) == 0:
        raise ArgumentError('You must specify the ability set name.\nAvailable sets: {}'.format(available_sets))
    if arg in client.area.ability_dice:
        client.ability_dice_set = arg
        client.send_host_message("Set ability set to {}.".format(arg))
    else:
        raise ArgumentError('Invalid ability set \'{}\'.\nAvailable sets: {}'.format(arg, available_sets))


def ooc_cmd_rolla(client, arg):
    if not hasattr(client.area, 'ability_dice'):
        rolla_reload(client.area)
    if not hasattr(client, 'ability_dice_set'):
        raise ClientError('You must set your ability set using /rolla_set <name>.')
    ability_dice = client.area.ability_dice[client.ability_dice_set]
    max_roll = ability_dice['max'] if 'max' in ability_dice else 6
    roll = random.randint(1, max_roll)
    ability = ability_dice[roll] if roll in ability_dice else "Nothing happens"
    client.area.send_host_message(
        '{} rolled a {} (out of {}): {}.'.format(client.get_char_name(), roll, max_roll, ability))
        
def ooc_cmd_refresh(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) > 0:
        raise ClientError('This command does not take in any arguments!')
    else:
        try:
            client.server.refresh()
            client.send_host_message('You have reloaded the server.')
        except ServerError:
            raise


def ooc_cmd_judgelog(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) != 0:
        raise ArgumentError('This command does not take any arguments.')
    jlog = client.area.judgelog
    if len(jlog) > 0:
        jlog_msg = '== Judge Log =='
        for x in jlog:
            jlog_msg += '\r\n{}'.format(x)
        client.send_host_message(jlog_msg)
    else:
        raise ServerError('There have been no judge actions in this area since start of session.')
