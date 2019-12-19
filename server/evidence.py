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

    def __init__(self):
        self.evidences = []
        self.poses = {
            'def': ['def', 'hld'],
            'pro': ['pro', 'hlp'],
            'wit': ['wit', 'sea'],
            'sea': ['sea', 'wit'],
            'hlp': ['hlp', 'pro'],
            'hld': ['hld', 'def'],
            'jud': ['jud', 'jur'],
            'jur': ['jur', 'jud'],
            'all':
            ['hlp', 'hld', 'wit', 'jud', 'pro', 'def', 'jur', 'sea', ''],
            'pos': []
        }

    def login(self, client):
        """
        Determine whether or not evidence can be modified.
        :param client: origin

        """
        if client.area.evidence_mod == 'FFA':
            return True
        elif client.area.evidence_mod == 'Mods' and \
            not client.is_mod:
            return False
        elif client.area.evidence_mod == 'CM' and \
            not client in client.area.owners and not client.is_mod:
            return False
        elif client.area.evidence_mod == 'HiddenCM' and \
            not client in client.area.owners and not client.is_mod:
            return False
        else:
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
        elif desc[:9] == '<owner = ' and desc[9:12] in self.poses and desc[
                12:14] == '>\n':
            # correct format: <owner = pos>\ndesc
            return True
        else:
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

        if client.area.evidence_mod == 'HiddenCM':
            pos = 'pos'
        if len(self.evidences) >= self.limit:
            client.send_ooc(
                f'You can\'t have more than {self.limit} evidence items at a time.'
            )
        else:
            self.evidences.append(self.Evidence(name, description, image, pos))

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
            if client.area.evidence_mod == 'HiddenCM' and self.login(client):
                nums_list.append(i + 1)
                evi = self.evidences[i]
                evi_list.append(
                    self.Evidence(evi.name, f'<owner = {evi.pos}>\n{evi.desc}',
                                  evi.image, evi.pos).to_string())
            elif client.pos in self.poses[self.evidences[i].pos]:
                nums_list.append(i + 1)
                evi_list.append(self.evidences[i].to_string())
        return nums_list, evi_list

    def del_evidence(self, client, id):
        """
        Delete an evidence item.
        :param client: origin
        :param id: evidence ID

        """
        if not self.login(client):
            return

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

        if client.area.evidence_mod == 'HiddenCM' and self.correct_format(
                client, arg[1]):
            self.evidences[id] = self.Evidence(arg[0], arg[1][14:], arg[2],
                                               arg[1][9:12])
        elif client.area.evidence_mod == 'HiddenCM':
            client.send_ooc('You entered a wrong pos.')
        else:
            self.evidences[id] = self.Evidence(arg[0], arg[1], arg[2], arg[3])
