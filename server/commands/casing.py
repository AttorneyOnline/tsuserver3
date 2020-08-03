import re

from server import database
from server.constants import TargetType
from server.exceptions import ClientError, ServerError, ArgumentError

from . import mod_only

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
    'ooc_cmd_judgelog',
    'ooc_cmd_afk',
    'ooc_cmd_remote_listen',
    'ooc_cmd_testimony',
    'ooc_cmd_testimony_clear',
    'ooc_cmd_testimony_remove',
    'ooc_cmd_testimony_amend',
    'ooc_cmd_testimony_swap',
]


def ooc_cmd_doc(client, arg):
    """
    Show or change the link for the current case document.
    Usage: /doc [url]
    """
    if len(arg) == 0:
        client.send_ooc(f'Document: {client.area.doc}')
        database.log_room('doc.request', client, client.area)
    else:
        client.area.change_doc(arg)
        client.area.broadcast_ooc('{} changed the doc link.'.format(
            client.char_name))
        database.log_room('doc.change', client, client.area, message=arg)


def ooc_cmd_cleardoc(client, arg):
    """
    Clear the link for the current case document.
    Usage: /cleardoc
    """
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    client.area.change_doc()
    client.area.broadcast_ooc('{} cleared the doc link.'.format(
        client.char_name))
    database.log_room('doc.clear', client, client.area)


@mod_only(hub_owners=True)
def ooc_cmd_evidence_mod(client, arg):
    """
    Change the evidence privilege mode. Refer to the documentation
    for more information on the function of each mode.
    Usage: /evidence_mod <FFA|Mods|CM|HiddenCM>
    """
    if not arg or arg == client.area.evidence_mod:
        client.send_ooc(
            f'current evidence mod: {client.area.evidence_mod}')
    elif arg in ['FFA', 'Mods', 'CM', 'HiddenCM']:
        if not client.is_mod:
            if client.area.evidence_mod == 'Mods':
                raise ClientError('You must be authorized to change this area\'s evidence mod from Mod-only.')
            if arg == 'Mods':
                raise ClientError('You must be authorized to set the area\'s evidence to Mod-only.')
        client.area.evidence_mod = arg
        client.area.broadcast_evidence_list()
        client.send_ooc(
            f'current evidence mod: {client.area.evidence_mod}')
        database.log_room('evidence_mod', client, client.area, message=arg)
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
    if not client.area.can_cm:
        raise ClientError('You can\'t become a CM in this area')
    if len(client.area.owners) == 0:
        if len(arg) > 0:
            raise ArgumentError(
                'You cannot \'nominate\' people to be CMs when you are not one.'
            )
        client.area.add_owner(client)
        database.log_room('cm.add', client, client.area, target=client, message='self-added')
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
                        f'{c.char_name} [{c.id}] is already a CM here.')
                else:
                    client.area.add_owner(c)
                    database.log_room('cm.add', client, client.area, target=c)
            except ValueError:
                client.send_ooc(
                    f'{id} does not look like a valid ID.')
            except (ClientError, ArgumentError):
                raise
    else:
        raise ClientError('You must be authorized to do that.')


@mod_only(area_owners=True)
def ooc_cmd_uncm(client, arg):
    """
    Remove a case manager from the current area.
    Usage: /uncm <id>
    """
    if len(arg) > 0:
        arg = arg.split()
    else:
        arg = [client.id]
    for _id in arg:
        try:
            _id = int(_id)
            c = client.server.client_manager.get_targets(
                client, TargetType.ID, _id, False)[0]
            if c in client.area.owners:
                client.area.remove_owner(c)
                database.log_room('cm.remove', client, client.area, target=c)
            else:
                client.send_ooc(
                    'You cannot remove someone from CMing when they aren\'t a CM.'
                )
        except ValueError:
            client.send_ooc(
                f'{_id} does not look like a valid ID.')
        except (ClientError, ArgumentError):
            raise


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
    # XXX: Merge with aoprotocol.net_cmd_casea
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

            lookingfor = [p for p, q in
                zip(['defense', 'prosecutor', 'judge', 'juror', 'stenographer'], args[1:])
                if q == '1']

            msg += ', '.join(lookingfor) + '.\r\n=================='

            client.server.send_all_cmd_pred('CASEA', msg, args[1], args[2],
                                            args[3], args[4], args[5], '1')

            client.set_case_call_delay()

            log_data = {k: v for k, v in
                zip(('message', 'def', 'pro', 'jud', 'jur', 'steno'), args)}
            database.log_room('case', client, client.area, message=log_data)
    else:
        raise ClientError(
            'You cannot announce a case in an area where you are not a CM!')


@mod_only()
def ooc_cmd_blockwtce(client, arg):
    """
    Prevent a user from using Witness Testimony/Cross Examination buttons
    as a judge.
    Usage: /blockwtce <id>
    """
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
        database.log_room('blockwtce', client, client.area, target=target)
    client.send_ooc('blockwtce\'d {}.'.format(
        targets[0].char_name))


@mod_only()
def ooc_cmd_unblockwtce(client, arg):
    """
    Allow a user to use WT/CE again.
    Usage: /unblockwtce <id>
    """
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
        database.log_room('unblockwtce', client, client.area, target=target)
    client.send_ooc('unblockwtce\'d {}.'.format(
        targets[0].char_name))


