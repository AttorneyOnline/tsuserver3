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
    limit = 35

    class Evidence:
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
            sequence = (self.name, self.desc, self.image)
            return '&'.join(sequence)

        def to_dict(self):
            return {'name': self.name, 'desc': self.desc, 'image': self.image, 'pos': self.pos}

    def __init__(self):
        self.evidences = []
        self.poses = {'def': ['def'],
                      'pro': ['pro'],
                      'wit': ['wit'],
                      'sea': ['sea'],
                      'hlp': ['hlp'],
                      'hld': ['hld'],
                      'jud': ['jud'],
                      'jur': ['jur'],
                      'defense': ['def', 'hld'],
                      'prosecution': ['pro', 'hlp'],
                      'benches': ['def', 'hld', 'pro', 'hlp'],
                      'witness': ['wit', 'sea'],
                      'judge': ['jud', 'jur'],
                      'all': ['hlp', 'hld', 'wit', 'jud', 'pro', 'def', 'jur', 'sea', ''],
                      'pos': []}

    def can_see(self, evi, pos):  # used with hiddenCM ebidense
        for p in evi.pos.strip(' ').split(','):
            poslist = self.poses[p]
            if pos in poslist:
                return True
        return False

    def login(self, client):
        if client.area.evidence_mod == 'FFA':
            return True
        if client.area.evidence_mod == 'Mods':
            if client.is_mod:
                return True
        if client.area.evidence_mod == 'CM':
            if client.is_cm or client.is_mod:
                return True
        if client.area.evidence_mod == 'HiddenCM':
            if client.is_cm or client.is_mod:
                return True
        return False

    def correct_format(self, client, desc):
        if client.area.evidence_mod != 'HiddenCM':
            return True
        else:
            # correct format: <owner=pos,pos,pos>\ndesc
            lines = desc.split('\n')
            cmd = lines[0].strip(' ') #remove all whitespace
            if cmd[:7] == '<owner=' and cmd.endswith('>'):
                poses = cmd[7:-1]
                #broken with extra shorthands
                # for pos in poses.strip(' ').split(','):
                #     if not (pos in self.poses['all']) and pos != 'pos':
                #         return False
                return True
            return False

    def add_evidence(self, client, name, description, image, pos='all'):
        if len(self.evidences) >= self.limit:
            client.send_host_message(
                'You can\'t have more than {} evidence items at a time.'.format(self.limit))
            return
        if self.login(client):
            if client.area.evidence_mod == 'HiddenCM':
                pos = 'pos'
            self.evidences.append(self.Evidence(
                name, description, image, pos))
        elif client.area.evidence_mod == 'HiddenCM':
            if not client.hub.status.lower().startswith('rp-strict'):
                pos = client.pos
                self.evidences.append(self.Evidence(
                    name, description, image, pos))

    def evidence_swap(self, client, id1, id2):
        if self.login(client):
            self.evidences[id1], self.evidences[id2] = self.evidences[id2], self.evidences[id1]

    def create_evi_list(self, client):
        evi_list = []
        nums_list = [0]
        for i in range(len(self.evidences)):
            if client.area.evidence_mod == 'HiddenCM' and self.login(client):
                nums_list.append(i+1)
                evi = self.evidences[i]
                evi_list.append(self.Evidence(evi.name, '<owner={}>\n{}'.format(evi.pos, evi.desc), evi.image,
                                              evi.pos).to_string())
            elif self.can_see(self.evidences[i], client.pos):
                nums_list.append(i+1)
                evi_list.append(self.evidences[i].to_string())
        return nums_list, evi_list

    def import_evidence(self, data):
        for evi in data:
            name, description, image, pos = evi['name'], evi['desc'], evi['image'], evi['pos']
            self.evidences.append(self.Evidence(name, description, image, pos))

    def del_evidence(self, client, id):
        if self.login(client):
            self.evidences.pop(id)
        elif client.area.evidence_mod == 'HiddenCM':
            if not client.hub.status.lower().startswith('rp-strict'):
                # Are you serious? This is absolutely fucking mental.
                # Server sends evidence to client in an indexed list starting from 1.
                # Client sends evidence updates to server using an index starting from 0.
                # This needs a complete overhaul.
                idx = client.evi_list[id+1]-1
                # self.evidences[idx].pos = 'pos' #simply hide it lo
                self.evidences.pop(idx)

    def edit_evidence(self, client, id, arg):
        if self.login(client):
            #evidence-based hub loading support, may be discontinued in the future.
            if(arg[0] == '/loadhub'):
                if not self.client.is_mod and not self.client.is_cm:
                    self.client.send_host_message(
                        "You must be authorized to do that.")
                    return
                try:
                    self.client.hub.load(arg[1].strip())
                    self.client.send_host_message("Loading hub save data...")
                    self.evidences.pop[id]
                except:
                    self.client.send_host_message(
                        "Could not load hub save data! Try pressing the [X] and make sure if your save data is correct.")
                return
            #END evidence-based hub loading support

            if client.area.evidence_mod == 'HiddenCM':
                if self.correct_format(client, arg[1]):
                    lines = arg[1].split('\n')
                    cmd = lines[0].strip(' ')  # remove all whitespace
                    poses = cmd[7:-1]
                    self.evidences[id] = self.Evidence(arg[0], '\n'.join(lines[1:]), arg[2], poses)
                else:
                    client.send_host_message('You entered a bad pos.')
                    return
            else:
                self.evidences[id] = self.Evidence(arg[0], arg[1], arg[2], arg[3])
        elif client.area.evidence_mod == 'HiddenCM':
            if not client.hub.status.lower().startswith('rp-strict'):
                # Are you serious? This is absolutely fucking mental.
                # Server sends evidence to client in an indexed list starting from 1.
                # Client sends evidence updates to server using an index starting from 0.
                # This needs a complete overhaul.
                idx = client.evi_list[id+1]-1
                self.evidences[idx] = self.Evidence(
                    arg[0], arg[1], arg[2], self.evidences[idx].pos)
