# KFO-Server, an Attorney Online server
#
# Copyright (C) 2020 Crystalwarrior <varsash@gmail.com>
#
# Derivative of tsuserver3, an Attorney Online server. Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
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


class EvidenceList:
    """Contains a list of evidence items."""
    limit = 35

    class Evidence:
        """Represents a single evidence item."""
        def __init__(self, name, desc, image, pos, can_hide_in=False):
            self.name = name
            self.desc = desc
            self.image = image
            self.public = False
            self.pos = pos
            self.can_hide_in = can_hide_in
            self.hiding_client = None

        def set_name(self, name):
            self.name = name

        def set_desc(self, desc):
            self.desc = desc

        def set_image(self, image):
            self.image = image

        def to_string(self):
            """Serialize data to the AO protocol."""
            sequence = (self.name, self.desc, self.image)
            return '&'.join(sequence)

        def to_dict(self):
            return {'name': self.name, 'desc': self.desc, 'image': self.image, 'pos': self.pos, 'can_hide_in': self.can_hide_in}

    def __init__(self):
        self.evidences = []

    def can_see(self, evi, pos):  # used with hiddenCM ebidense
        pos = pos.strip(' ')
        for p in evi.pos.strip(' ').split(','):
            if p == 'all' or (pos != '' and pos == p):
                return True
        return False

    def can_hide_in(self, evi):
        return evi.can_hide_in

    def login(self, client):
        """
        Determine whether or not evidence can be modified.
        :param client: origin

        """
        if client.area.evidence_mod == 'FFA' or client.area.evidence_mod == 'HiddenCM':
            return True
        elif client.area.evidence_mod == 'Mods' and \
            not client.is_mod:
            return False
        elif client.area.evidence_mod == 'CM' and \
            not client in client.area.owners and not client.is_mod:
            return False
        return True

    def correct_format(self, client, desc):
        """
        Check whether or not an evidence item contains a correct
        `<owner = [pos]>` metadata, if HiddenCM mode is on.
        :param client: origin
        :param desc: evidence description

        """
        if client.area.evidence_mod != 'HiddenCM':
            return True
        # correct format: <owner=pos,pos,pos>\ndesc
        lines = desc.split('\n')
        cmd = lines[0].strip(' ') #remove all whitespace
        if cmd[:7] == '<owner=' and cmd.endswith('>'):
            return True
        return False

    def add_evidence(self, client, name, description, image, pos='all'):
        """
        Add an evidence item.
        :param client: origin
        :param name: evidence name
        :param description: evidence description
        :param image: evidence image file
        :param pos: positions for which evidence will be shown
        (Default value = 'all')

        """
        if not self.login(client):
            return
        if client.area.dark:
            return
        if len(self.evidences) >= self.limit:
            client.send_ooc(
                f'You can\'t have more than {self.limit} evidence items at a time.'
            )
            return
        if client in client.area.owners or client.is_mod:
            pos = 'hidden'
            self.evidences.append(self.Evidence(
                name, description, image, pos))
        else:
            if len(client.area.pos_lock) > 0:
                pos = client.pos
            else:
                pos = 'all'
            self.evidences.append(self.Evidence(
                name, description, image, pos))

    def evidence_swap(self, client, id1, id2):
        """
        Swap two evidence items.
        :param client: origin
        :param id1: evidence ID 1
        :param id2: evidence ID 2

        """
        if not self.login(client):
            return

        self.evidences[id1], self.evidences[id2] = self.evidences[
            id2], self.evidences[id1]

    def create_evi_list(self, client):
        """
        Compose an evidence list to send to a client.
        :param client: client to send list to

        """
        evi_list = []
        nums_list = [0]
        for i in range(len(self.evidences)):
            if client in client.area.owners or client.is_mod:
                nums_list.append(i+1)
                evi = self.evidences[i]
                desc = evi.desc
                if client.area.evidence_mod == 'HiddenCM':
                    can_hide_in = int(evi.can_hide_in)
                    desc = f'<owner={evi.pos}>\n<can_hide_in={can_hide_in}>\n{evi.desc}'
                evi_list.append(
                    self.Evidence(evi.name, desc,
                                  evi.image, evi.pos).to_string())
            elif not client.area.dark and self.can_see(self.evidences[i], client.pos):
                nums_list.append(i+1)
                evi_list.append(self.evidences[i].to_string())
        return nums_list, evi_list

    def import_evidence(self, data):
        for evi in data:
            name, desc, image, pos, can_hide_in = '<name>', '<desc>', '', 'all', False
            if 'name' in evi:
                name = evi['name']
            if 'desc' in evi:
                desc = evi['desc']
            if 'image' in evi:
                image = evi['image']
            if 'pos' in evi:
                pos = evi['pos']
            if 'can_hide_in' in evi:
                can_hide_in = evi['can_hide_in'] == True
            self.evidences.append(self.Evidence(name, desc, image, pos, can_hide_in))

    def del_evidence(self, client, id):
        """
        Delete an evidence item.
        :param client: origin
        :param id: evidence ID

        """
        if not self.login(client):
            return
        if client.area.dark:
            return
        evi = self.evidences[id]
        if not client in client.area.owners and not client.is_mod:
            id = client.evi_list[id+1]-1
            evi = self.evidences[id]
            if client.area.evidence_mod == 'HiddenCM':
                if evi.pos != 'hidden':
                    evi.name = f'🚮{evi.name}'
                    evi.desc = f'(🚮Deleted by [{client.id}] {client.showname} ({client.name}))\n{evi.desc}'
                    evi.pos = 'hidden'
            else:
                self.evidences.pop(id)
        else:
            self.evidences.pop(id)
        c = evi.hiding_client
        if c != None:
            c.hide(False)
            c.area.broadcast_area_list(c)
            c.send_ooc(f'You discover {c.showname} in the {evi.name}!')

    def edit_evidence(self, client, id, arg):
        """
        Modify an evidence item.
        :param client: origin
        :param id: evidence ID
        :param arg: evidence information

        """
        if not self.login(client):
            return
        if client.area.dark:
            return
        if client in client.area.owners or client.is_mod:
            if client.area.evidence_mod == 'HiddenCM':
                if self.correct_format(client, arg[1]):
                    lines = arg[1].split('\n')
                    cmd = lines[0].strip(' ')  # remove whitespace at beginning and end of string
                    poses = cmd[7:-1]
                    can_hide_in = lines[1].strip(' ')[13:-1] == "1"
                    self.evidences[id] = self.Evidence(arg[0], '\n'.join(lines[2:]), arg[2], poses, can_hide_in)
                else:
                    client.send_ooc('You entered a bad pos! Make sure to have <owner=pos> at the top, where "pos" is the /pos this evidence should show up in. Put in "all" if you want it to show up in all pos, or "hidden" for no pos.')
                    return
            else:
                self.evidences[id] = self.Evidence(arg[0], arg[1], arg[2], arg[3])
        else:
            # Are you serious? This is absolutely fucking mental.
            # Server sends evidence to client in an indexed list starting from 1.
            # Client sends evidence updates to server using an index starting from 0.
            # This needs a complete overhaul.
            idx = client.evi_list[id+1]-1
            # c = self.evidences[idx].hiding_client
            # if c != None:
            #     c.hide(False)
            #     c.area.broadcast_area_list(c)
            #     client.send_ooc(f'You discover {c.showname} in the {self.evidences[idx].name}!')
            self.evidences[idx] = self.Evidence(
                arg[0], arg[1], arg[2], self.evidences[idx].pos)
