class EvidenceList:
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
            
    def __init__(self):
        self.evidences = []
        self.poses = {'def':['def', 'hld'], 'pro':['pro', 'hlp'], 'wit':['wit'], 'hlp':['hlp', 'pro'], 'hld':['hld', 'def'], 'jud':['jud'], 'all':['hlp', 'hld', 'wit', 'jud', 'pro', 'def', '']}
        
    def add_evidence(self, client, name, description, image, pos = 'all'):
        if client.area.evidence_mod == 'FFA':
            pass
        if client.area.evidence_mod == 'Mods':
            #TODO evidences only for mods
            return
        if client.area.evidence_mod == 'CM':
            if not client.is_cm and not client.is_mod:
                return
        if client.area.evidence_mod == 'HiddenCM':
            #TODO evidences visible only after presenting
            return
        self.evidences.append(self.Evidence(name, description, image, pos))
        
    def evidence_swap(self, client, id1, id2):
        if client.area.evidence_mod == 'FFA':
            pass
        if client.area.evidence_mod == 'Mods':
            #TODO evidences only for mods
            return
        if client.area.evidence_mod == 'CM':
            if not client.is_cm and not client.is_mod:
                return
        if client.area.evidence_mod == 'HiddenCM':
            #TODO evidences visible only after presenting
            return
        self.evidences[id1], self.evidences[id2] = self.evidences[id2], self.evidences[id1]
            
    def create_evi_list(self, client):
        evi_list = []
        for i in range(len(self.evidences)):
            if client.pos in self.poses[self.evidences[i].pos]:
                evi_list.append(i)
        return evi_list
    
    def del_evidence(self, client, id):
        if client.area.evidence_mod == 'FFA':
            pass
        if client.area.evidence_mod == 'Mods':
            #TODO evidences only for mods
            return
        if client.area.evidence_mod == 'CM':
            if not client.is_cm and not client.is_mod:
                return
        if client.area.evidence_mod == 'HiddenCM':
            #TODO evidences visible only after presenting
            return
        self.evidences.pop(id)
        
    def edit_evidence(self, client, id, arg):
        if client.area.evidence_mod == 'FFA':
            pass
        if client.area.evidence_mod == 'Mods':
            #TODO evidences only for mods
            return
        if client.area.evidence_mod == 'CM':
            if not client.is_cm and not client.is_mod:
                return
        if client.area.evidence_mod == 'HiddenCM':
            #TODO evidences visible only after presenting
            return
        self.evidences[id] = self.Evidence(arg[0], arg[1], arg[2], arg[3])