import yaml
import os
import copy

class Database:

    def __init__(self, server):
        self.server = server
        self.setup_database()

    def setup_database(self):
        self.character_data = self.make_character_database()
        self.music_data = self.make_music_database()
        self.user_data = self.make_user_database()
        self.check_char_list()
        self.check_music_list()
        self.check_user_list()
        self.write_character_data()
        self.write_music_data()

    def make_character_database(self):
        data = []
        try:
            with open('storage/stats/chars.yaml', 'r') as char:
                data = yaml.load(char)
        except FileNotFoundError:
            if not os.path.exists('storage/stats/'):
                os.makedirs('storage/stats/')
            with open('storage/stats/chars.yaml', 'w') as char:
                yaml.dump([], char, default_flow_style = False)
        except ValueError:
            return
        if not data:
            data = self.create_new_char_database()
        return data

    def write_character_data(self):
        data = copy.deepcopy(self.character_data)
        with open('storage/stats/chars.yaml', 'w') as cdata:
            yaml.dump(data, cdata, default_flow_style = False)

    def check_char_list(self):
        for char in self.character_data:
            obj = self.character_data[char]
            for index in list(obj.indexes.keys()):
                if index not in obj.data:
                    self.character_data[char].data[index] = obj.indexes[index]

    def make_music_database(self):
        data = []
        try:
            with open('storage/stats/music.yaml', 'r') as char:
                    data =  yaml.load(char)
        except FileNotFoundError:
            if not os.path.exists('storage/stats/'):
                os.makedirs('storage/stats/')
            with open('storage/stats/music.yaml', 'w') as char:
                yaml.dump([], char, default_flow_style = False)
        except ValueError:
            return
        if not data:
            data = self.create_new_music_database()
        return data


    def write_music_data(self):
        data = copy.deepcopy(self.music_data)
        with open('storage/stats/music.yaml', 'w') as mdata:
            yaml.dump(data, mdata, default_flow_style = False)

    def check_music_list(self):
        for char in self.music_data:
            obj = self.music_data[char]
            for index in list(obj.indexes.keys()):
                if index not in obj.data:
                    obj.data[index] = obj.indexes[index]

    def check_user_list(self):
        for char in self.user_data:
            obj = self.user_data[char]
            for index in list(obj.indexes.keys()):
                if index not in obj.data:
                    obj.data[index] = obj.indexes[index]

    def make_user_database(self):
        data = {}
        try:
            with open('storage/stats/user.yaml', 'r') as char:
                data = yaml.load(char)
        except FileNotFoundError:
            if not os.path.exists('storage/stats/'):
                os.makedirs('storage/stats/')
            with open('storage/stats/user.yaml', 'w') as char:
                yaml.dump([], char, default_flow_style = False)
        except ValueError:
            return
        return data

    def write_user_data(self):
        data = copy.deepcopy(self.user_data)
        with open('storage/stats/user.yaml', 'w') as udata:
            yaml.dump(data, udata, default_flow_style = False)

    def create_new_char_database(self):
        data = {}
        for i, ch in enumerate(self.server.char_list):
            data[i] = charData(i, ch.lower())
        return data

    def create_new_music_database(self):
        data = {}
        i = 0
        for cat in self.server.music_list:
            for song in cat['songs']:
                data[song['name'].lower()] = musicData(i, song['name'].lower())
        return data

    def character_picked(self, cid):
        self.character_data[cid].data["picked"] += 1

    def char_talked(self, cid, ipid, status):
        if status.lower() == 'idle':
            self.character_data[cid].data["times_talked_idle"] += 1
            self.user_data[ipid].data["times_talked_idle"] += 1
        if status.lower() == 'building-open' or status.lower() == 'building-full' or status.lower() == 'recess':
            self.character_data[cid].data["times_talked_build_recess"] += 1
            self.user_data[ipid].data["times_talked_build_recess"] += 1
        if status.lower() == 'casing-open' or status.lower() == 'casing-full':
            self.character_data[cid].data["times_talked_casing"] += 1
            self.user_data[ipid].data["times_talked_casing"] += 1

    def music_played(self, name, status):
        if status.lower() == 'idle':
            self.music_data[name.lower()].data["times_talked_idle"] += 1
        if status.lower() == 'building-open' or status.lower() == 'building-full' or status.lower() == 'recess':
            self.music_data[name.lower()].data["times_played_build_recess"] += 1
        if status.lower() == 'casing-open' or status.lower() == 'casing-full':
            self.music_data[name.lower()].data["times_played_casing"] += 1

    def connect_data(self, ipid, hdid):
        if ipid not in self.user_data:
            self.user_data[ipid] = userData(ipid, hdid)
        else:
            self.user_data[ipid].data["times_connected"] += 1
            if hdid not in self.user_data[ipid].hdid:
                self.user_data[ipid].hdid.append(hdid)

    def kicked_user(self, ipid):
        try:
            self.user_data[ipid].data["times_kicked"] += 1
        except IndexError:
            return

    def muted_user(self, ipid):
        try:
            self.user_data[ipid].data["times_muted"] += 1
        except IndexError:
            return

    def banned_user(self, ipid):
        try:
            self.user_data[ipid].data["times_banned"] += 1
        except IndexError:
            return

    def user_voted(self, ipid):
        try:
            self.user_data[ipid].data["times_voted"] += 1
        except IndexError:
            return

    def user_doc(self, ipid):
        try:
            self.user_data[ipid].data["times_doc"] += 1
        except IndexError:
            return

    def save_alldata(self):
        self.write_user_data()
        self.write_character_data()
        self.write_music_data()

class charData:

    indexes =  {
        "picked": 0,
        "times_talked_idle": 0,
        "times_talked_build_recess": 0,
        "times_talked_casing": 0,
    }

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.data = {}
        for i in self.indexes:
            self.data[i] = self.indexes[i]

class musicData:

    indexes =  {
        "times_played_idle": 0,
        "times_played_build_recess": 0,
        "times_played_casing": 0,
    }

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.data = {}
        for i in self.indexes:
            self.data[i] = self.indexes[i]

class userData:

    indexes =  {
        "times_connected": 0,
        "times_talked_idle": 0,
        "times_talked_build_recess": 0,
        "times_talked_casing": 0,
        "times_kicked": 0,
        "times_muted": 0,
        "times_banned": 0,
        "times_voted": 0,
        "times_doc": 0,
    }

    def __init__(self, id, hdid):
        self.ipid = id
        self.hdid = [hdid]
        self.data = {}
        for i in self.indexes:
            self.data[i] = self.indexes[i]

    def add_hdid(self, hdid):
        self.hdid.append(hdid)