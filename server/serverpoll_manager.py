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
import yaml
import time

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

    def load_poll_list(self):
        try:
            with open('storage/poll/polllist.json', 'r') as poll_list_file:
                self.poll_list = json.load(poll_list_file)
        except FileNotFoundError:
            with open('storage/poll/polllist.json', 'w') as poll_list_file:
                json.dump([], poll_list_file)
            return
        except ValueError:
            return

    def write_poll_list(self):
        with open('storage/poll/polllist.json', 'w') as poll_list_file:
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
                    'voteyes': 0,
                    'voteno': 0,
                    'created': tmp,
                    'log': []
                }
                with open('storage/poll/{} \'{}\'.yaml'.format(test, value), 'w') as file:
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

    def add_vote(self, value, vote, client):
        tmp = time.strftime('%y-%m-%d %H:%M:%S')
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
            log = self.vote['log']
            if [item for item in log if item[1] == client.get_ip()] or [item for item in log if item[2] == client.get_hdid()]:
                # Now to log their failed vote
                self.vote['log'] += (['FAILED VOTE', tmp, client.get_ip(), client.get_hdid()],)
                self.write_votelist(poll_voting)
                logger.log_serverpoll(
                    'Vote \'{}\' failed by {} ({}) in {}, with IP {} and HDID {}, at {}. Reason: Already voted.'.format(
                        vote, client.name, client.get_char_name(), client.area.name, client.get_ip(), client.get_hdid(), tmp))
                client.send_host_message('You have already voted in this poll.')
            else:
                # If they aren't a filthy rigger, they should get to this point.
                if vote == "yes":
                    self.vote['voteyes'] += 1
                elif vote == "no":
                    self.vote['voteno'] += 1
                if not [item for item in log if item[1] == client.get_ip()] or not [item for item in log if item[2] == client.get_hdid]:
                    tmp = time.strftime('%y-%m-%d %H:%M:%S')
                    self.vote['log'] += ([tmp, client.get_ip(), client.get_hdid()],)
                self.write_votelist(poll_voting)
                logger.log_serverpoll(
                    'Vote \'{}\' added succesfully by {} ({}) in {}, with IP {} and HDID {}, at {}. Reason: Already voted.'.format(
                        vote, client.name, client.get_char_name(), client.area.name, client.get_ip(), client.get_hdid(),
                        tmp))
                client.send_host_message('You have successfully voted! Congratulations.')
        except FileNotFoundError:
            logger.log_serverpoll(
                'Vote \'{}\' failed by {} ({}) in {}, with IP {} and HDID {}, at {}. Reason:FileNotFound error.'.format(
                    vote, client.name, client.get_char_name(), client.area.name, client.get_ip(), client.get_hdid(),
                    tmp))
            client.send_host_message('Voting Error - Poll does not exist.')
            raise ServerError('The specified poll does not have a file associated with it.')
        except IndexError:
            # todo: A bit redundant. There's probably a better way.
            if vote == "yes":
                self.vote['voteyes'] += 1
            elif vote == "no":
                self.vote['voteno'] += 1
            tmp = time.strftime('%y-%m-%d %H:%M:%S')
            self.vote['log'] += ([tmp, client.get_ip(), client.get_hdid()],)
            self.write_votelist(poll_voting)
            logger.log_serverpoll('Vote \'{}\' added successfully by {}'.format(vote, client.get_ip()))
            client.send_host_message('You have successfully voted! Congratulations.')

    def write_votelist(self, poll):
        with open('storage/poll/{} \'{}\'.yaml'.format(poll[1], poll[0]), 'w') as votelist_file:
            yaml.dump(self.vote, votelist_file, default_flow_style=False)
            #           Clear variables to default now that you're done writing.
            self.vote = []
