# tsuserver3, an Attorney Online server
#
# Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import os
import time

import yaml

from server import logger
from server.exceptions import ServerError


class ServerpollManager:
    def __init__(self, server):
        self.server = server
        self.poll_list = []
        self.poll_display = []
        self.current_poll = []
        self.load_poll_list()
        self.vote = []
        self.slots = []
        self.voting = 0
        self.voting_at = 0

    def load_poll_list(self):
        try:
            with open('storage/poll/polllist.json', 'r') as poll_list_file:
                self.poll_list = json.load(poll_list_file)
        except FileNotFoundError:
            if not os.path.exists('storage/poll/'):
                os.makedirs('storage/poll/')
            with open('storage/poll/polllist.json', 'w+') as poll_list_file:
                json.dump([], poll_list_file)
            return
        except ValueError:
            return

    def write_poll_list(self):
        with open('storage/poll/polllist.json', 'w+') as poll_list_file:
            json.dump(self.poll_list, poll_list_file)

    def show_poll_list(self):
        output = [item[0] for item in self.poll_list]
        return output

    def poll_number(self):
        return len(self.poll_list)

    def add_poll(self, value):
        test = time.strftime('%y-%m-%d %H%M-%S')
        if not ([item for item in self.poll_list if item[0] == value]):
            if len(self.poll_list) < self.server.config['poll_slots']:
                self.poll_list.append([value, test])
                tmp = time.strftime('%y-%m-%d %H:%M:%S')
                newfile = {
                    'name': value,
                    'polldetail': None,
                    'multivote': False,
                    'choices': ["Yes", "No"],
                    'votes': {"yes": 0, "no": 0},
                    'created': tmp,
                    'log': [],
                    'faillog': [],
                }
                with open('storage/poll/{} \'{}\'.yaml'.format(test, value), 'w+') as file:
                    yaml.dump(newfile, file, default_flow_style=False)
                    logger.log_serverpoll('Poll \'{}\' added successfully.'.format(value))
            else:
                logger.log_serverpoll('Failed to add poll. Reason: The poll queue is full.')
                raise ServerError('The Poll Queue is full!')
        else:
            logger.log_serverpoll('Failed to add poll. Reason: This poll already exists.')
            raise ServerError('This poll already exists.')
        self.write_poll_list()

    def remove_poll(self, value):
        if ([i for i in self.poll_list if i[0] == "{}".format(value)]):
            self.poll_list = [i for i in self.poll_list if i[0] != "{}".format(value)]
            logger.log_serverpoll('Poll \'{}\' removed.'.format(value))
        elif value == "all":
            self.poll_list = []
            logger.log_serverpoll('All polls removed.')
        else:
            logger.log_serverpoll('Poll removal failed. Reason: The specified poll does not exist.')
            raise ServerError('The specified poll does not exist.')
        self.write_poll_list()

    def polldetail(self, value, detail):
        for i in self.poll_list:
            if i[0].lower() == value.lower():
                stream = open('storage/poll/{} \'{}\'.yaml'.format(i[1], i[0]), 'r')
                hold = yaml.load(stream)
                hold['polldetail'] = detail
                write = open('storage/poll/{} \'{}\'.yaml'.format(i[1], i[0]), 'w+')
                yaml.dump(hold, write, default_flow_style=False)
                return 1
        return 0

    def returndetail(self, value):
        for i in self.poll_list:
            if i[0].lower() == value.lower():
                stream = open('storage/poll/{} \'{}\'.yaml'.format(i[1], i[0]), 'r')
                hold = yaml.load(stream)
                return hold['polldetail']

    def returnmulti(self, value):
        for i in self.poll_list:
            if i[0].lower() == value.lower():
                stream = open('storage/poll/{} \'{}\'.yaml'.format(i[1], i[0]), 'r')
                hold = yaml.load(stream)
                return hold['multivote']

    def poll_exists(self, value):
        if [i for i in self.poll_list if i[0] == "{}".format(value)]:
            return True
        else:
            return False

    def load_votelist(self, value):
        if [i for i in self.poll_list if i[0] == "{}".format(value)]:
            poll_selected = [i[1] for i in self.poll_list if i[0] == "{}".format(value)]
            self.current_poll = ('{} \'{}\''.format("".join(poll_selected), value))
        else:
            return

    def get_votelist(self, value):
        try:
            if [i for i in self.poll_list if i[0] == "{}".format(value)]:
                poll_selected = [i[1] for i in self.poll_list if i[0] == "{}".format(value)]
                output = ('{} \'{}\''.format("".join(poll_selected), value))
                stream = open('storage/poll/{}.yaml'.format(output), 'r')
                stream2 = yaml.load(stream)
                log = stream2['log']
                return log
            else:
                return None
        except FileNotFoundError:
            raise ServerError('The specified poll has no file associated with it.')
        except IndexError:
            raise ServerError('The poll list is currently empty.')

    def get_poll_choices(self, value):
        try:
            if [i for i in self.poll_list if i[0] == "{}".format(value)]:
                poll_selected = [i[1] for i in self.poll_list if i[0] == "{}".format(value)]
                output = ('{} \'{}\''.format("".join(poll_selected), value))
                stream = open('storage/poll/{}.yaml'.format(output), 'r')
                stream2 = yaml.load(stream)
                choices = stream2['choices']
                return choices
            else:
                return None
        except FileNotFoundError:
            raise ServerError('The specified poll has no file associated with it.')
        except IndexError:
            return

    def clear_poll_choice(self, value):
        try:
            if [i for i in self.poll_list if i[0] == "{}".format(value)]:
                poll_selected = [i[1] for i in self.poll_list if i[0] == "{}".format(value)]
                output = ('{} \'{}\''.format("".join(poll_selected), value))
                stream = open('storage/poll/{}.yaml'.format(output), 'r')
                stream2 = yaml.load(stream)
                stream2['choices'] = []
                stream2['votes'] = {}
                with open('storage/poll/{}.yaml'.format(output), 'w+') as votelist_file:
                    yaml.dump(stream2, votelist_file, default_flow_style=False)
                return stream2['choices']
            else:
                return None
        except FileNotFoundError:
            raise ServerError('The specified poll has no file associated with it.')
        except IndexError:
            return

    def remove_poll_choice(self, client, value, remove):
        try:
            if [i for i in self.poll_list if i[0] == "{}".format(value)]:
                poll_selected = [i[1] for i in self.poll_list if i[0] == "{}".format(value)]
                output = ('{} \'{}\''.format("".join(poll_selected), value))
                stream = open('storage/poll/{}.yaml'.format(output), 'r')
                stream2 = yaml.load(stream)
                choices = stream2['choices']
                if not remove in choices:
                    client.send_host_message('Item is not a choice.')
                    return
                stream2['choices'] = [x for x in choices if not x == remove]
                stream2['votes'].pop(remove.lower())
                with open('storage/poll/{}.yaml'.format(output), 'w+') as votelist_file:
                    yaml.dump(stream2, votelist_file, default_flow_style=False)
                return stream2['choices']
            else:
                return None
        except FileNotFoundError:
            raise ServerError('The specified poll has no file associated with it.')
        except IndexError:
            return

    def add_poll_choice(self, client, value, add):
        try:
            if [i for i in self.poll_list if i[0] == "{}".format(value)]:
                poll_selected = [i[1] for i in self.poll_list if i[0] == "{}".format(value)]
                output = ('{} \'{}\''.format("".join(poll_selected), value))
                stream = open('storage/poll/{}.yaml'.format(output), 'r')
                stream2 = yaml.load(stream)
                if add.lower() in [x.lower() for x in stream2['choices']]:
                    client.send_host_message('Item already a choice.')
                    return
                stream2['choices'].append(str(add))
                stream2['votes'][add.lower()] = 0
                with open('storage/poll/{}.yaml'.format(output), 'w+') as votelist_file:
                    yaml.dump(stream2, votelist_file, default_flow_style=False)
                return stream2['choices']
            else:
                return None
        except FileNotFoundError:
            raise ServerError('The specified poll has no file associated with it.')
        except IndexError:
            return

    def make_multipoll(self, value):
        try:
            if [i for i in self.poll_list if i[0] == "{}".format(value)]:
                poll_selected = [i[1] for i in self.poll_list if i[0] == "{}".format(value)]
                output = ('{} \'{}\''.format("".join(poll_selected), value))
                stream = open('storage/poll/{}.yaml'.format(output), 'r')
                stream2 = yaml.load(stream)
                stream2['multivote'] = not stream2['multivote']
                with open('storage/poll/{}.yaml'.format(output), 'w+') as votelist_file:
                    yaml.dump(stream2, votelist_file, default_flow_style=False)
                return stream2['choices']
            else:
                return None
        except FileNotFoundError:
            raise ServerError('The specified poll has no file associated with it.')
        except IndexError:
            return

    def add_vote(self, value, vote, client):
        tmp = time.strftime('%y-%m-%d %H:%M:%S')
        data_c = self.server.stats_manager.user_data[client.ipid]
        try:
            # Open that shit up and extract the important parts.
            poll_voting = []
            for poll in self.poll_list:
                if poll[0].lower() == value.lower():
                    poll_voting = poll
                    break
            if not poll_voting:
                raise ServerError('Poll not found.')
            stream = open('storage/poll/{} \'{}\'.yaml'.format(poll_voting[1], poll_voting[0]), 'r')
            self.vote = yaml.load(stream)
            log = self.vote["log"]
            ipid_voted = self.check_ipid(log, client)
            hdid_voted = self.check_hdid(log, client)
            if (ipid_voted or hdid_voted) and (not self.vote['multivote']):
                # Now to log their failed vote
                self.vote['faillog'] += (['FAILED VOTE', tmp, client.ipid, client.hdid, vote,
                                      "{} ({}) at area {}".format(client.name, client.get_char_name(),
                                                                  client.area.name),
                                      "Times voted: {}, Times spoken in casing: {}, Times used doc: {}".format( data_c.data["times_voted"],data_c.data["times_talked_casing"]
                                                                                                                , data_c.data["times_doc"])],)
                self.write_votelist(poll_voting)
                client.send_host_message('You have already voted in this poll.')
                logger.log_serverpoll(
                    'Vote in poll {} \'{}\' failed by {} ({}) in {}, with IP {} and HDID {}, at {}. Reason: Already voted.'.format(
                        poll[0], vote, client.name, client.get_char_name(), client.area.name, client.real_ip, client.hdid,
                        tmp))
            elif (ipid_voted or hdid_voted) and [item for item in log if item[3].lower() == vote.lower()]:
                self.vote['faillog'] += (['FAILED VOTE', tmp, client.real_ip, client.hdid, vote,
                                      "{} ({}) at area {}".format(client.name, client.get_char_name(),
                                                                  client.area.name),
                                      "Times voted: {}, Times spoken in casing: {}, Times used doc: {}".format( data_c.data["times_voted"],data_c.data["times_talked_casing"]
                                                                                                                , data_c.data["times_doc"])],)
                self.write_votelist(poll_voting)
                client.send_host_message('You have chosen this choice already.')
                logger.log_serverpoll(
                    'Vote in poll {} \'{}\' failed by {} ({}) in {}, with IP {} and HDID {}, at {}. Reason: Already voted.'.format(
                        poll[0], vote, client.name, client.get_char_name(), client.area.name, client.real_ip, client.hdid,
                        tmp))
            else:
                # If they aren't a filthy rigger, they should get to this point
                if vote.lower() in [x.lower() for x in self.vote['choices']]:
                    self.vote['votes'][vote.lower()] += 1
                tmp = time.strftime('%y-%m-%d %H:%M:%S')
                self.vote['log'] += ([tmp, client.real_ip, client.hdid, vote,
                                      "{} ({}) at area {}".format(client.name, client.get_char_name(),
                                                                  client.area.name),
                                      "Times voted: {}, Times spoken in casing: {}, Times used doc: {}".format( data_c.data["times_voted"],data_c.data["times_talked_casing"]
                                                                                                                , data_c.data["times_doc"])],)
                self.write_votelist(poll_voting)
                self.server.stats_manager.user_voted(client.real_ip)
                client.send_host_message('You have successfully voted! Congratulations.')
                logger.log_serverpoll(
                    'Vote in poll {} \'{}\' added succesfully by {} ({}) in {}, with IP {} and HDID {}, at {}.'.format(
                        poll[0], vote, client.name, client.get_char_name(), client.area.name, client.real_ip, client.hdid,
                        tmp))
        except FileNotFoundError:
            client.send_host_message('Voting Error - Poll does not exist.')
            logger.log_serverpoll(
                'Vote in poll {} \'{}\' failed by {} ({}) in {}, with IP {} and HDID {}, at {}. Reason:FileNotFound error.'.format(
                    poll[0], vote, client.name, client.get_char_name(), client.area.name, client.real_ip, client.hdid,
                    tmp))
            raise ServerError('The specified poll does not have a file associated with it.')
        except IndexError:
            # todo: A bit redundant. There's probably a better way.
            if vote.lower() in [x.lower() for x in self.vote['choices']]:
                self.vote['votes'][vote.lower()] += 1
            tmp = time.strftime('%y-%m-%d %H:%M:%S')
            self.vote['log'] += ([tmp, client.ipid, client.hdid, vote,
                                  "{} ({}) at area {}".format(client.name, client.get_char_name(), client.area.name),
                                      "Times voted: {}, Times spoken in casing: {}, Times used doc: {}".format( data_c.data["times_voted"],data_c.data["times_talked_casing"]
                                                                                                                , data_c.data["times_doc"])],)
            self.write_votelist(poll_voting)
            client.send_host_message('You have successfully voted! Congratulations.')
            self.server.stats_manager.user_voted(client.ipid)
            logger.log_serverpoll('Vote \'{}\' added successfully by {}'.format(vote, client.get_ip()))

    def write_votelist(self, poll):
        with open('storage/poll/{} \'{}\'.yaml'.format(poll[1], poll[0]), 'w+') as votelist_file:
            yaml.dump(self.vote, votelist_file, default_flow_style=False)
            #           Clear variables to default now that you're done writing.
            self.vote = []

    def check_ipid(self, log, client):
        voted = False
        ipid = client.ipid
        for item in log:
            if item[1] == ipid:
                voted = True
        return voted


    def check_hdid(self, log, client):
        voted = False
        hdid = client.hdid
        if hdid in client.server.ban_manager.hdid_exempt:
            return voted
        for item in log:
            if item[2] == hdid:
                voted = True
        return voted