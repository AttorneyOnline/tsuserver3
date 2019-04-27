import re

from server import logger
from server.constants import TargetType
from server.exceptions import ClientError, ServerError, ArgumentError

__all__ = [
    'ooc_cmd_doc',
    'ooc_cmd_cleardoc',
    'ooc_cmd_evidence_mod',
    'ooc_cmd_evi_swap',
    'ooc_cmd_cm',
    'ooc_cmd_uncm',
    'ooc_cmd_setcase',
    'ooc_cmd_anncase',
    'ooc_cmd_blockwtce',
    'ooc_cmd_unblockwtce',
    'ooc_cmd_judgelog'
]


def ooc_cmd_doc(client, arg):
    """
    Show or change the link for the current case document.
    Usage: /doc [url]
    """
    if len(arg) == 0:
        client.send_ooc(f'Document: {client.area.doc}')
        logger.log_server(
            '[{}][{}]Requested document. Link: {}'.format(
                client.area.abbreviation, client.char_name,
                client.area.doc), client)
    else:
        client.area.change_doc(arg)
        client.area.broadcast_ooc('{} changed the doc link.'.format(
            client.char_name))
        logger.log_server(
            '[{}][{}]Changed document to: {}'.format(client.area.abbreviation,
                                                     client.char_name,
                                                     arg), client)


def ooc_cmd_cleardoc(client, arg):
    """
    Clear the link for the current case document.
    Usage: /cleardoc
    """
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    client.area.broadcast_ooc('{} cleared the doc link.'.format(
        client.char_name))
    logger.log_server(
        '[{}][{}]Cleared document. Old link: {}'.format(
            client.area.abbreviation, client.char_name, client.area.doc),
        client)
    client.area.change_doc()


def ooc_cmd_evidence_mod(client, arg):
    """
    Change the evidence privilege mode. Refer to the documentation
    for more information on the function of each mode.
    Usage: /evidence_mod <FFA|Mods|CM|HiddenCM>
    """
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    elif not arg or arg == client.area.evidence_mod:
        client.send_ooc(
            f'current evidence mod: {client.area.evidence_mod}')
    elif arg in ['FFA', 'Mods', 'CM', 'HiddenCM']:
        if client.area.evidence_mod == 'HiddenCM':
            for i in range(len(client.area.evi_list.evidences)):
                client.area.evi_list.evidences[i].pos = 'all'
        client.area.evidence_mod = arg
        client.send_ooc(
            f'current evidence mod: {client.area.evidence_mod}')
    else:
        raise ArgumentError(
            'Wrong Argument. Use /evidence_mod <MOD>. Possible values: FFA, CM, Mods, HiddenCM'
        )


def ooc_cmd_evi_swap(client, arg):
    """
    Swap the positions of two evidence items on the evidence list.
    Usage: /evi_swap <id> <id>
    """
    args = list(arg.split(' '))
    if len(args) != 2:
        raise ClientError("you must specify 2 numbers")
    try:
        client.area.evi_list.evidence_swap(client, int(args[0]), int(args[1]))
        client.area.broadcast_evidence_list()
    except:
        raise ClientError("you must specify 2 numbers")


def ooc_cmd_cm(client, arg):
    """
    Add a case manager for the current room.
    Usage: /cm <id>
    """
    if 'CM' not in client.area.evidence_mod:
        raise ClientError('You can\'t become a CM in this area')
    if len(client.area.owners) == 0:
        if len(arg) > 0:
            raise ArgumentError(
                'You cannot \'nominate\' people to be CMs when you are not one.'
            )
        client.area.owners.append(client)
        if client.area.evidence_mod == 'HiddenCM':
            client.area.broadcast_evidence_list()
        client.server.area_manager.send_arup_cms()
        client.area.broadcast_ooc('{} [{}] is CM in this area now.'.format(
            client.char_name, client.id))
    elif client in client.area.owners:
        if len(arg) > 0:
            arg = arg.split(' ')
        for id in arg:
            try:
                id = int(id)
                c = client.server.client_manager.get_targets(
                    client, TargetType.ID, id, False)[0]
                if not c in client.area.clients:
                    raise ArgumentError(
                        'You can only \'nominate\' people to be CMs when they are in the area.'
                    )
                elif c in client.area.owners:
                    client.send_ooc(
                        '{} [{}] is already a CM here.'.format(
                            c.char_name, c.id))
                else:
                    client.area.owners.append(c)
                    if client.area.evidence_mod == 'HiddenCM':
                        client.area.broadcast_evidence_list()
                    client.server.area_manager.send_arup_cms()
                    client.area.broadcast_ooc(
                        '{} [{}] is CM in this area now.'.format(
                            c.char_name, c.id))
            except:
                client.send_ooc(
                    f'{id} does not look like a valid ID.')
    else:
        raise ClientError('You must be authorized to do that.')