@mod_only()
def ooc_cmd_judgelog(client, arg):
    """
    List the last 10 uses of judge controls in the current area.
    Usage: /judgelog
    """
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


def ooc_cmd_afk(client, arg):
    client.server.client_manager.toggle_afk(client)


@mod_only(area_owners=True)
def ooc_cmd_remote_listen(client, arg):
    """
    Change the remote listen logs to either NONE, IC, OOC or ALL. It will send you those messages from the areas you are an owner of.
    Usage: /remote_listen [option]
    """
    options = {
        'NONE': 0,
        'IC': 1,
        'OOC': 2,
        'ALL': 3,
    }
    if arg == '':
        client.send_ooc(f'Your current option is: {options[client.remote_listen]}')
        return
    try:
        client.remote_listen = options[arg]
    except KeyError:
        raise ArgumentError('Invalid option! Your options are NONE, IC, OOC or ALL.')


def ooc_cmd_testimony(client, arg):
    """
    Display the currently recorded testimony. Optionally, idx can be passed to move to that statement.
    Usage: /testimony [idx]
    """
    if len(client.area.testimony) <= 0:
        client.send_ooc('There is no testimony recorded!')
        return
    args = arg.split()
    if len(args) > 0:
        try:
            if client.area.recording == True:
                client.send_ooc('It is not cross-examination yet!')
                return
            idx = int(args[0]) - 1
            client.area.testimony_send(idx)
            client.area.broadcast_ooc(f'{client.char_name} has moved to Statement {idx+1}.')
        except ValueError:
            raise ArgumentError('Index must be a number!')
        except ClientError:
            raise
        return

    msg = f'Use > IC to progress, < to backtrack, >3 or <3 to go to specific statements.'
    msg += f'\n-- {client.area.testimony_title} --'
    for i, statement in enumerate(client.area.testimony):
        # [15] SHOWNAME
        name = statement[15]
        if name == '' and statement[8] != -1:
            # [8] CID
            name = client.server.char_list[statement[8]]
        txt = statement[4].replace('{', '').replace('}', '')
        here = '  '
        if i == client.area.testimony_index:
            here = '->'
        msg += f'\n{here}[{i+1}] {name}: {txt}'
    client.send_ooc(msg)


@mod_only(area_owners=True)
def ooc_cmd_testimony_clear(client, arg):
    """
    Clear the current testimony.
    Usage: /testimony_clear
    """
    if len(client.area.testimony) <= 0:
        client.send_ooc('There is no testimony recorded!')
        return
    if len(arg) != 0:
        raise ArgumentError('This command does not take any arguments.')
    client.area.testimony.clear()
    client.area.testimony_title = ''
    client.area.broadcast_ooc(f'{client.char_name} cleared the current testimony.')


@mod_only(area_owners=True)
def ooc_cmd_testimony_remove(client, arg):
    """
    Remove the statement at index.
    Usage: /testimony_remove <idx>
    """
    if len(client.area.testimony) <= 0:
        client.send_ooc('There is no testimony recorded!')
        return
    args = arg.split()
    if len(args) <= 0:
        raise ArgumentError('Usage: /testimony_remove <idx>.')
    try:
        idx = int(args[0]) - 1
        client.area.testimony.pop(idx)
        if client.area.testimony_index == idx:
            client.area.testimony_index = -1
        client.area.broadcast_ooc(f'{client.char_name} has removed Statement {idx+1}.')
    except ValueError:
        raise ArgumentError('Index must be a number!')
    except IndexError:
        raise ArgumentError('Index out of bounds!')
    except ClientError:
        raise


@mod_only(area_owners=True)
def ooc_cmd_testimony_amend(client, arg):
    """
    Edit the spoken message of the statement at idx.
    Usage: /testimony_amend <idx> <msg>
    """
    if len(client.area.testimony) <= 0:
        client.send_ooc('There is no testimony recorded!')
        return
    args = arg.split()
    if len(args) < 2:
        raise ArgumentError('Usage: /testimony_remove <idx> <msg>.')
    try:
        idx = int(args[0]) - 1
        lst = list(client.area.testimony[idx])
        lst[4] = "}}}" + args[1:]
        client.area.testimony[idx] = tuple(lst)
        client.area.broadcast_ooc(f'{client.char_name} has amended Statement {idx+1}.')
    except ValueError:
        raise ArgumentError('Index must be a number!')
    except IndexError:
        raise ArgumentError('Index out of bounds!')
    except ClientError:
        raise


@mod_only(area_owners=True)
def ooc_cmd_testimony_swap(client, arg):
    """
    Swap the two statements by idx.
    Usage: /testimony_swap <idx1> <idx2>
    """
    if len(client.area.testimony) <= 0:
        client.send_ooc('There is no testimony recorded!')
        return
    args = arg.split()
    if len(args) < 2:
        raise ArgumentError('Usage: /testimony_remove <idx1> <idx2>.')
    try:
        idx1 = int(args[0]) - 1
        idx2 = int(args[1]) - 1
        client.area.testimony[idx2], client.area.testimony[idx1] = client.area.testimony[idx1], client.area.testimony[idx2]
        client.area.broadcast_ooc(f'{client.char_name} has swapped Statements {idx1+1} and {idx2+1}.')
    except ValueError:
        raise ArgumentError('Index must be a number!')
    except IndexError:
        raise ArgumentError('Index out of bounds!')
    except ClientError:
        raise