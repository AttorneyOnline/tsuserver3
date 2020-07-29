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


class EvidenceList:
    """Contains a list of evidence items."""
    limit = 35

    class Evidence:
        """Represents a single evidence item."""
        def __init__(self, name, desc, image, pos):
            self.name = name
            self.desc = desc
            self.image = image
            self.public = False
            self.pos = pos

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
            return {'name': self.name, 'desc': self.desc, 'image': self.image, 'pos': self.pos}

    def __init__(self):
        self.evidences = []

    def can_see(self, evi, pos):  # used with hiddenCM ebidense
        pos = pos.strip(' ')
        for p in evi.pos.strip(' ').split(','):
            if p == 'all' or (pos != '' and pos == p):
                return True
        return False

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
            # poses = cmd[7:-1]
            #broken with extra shorthands
            # for pos in poses.strip(' ').split(','):
            #     if not (pos in self.poses['all']) and pos != 'pos':
            #         return False
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
        if len(self.evidences) >= self.limit:
            client.send_ooc(
                f'You can\'t have more than {self.limit} evidence items at a time.'
            )
            return
        if client in client.area.owners or client.is_mod:
            pos = 'pos'
            self.evidences.append(self.Evidence(
                name, description, image, pos))
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
                    desc = f'<owner={evi.pos}>\n{evi.desc}'
                evi_list.append(
                    self.Evidence(evi.name, desc,
                                  evi.image, evi.pos).to_string())
            elif self.can_see(self.evidences[i], client.pos):
                nums_list.append(i+1)
                evi_list.append(self.evidences[i].to_string())
        return nums_list, evi_list

    def import_evidence(self, data):
        for evi in data:
            name, description, image, pos = evi['name'], evi['desc'], evi['image'], evi['pos']
            self.evidences.append(self.Evidence(name, description, image, pos))

    def del_evidence(self, client, id):
        """
        Delete an evidence item.
        :param client: origin
        :param id: evidence ID

        """
        if not self.login(client):
            return
        if not client in client.area.owners and not client.is_mod:
            id = client.evi_list[id+1]-1
        self.evidences.pop(id)

    def edit_evidence(self, client, id, arg):
        """
        Modify an evidence item.
        :param client: origin
        :param id: evidence ID
        :param arg: evidence information

        """
        if not self.login(client):
            return
        if client in client.area.owners or client.is_mod:
            if client.area.evidence_mod == 'HiddenCM':
                if self.correct_format(client, arg[1]):
                    lines = arg[1].split('\n')
                    cmd = lines[0].strip(' ')  # remove all whitespace
                    poses = cmd[7:-1]
                    self.evidences[id] = self.Evidence(arg[0], '\n'.join(lines[1:]), arg[2], poses)
                else:
                    client.send_ooc('You entered a bad pos.')
                    return
            else:
                self.evidences[id] = self.Evidence(arg[0], arg[1], arg[2], arg[3])
        else:
            # Are you serious? This is absolutely fucking mental.
            # Server sends evidence to client in an indexed list starting from 1.
            # Client sends evidence updates to server using an index starting from 0.
            # This needs a complete overhaul.
            idx = client.evi_list[id+1]-1
            self.evidences[idx] = self.Evidence(
                arg[0], arg[1], arg[2], self.evidences[idx].pos)