def ooc_cmd_uncm(client, arg):
    """
    Remove a case manager from the current area.
    Usage: /uncm <id>
    """
    if client in client.area.owners or client.is_mod:
        if len(arg) > 0:
            arg = arg.split(' ')
        else:
            arg = [client.id]
        for id in arg:
            try:
                id = int(id)
                c = client.server.client_manager.get_targets(
                    client, TargetType.ID, id, False)[0]
                if c in client.area.owners:
                    client.area.owners.remove(c)
                    client.server.area_manager.send_arup_cms()
                    client.area.broadcast_ooc(
                        '{} [{}] is no longer CM in this area.'.format(
                            c.char_name, c.id))
                else:
                    client.send_ooc(
                        'You cannot remove someone from CMing when they aren\'t a CM.'
                    )
            except:
                client.send_ooc(
                    f'{id} does not look like a valid ID.')
    else:
        raise ClientError('You must be authorized to do that.')


# LEGACY
def ooc_cmd_setcase(client, arg):
    """
    Set the positions you are interested in taking for a case.
    (This command is used internally by the 2.6 client.)
    """
    args = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', arg)
    if len(args) == 0:
        raise ArgumentError('Please do not call this command manually!')
    else:
        client.casing_cases = args[0]
        client.casing_cm = args[1] == "1"
        client.casing_def = args[2] == "1"
        client.casing_pro = args[3] == "1"
        client.casing_jud = args[4] == "1"
        client.casing_jur = args[5] == "1"
        client.casing_steno = args[6] == "1"


# LEGACY
def ooc_cmd_anncase(client, arg):
    """
    Announce that a case is currently taking place in this area,
    needing a certain list of positions to be filled up.
    Usage: /anncase <message> <def> <pro> <jud> <jur> <steno>
    """
    if client in client.area.owners:
        if not client.can_call_case():
            raise ClientError(
                'Please wait 60 seconds between case announcements!')
        args = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', arg)
        if len(args) == 0:
            raise ArgumentError('Please do not call this command manually!')
        elif len(args) == 1:
            raise ArgumentError(
                'You should probably announce the case to at least one person.'
            )
        else:
            if not args[1] == "1" and not args[2] == "1" and not args[
                    3] == "1" and not args[4] == "1" and not args[5] == "1":
                raise ArgumentError(
                    'You should probably announce the case to at least one person.'
                )
            msg = '=== Case Announcement ===\r\n{} [{}] is hosting {}, looking for '.format(
                client.char_name, client.id, args[0])

            lookingfor = []

            if args[1] == "1":
                lookingfor.append("defence")
            if args[2] == "1":
                lookingfor.append("prosecutor")
            if args[3] == "1":
                lookingfor.append("judge")
            if args[4] == "1":
                lookingfor.append("juror")
            if args[5] == "1":
                lookingfor.append("stenographer")

            msg = msg + ', '.join(lookingfor) + '.\r\n=================='

            client.server.send_all_cmd_pred('CASEA', msg, args[1], args[2],
                                            args[3], args[4], args[5], '1')

            client.set_case_call_delay()

            logger.log_server(
                '[{}][{}][CASE_ANNOUNCEMENT]{}, DEF: {}, PRO: {}, JUD: {}, JUR: {}, STENO: {}.'
                .format(client.area.abbreviation, client.char_name,
                        args[0], args[1], args[2], args[3], args[4], args[5]),
                client)
    else:
        raise ClientError(
            'You cannot announce a case in an area where you are not a CM!')


def ooc_cmd_blockwtce(client, arg):
    """
    Prevent a user from using Witness Testimony/Cross Examination buttons
    as a judge.
    Usage: /blockwtce <id>
    """
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError('You must specify a target. Use /blockwtce <id>.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must enter a number. Use /blockwtce <id>.')
    if not targets:
        raise ArgumentError('Target not found. Use /blockwtce <id>.')
    for target in targets:
        target.can_wtce = False
        target.send_ooc(
            'A moderator blocked you from using judge signs.')
        logger.log_mod(
            'BlockWTCE\'d {} [{}]({}).'.format(target.char_name,
                                               target.id, target.ip),
            client)
    client.send_ooc('blockwtce\'d {}.'.format(
        targets[0].char_name))


def ooc_cmd_unblockwtce(client, arg):
    """
    Allow a user to use WT/CE again.
    Usage: /unblockwtce <id>
    """
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError(
            'You must specify a target. Use /unblockwtce <id>.')
    try:
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(arg), False)
    except:
        raise ArgumentError('You must enter a number. Use /unblockwtce <id>.')
    if not targets:
        raise ArgumentError('Target not found. Use /unblockwtce <id>.')
    for target in targets:
        target.can_wtce = True
        target.send_ooc(
            'A moderator unblocked you from using judge signs.')
        logger.log_mod(
            'UnblockWTCE\'d {} [{}]({}).'.format(target.char_name,
                                                 target.id, target.ip),
            client)
    client.send_ooc('unblockwtce\'d {}.'.format(
        targets[0].char_name))


def ooc_cmd_judgelog(client, arg):
    """
    List the last 10 uses of judge controls in the current area.
    Usage: /judgelog
    """
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) != 0:
        raise ArgumentError('This command does not take any arguments.')
    jlog = client.area.judgelog
    if len(jlog) > 0:
        jlog_msg = '== Judge Log =='
        for x in jlog:
            jlog_msg += f'\r\n{x}'
        client.send_ooc(jlog_msg)
    else:
        raise ServerError(
            'There have been no judge actions in this area since start of session.'
        )
