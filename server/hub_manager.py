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
import asyncio
import random

import time
import oyaml as yaml #ordered yaml

import re
import string

import os.path

from collections import OrderedDict

from server.constants import TargetType
from server.exceptions import AreaError
from server.evidence import EvidenceList

from heapq import heappop, heappush

class HubManager:
	class Hub:
		class Schedule:
			def __init__(self, hub, _id, target, time, affected, message, msgtype):
				self.hub = hub
				self.id = _id
				targetlist = ['area', 'user']
				self.target = targetlist.pop(targetlist.index(target)) #If there isn't such a "target" it will throw an error
				self.start_time = -1
				self.time = time
				self.affected = affected
				self.message = message
				typelist = ['ic', 'ooc']
				self.msgtype = typelist.pop(typelist.index(msgtype))
				self.display = 0

				self.cancelling = False
				self.task = None

			def start(self):
				self.task = asyncio.get_event_loop().create_task(self.step())

			async def step(self):
				loop = asyncio.get_event_loop()
				self.start_time = loop.time()
				end_time = loop.time() + self.time
				step = self.time / 10
				stepcount = 10
				try:
					# print('Timer {} id, with {} seconds, {} step, START'.format(self.id, self.time, step))
					while True:
						if self.cancelling:
							return
						self.hub.schedule_step(self.id, stepcount)
						stepcount -= 1
						# print('Timer {} id, {} seconds left'.format(self.id, end_time - loop.time()))
						if loop.time() >= end_time:
							break
						await asyncio.sleep(step)
					self.hub.schedule_finish(self.id)
				except asyncio.CancelledError:
					raise
				except Exception:
					pass

			def cancel(self):
				self.cancelling = True
				# print('Timer {} id, with {} seconds, CANCEL'.format(self.id, self.time))

		class Area:
			def __init__(self, area_id, server, hub, name, can_rename=True, background='default', bg_lock=False, pos_lock=None, evidence_mod = 'FFA',
						locking_allowed = False, can_remove = False, accessible = None, desc = '', locked=False, hidden=False, max_players=-1, move_delay=0):
				self.id = area_id
				self.server = server
				self.hub = hub

				self.clients = set()
				self.music_looper = None
				self.next_message_time = 0
				self.hp_def = 10
				self.hp_pro = 10
				self.judgelog = []
				self.current_music = ''
				self.current_music_player = ''
				self.current_music_player_ipid = ''
				self.current_ambience = ''
				self.is_recording = False
				self.record_start = 0
				self.recorded_messages = []
				self.mute_ic = False

				self.evi_list = EvidenceList()
				self.locked_by = None

				self.update(name, can_rename, background, bg_lock, pos_lock, evidence_mod, locking_allowed, can_remove, accessible, desc, locked, hidden, max_players, move_delay)

			def update(self, name, can_rename=True, background='default', bg_lock=False, pos_lock=None, evidence_mod = 'FFA',
						locking_allowed = False, can_remove = False, accessible = None, desc = '', locked=False, hidden=False, max_players=-1, move_delay=0):
				self.name = name
				self.can_rename = can_rename
				self.background = background
				self.bg_lock = bg_lock
				if pos_lock is None:
					self.pos_lock = []
				else:
					self.pos_lock = pos_lock
				self.evidence_mod = evidence_mod
				self.locking_allowed = locking_allowed
				self.can_remove = can_remove
				if accessible is None:
					self.accessible = []
				else:
					self.accessible = accessible
				self.desc = desc
				self.is_locked = locked
				self.is_hidden = hidden
				self.max_players = max_players
				self.move_delay = move_delay

			def set_desc(self, dsc):
				desc = dsc[:512]

			def yaml_save(self):
				data = OrderedDict()
				data['area'] = self.name
				data['background'] = self.background
				data['can_rename'] = self.can_rename
				data['bglock'] = self.bg_lock
				plock = ' '.join(map(str, self.pos_lock))
				if len(plock) > 0:
					data['poslock'] = plock
				data['evidence_mod'] = self.evidence_mod
				data['locking_allowed'] = self.locking_allowed
				data['can_remove'] = self.can_remove
				data['locked'] = self.is_locked
				data['hidden'] = self.is_hidden
				data['max_players'] = self.max_players
				data['move_delay'] = self.move_delay
				acs = ' '.join(map(str, self.accessible))
				if len(acs) > 0:
					data['accessible'] = acs
				data['desc'] = self.desc
				if len(self.evi_list.evidences) > 0:
					data['evidence'] = [e.to_dict() for e in self.evi_list.evidences]
				return data
				
			def update_from_yaml(self, area):
				if 'can_rename' not in area:
					area['can_rename'] = False
				if 'bglock' not in area:
					area['bglock'] = False
				if 'poslock' not in area or area['poslock'] == None or area['poslock'] == 'null':
					area['poslock'] = []
				else:
					_poslock = area['poslock'].split(' ')
					area['poslock'] = []
					for pos in _poslock:
						pos = pos.lower()
						if pos in ['def', 'pro', 'hld', 'hlp', 'jud', 'wit', 'sea', 'jur'] and not (pos in area['poslock']):
							area['poslock'].append(pos)
				if 'evidence_mod' not in area:
					area['evidence_mod'] = 'FFA'
				if 'locking_allowed' not in area:
					area['locking_allowed'] = False
				if 'can_remove' not in area:
					area['can_remove'] = False
				if 'accessible' not in area or type(area['accessible']) != list or len(area['accessible']) <= 0:
					area['accessible'] = []
				else:
					area['accessible'] = [int(s) for s in str(area['accessible']).split(' ')]
				if 'desc' not in area:
					area['desc'] = ''
				if 'locked' not in area:
					area['locked'] = False
				if 'hidden' not in area:
					area['hidden'] = False
				if 'max_players' not in area:
					area['max_players'] = -1
				if 'move_delay' not in area:
					area['move_delay'] = 0

				self.update(area['area'], area['can_rename'], area['background'], area['bglock'],
								area['poslock'], area['evidence_mod'], area['locking_allowed'],
								area['can_remove'], area['accessible'], area['desc'], area['locked'],
								area['hidden'], area['max_players'], area['move_delay'])

				self.change_background(self.background) #make sure everyone in the area gets the background update

				if 'evidence' not in area or len(area['evidence']) <= 0:
					area['evidence'] = []

				if len(area['evidence']) > 0:
					self.evi_list.evidences.clear()
					self.evi_list.import_evidence(area['evidence'])
					self.update_area_list()

			def new_client(self, client):
				self.clients.add(client)
				hidden = ''
				if client.hidden:
					hidden = ' [HIDDEN]'
				self.hub.send_to_cm('MoveLog', '[{}] {} has entered area [{}] {}.{}'.format(
					client.id, client.get_char_name(True), self.id, self.name, hidden), client)

				self.update_area_list(client)
				# self.server.hub_manager.send_arup_players()
				self.play_ambience(client)

			def remove_client(self, client):
				if self.locked_by == client:  # /lockin was used. Unlock the room.
					self.unlock()
				self.clients.remove(client)
				hidden = ''
				if client.hidden:
					hidden = ' [HIDDEN]'
				self.hub.send_to_cm('MoveLog', '[{}] {} has left area [{}] {}.{}'.format(
					client.id, client.get_char_name(True), self.id, self.name, hidden), client)
				# self.server.hub_manager.send_arup_players()

			def update_area_list(self, client=None):
				clients = []				
				if client == None:
					clients = self.clients
				else:
					clients.append(client)

				for c in clients:
					allowed = c.is_cm or c.is_mod or c.get_char_name() == "Spectator"
					rpmode = not allowed and c.hub.rpmode
					c.reload_music_list([a.name for a in c.get_area_list(rpmode, rpmode)])
					c.send_command('LE', *self.get_evidence_list(c)) #Update evidence list as well

			def lock(self, client=None):
				self.is_locked = True
				self.locked_by = client
				by = ''
				if self.locked_by != None:
					by = ' by {}'.format(client.get_char_name())
				self.send_host_message('This area is now locked{}.'.format(by))

			def unlock(self):
				self.is_locked = False
				self.locked_by = None
				self.send_host_message('This area is now open.')

			def hide(self):
				self.is_hidden = True
				self.send_host_message('This area is now hidden.')

			def unhide(self):
				self.is_hidden = False
				self.send_host_message('This area is now unhidden.')

			def is_char_available(self, char_id):
				return char_id not in [x.char_id for x in self.clients]

			def get_rand_avail_char_id(self):
				avail_set = set(range(len(self.server.char_list))) - set([x.char_id for x in self.clients])
				if len(avail_set) == 0:
					raise AreaError('No available characters.')
				return random.choice(tuple(avail_set))

			def send_command(self, cmd, *args):
				for c in self.clients:
					c.send_command(cmd, *args)

			def send_host_message(self, msg):
				self.send_command('CT', self.server.config['hostname'], msg)

			def set_next_msg_delay(self, delay):
				delay = min(3000, 100 + delay) #100ms lag margin
				self.next_message_time = round(time.time() * 1000.0 + delay)

			def play_ambience(self, client):
				#'MC' = music packet
				#'name' = name of the ambience
				#-1 = the character id (unused)
				#"" = showname
				#-1 = confusing, but -1 means "loop this" and anything else means "don't".
				#1 = Which channel to play this song on. Available channels are 0, 1, 2 and 3.
				#1 = Whether or not we should cross-fade this track. Note that crossfading tries to update the
				#	position of the next played song to match the last one as well. (enjoy your dynamic music)
				client.send_command('MC', self.current_ambience, -1, "", -1, 1, 1)

			def set_ambience(self, name, cid):
				self.current_ambience = name
				self.send_command('MC', self.current_ambience, -1, "", -1, 1, 1)

			def play_music(self, name, cid, length=-1):
				for client in self.server.client_manager.clients:
					if client.char_id == cid:
						self.current_music_player = client.get_char_name()
						self.current_music_player_ipid = client.ipid
						break

				self.current_music = name
				if (length > 0):
					length = -1 #That means the server defined the length for this file, aka it should loop.
				self.send_command('MC', name, cid, "", length, 0, 0)
				if self.music_looper:
					self.music_looper.cancel()
				if length > 0:
					self.music_looper = asyncio.get_event_loop().call_later(length,
																			lambda: self.play_music(name, -1, length))

			def play_music_shownamed(self, name, cid, showname, length=-1):
				for client in self.server.client_manager.clients:
					if client.char_id == cid:
						self.current_music_player = client.get_char_name(True)
						self.current_music_player_ipid = client.ipid
						break

				self.current_music = name
				if (length > 0):
					length = -1 #That means the server defined the length for this file, aka it should loop.
				self.send_command('MC', name, cid, showname, length, 0, 0)
				if self.music_looper:
					self.music_looper.cancel()
				if length > 0:
					self.music_looper = asyncio.get_event_loop().call_later(length,
																			lambda: self.play_music(name, -1, length))

			def can_send_message(self, client):
				if self.cannot_ic_interact(client):
					client.send_host_message('You are unable to speak in this area.')
					return False
				return (time.time() * 1000.0 - self.next_message_time) > 0

			def time_until_move(self, client):
				secs = round(time.time() * 1000.0 - client.last_move_time)
				highest = max(client.move_delay, self.move_delay, self.hub.move_delay)
				test = highest * 1000.0 - secs
				if test > 0:
					return test
				return 0

			def cannot_ic_interact(self, client):
				return self.mute_ic and (not client.is_cm and not client.is_mod)

			def change_hp(self, side, val):
				if not 0 <= val <= 10:
					raise AreaError('Invalid penalty value.')
				if not 1 <= side <= 2:
					raise AreaError('Invalid penalty side.')
				if side == 1:
					self.hp_def = val
				elif side == 2:
					self.hp_pro = val
				self.send_command('HP', side, val)

			def change_background(self, bg, bypass=False):
				if not bypass and self.server.bglock and bg.lower() not in (name.lower() for name in self.server.backgrounds):
					raise AreaError('Invalid background name {}.'.format(bg))
				self.background = bg
				for client in self.clients:
					#Update all clients to the pos lock
					if len(self.pos_lock) > 0 and client.pos not in self.pos_lock:
						client.change_position(self.pos_lock[0])
					client.send_command('BN', self.background, client.pos)

			# def change_desc(self, desc=''):
			# 	self.desc = desc

			def add_to_judgelog(self, client, msg):
				if len(self.judgelog) >= 10:
					self.judgelog = self.judgelog[1:]
				self.judgelog.append('{} ({}) {}.'.format(
					client.get_char_name(True), client.get_ip(), msg))

			def get_evidence_list(self, client):
				client.evi_list, evi_list = self.evi_list.create_evi_list(client)
				if client.blinded: #oops
					return [0]
				return evi_list

			def broadcast_evidence_list(self):
				"""
					LE#<name>&<desc>&<img>#<name>
					
				"""
				for client in self.clients:
					client.send_command('LE', *self.get_evidence_list(client))

			# def get_cms(self):
			# 	msg = ''
			# 	for i in self.owners:
			# 		msg = msg + '[' + str(i.id) + '] ' + i.get_char_name() + ', '
			# 	if len(msg) > 2:
			# 		msg = msg[:-2]
			# 	return msg

		def __init__(self, hub_id, server, name, allow_cm=False, max_areas=1, doc='No document.', status='IDLE', showname_changes_allowed=False,
						shouts_allowed=True, non_int_pres_only=False, iniswap_allowed=True, blankposting_allowed=True, abbreviation='', move_delay=0, keys=[]):
			self.server = server
			self.id = hub_id

			self.rpmode = False
			self.master = None
			self.is_ooc_muted = False
			self.areas = []
			self.cur_id = 0
			self.schedules = []
			self.cur_sched = [i for i in range(20)] #Max 20 schedules per hub
			self.update(name, allow_cm, max_areas, doc, status, showname_changes_allowed,
							shouts_allowed, non_int_pres_only, iniswap_allowed, blankposting_allowed, abbreviation, move_delay, keys)

		def update(self, name, allow_cm=False, max_areas=1, doc='No document.', status='IDLE', showname_changes_allowed=False,
					 shouts_allowed=True, non_int_pres_only=False, iniswap_allowed=True, blankposting_allowed=True, abbreviation='', move_delay=0, keys=[]):
			self.name = name
			self.allow_cm = allow_cm
			self.max_areas = max_areas
			self.doc = doc
			self.status = status
			self.showname_changes_allowed = showname_changes_allowed
			self.shouts_allowed = shouts_allowed
			self.non_int_pres_only = non_int_pres_only
			self.iniswap_allowed = iniswap_allowed
			self.blankposting_allowed = blankposting_allowed
			self.move_delay = move_delay
			self.keys = keys
			if abbreviation == '':
				self.abbreviation = self.get_generated_abbreviation()

		def yaml_save(self, stream='', limited=True):
			data = OrderedDict()
			if not limited:
				data['hub'] = self.name
				data['allow_cm'] = self.allow_cm
				data['max_areas'] = self.max_areas
				data['abbreviation'] = self.abbreviation
			data['doc'] = self.doc
			data['status'] = self.status
			data['showname_changes_allowed'] = self.showname_changes_allowed
			data['shouts_allowed'] = self.shouts_allowed
			data['noninterrupting_pres'] = self.non_int_pres_only
			data['iniswap_allowed'] = self.iniswap_allowed
			data['blankposting_allowed'] = self.blankposting_allowed
			data['move_delay'] = self.move_delay
			areas = []
			for area in self.areas:
				areas.append(area.yaml_save())
			data['areas'] = areas
			return data

		def yaml_dump(self, name=''):
			if name == '':
				raise AreaError('Invalid name.')

			path = 'storage/hubs'
			num_files = len([f for f in os.listdir(
				path) if os.path.isfile(os.path.join(path, f))])
			if (num_files >= 100): #yikes
				raise AreaError('Server storage full! Please contact the server host to resolve this issue.')
			with open('{}/{}.yaml'.format(path, name), 'w') as stream:
				yaml.dump(self.yaml_save(), stream, default_flow_style=False)

		def yaml_load(self, name=''):
			path = 'storage/hubs'
			with open('{}/{}.yaml'.format(path, name), 'r') as stream:
				hub = yaml.load(stream)

			self.update_from_yaml(hub)

		def update_from_yaml(self, hub):
			if 'hub' in hub:
				self.name = hub['hub']
			if 'allow_cm' in hub:
				self.allow_cm = hub['allow_cm']
			if 'max_areas' in hub:
				self.max_areas = hub['max_areas']
			if 'doc' in hub:
				self.change_doc(hub['doc'])
			if 'status' in hub:
				self.change_status(hub['status'])
			if 'showname_changes_allowed' in hub:
				self.showname_changes_allowed = hub['showname_changes_allowed']
			if 'shouts_allowed' in hub:
				self.shouts_allowed = hub['shouts_allowed']
			if 'noninterrupting_pres' in hub:
				self.non_int_pres_only = hub['noninterrupting_pres']
			if 'iniswap_allowed' in hub:
				self.iniswap_allowed = hub['iniswap_allowed']
			if 'blankposting_allowed' in hub:
				self.blankposting_allowed = hub['blankposting_allowed']
			if 'abbreviation' in hub:
				self.abbreviation = hub['abbreviation']
			if 'move_delay' in hub:
				self.move_delay = hub['move_delay']

			while len(self.areas) < len(hub['areas']):
				self.create_area('Area {}'.format(self.cur_id))
			aid = 0
			for area in hub['areas']:
				self.areas[aid].update_from_yaml(area)
				aid += 1

		def create_area(self, name, can_rename=True, bg='default', bglock=False, poslock=None, evimod='FFA', lockallow=True, removable=True, accessible=None, desc='', locked=False, hidden=False):
			self.areas.append(
				self.Area(self.cur_id, self.server, self, name, can_rename, bg, bglock, poslock, evimod, lockallow, removable, accessible, desc, locked, hidden))
			self.cur_id += 1
			self.update_area_list()

		def remove_area(self, area):
			if not (area in self.areas):
				raise AreaError('Area not found.')
			clients = area.clients.copy()
			for client in clients:
				client.change_area(self.default_area())

			#Update area accessibility memes
			for _area in self.areas:
				accessible = []
				for _id in _area.accessible:
					if _id > area.id:
						_id -= 1 #Shift it down as one area was removed
					elif _id == area.id:
						continue #remove the reference to this area
					accessible.append(_id)
				_area.accessible = accessible
			self.areas.remove(area)
			self.update_area_ids()
			self.update_area_list()

		def swap_area(self, area1, area2):
			if not (area1 in self.areas) or not (area2 in self.areas):
				raise AreaError('Area not found.')

			a, b = self.areas.index(area1), self.areas.index(area2)
			self.areas[b], self.areas[a] = self.areas[a], self.areas[b] #Swap 'em good

			#Update area accessibility memes
			for _area in self.areas:
				accessible = []
				for _id in _area.accessible:
					if _id == a:
						_id = b
					elif _id == b:
						_id = a
					accessible.append(_id)
				_area.accessible = accessible

			self.update_area_ids()
			self.update_area_list()

		#Global update of all areas for the client music lists in the hub
		def update_area_list(self):
			for area in self.areas:
				area.update_area_list()

		def update_area_ids(self):
			for i, area in enumerate(self.areas):
				area.id = i
			self.cur_id = i+1

		def change_doc(self, doc='No document.'):
			self.doc = doc

		def new_client(self, client):
			return

		def remove_client(self, client):
			if client.is_cm:
				client.is_cm = False
				client.broadcast_ic.clear()
				if self.master == client:
					self.master = None
			
			if client.hidden:
				client.hide(False)
			if client.blinded:
				client.blind(False)

		def default_area(self):
			return self.areas[0]

		def get_area_by_name(self, name):
			for area in self.areas:
				if area.name.lower() == name.lower():
					return area
			raise AreaError('Area not found.')

		def get_area_by_id(self, num):
			for area in self.areas:
				if area.id == num:
					return area
			raise AreaError('Area not found.')

		def get_area_by_id_or_name(self, args):
			try:
				return self.get_area_by_name(args)
			except:
				try:
					return self.get_area_by_id(int(args))
				except:
					raise AreaError('Area not found.')

		def change_status(self, value):
			allowed_values = ('idle', 'rp', 'rp-strict',
							'looking-for-players', 'lfp', 'recess', 'gaming')
			if value.lower() not in allowed_values:
				raise AreaError('Invalid status. Possible values: {}'.format(
					', '.join(allowed_values)))
			if value.lower() == 'lfp':
				value = 'looking-for-players'
			self.status = value.upper()
			if value.lower().startswith('rp'):
				self.start_recording(True, True)
				self.rpmode = True
			else:
				self.stop_recording(True)
				self.rpmode = False
			self.server.hub_manager.send_arup_status()
			self.update_area_list()

		def is_iniswap(self, client, anim1, anim2, char):
			if self.iniswap_allowed:
				return False
			if '..' in anim1 or '..' in anim2:
				return True
			for char_link in self.server.allowed_iniswaps:
				if client.get_char_name() in char_link and char in char_link:
					return False
			return True

		def clear_recording(self, announce=False):
			for area in self.areas:
				area.recorded_messages.clear()
			
			if announce:
				self.send_host_message('Clearing IC records for {} areas.'.format(len(self.areas)))

		def start_recording(self, announce=False, clear=False):
			msg = ''
			i = 0
			for area in self.areas:
				if clear and not area.is_recording and len(area.recorded_messages) > 0:
					area.recorded_messages.clear()
					i += 1
				area.is_recording = True
				area.record_start = time.gmtime()
			
			if i > 0:
				msg = ' (Clearing records for {} areas)'.format(i)

			if announce:
				self.send_host_message('Starting IC records for {} areas{}.'.format(len(self.areas), msg))

		def stop_recording(self, announce=False):
			i = 0
			for area in self.areas:
				if area.is_recording:
					area.is_recording = False
					i += 1

			if announce and i > 0:
				self.send_host_message('Stopping IC records for {} areas.'.format(i))

		def send_host_message(self, msg):
			for area in self.areas:
				area.send_host_message(msg)

		def send_to_cm(self, T, msg, exceptions):
			if type(exceptions) != list:
				exceptions = [exceptions]
			for area in self.areas:
				for client in area.clients:
					if not (client in exceptions) and client.is_cm and T in client.cm_log_type:
						client.send_host_message('$CM[{}]{}'.format(T, msg))

		def get_cm_list(self):
			cms = []
			for area in self.areas:
				for client in area.clients:
					if client.is_cm:
						cms.append(client)
			
			return cms

		def send_command(self, cmd, *args):
			for area in self.areas:
				area.send_command(cmd, *args)
		
		def set_next_msg_delay(self, msg_length):
			for area in self.areas:
				area.set_next_msg_delay(msg_length)
		
		def clients(self):
			clients = set()
			for area in self.areas:
				for client in area.clients:
					clients.add(client)
			return clients

		def get_generated_abbreviation(self):
			name = self.name
			if name.lower().startswith("courtroom"):
				return "CR" + name.split()[-1]
			elif name.lower().startswith("hub"):
				return "H" + name.split()[-1]
			elif len(name.split()) > 1:
				return "".join(item[0].upper() for item in name.split())
			elif len(name) > 3:
				return name[:3].upper()
			else:
				return name.upper()

		def setup_schedule(self, targets, time, affected, message, msgtype):
			try:
				_id = heappop(self.cur_sched)
				self.schedules.append(self.Schedule(self, _id, targets, time, affected, message, msgtype))
				return _id
			except:
				return -1

		def find_schedule(self, _id):
			return [s for s in self.schedules if s.id == _id][0]

		def destroy_schedule(self, _id):
			schedule = self.find_schedule(_id)
			if not schedule:
				return
			schedule.cancel()
			self.schedules.remove(schedule)
			heappush(self.cur_sched, _id) #return the ID as available

		def start_schedule(self, _id):
			schedule = self.find_schedule(_id)
			if not schedule:
				return
			schedule.start()

		def stop_schedule(self, _id):
			schedule = self.find_schedule(_id)
			if not schedule:
				return
			schedule.cancel()
		
		def schedule_step(self, _id, val):
			#TODO: Check for all "linked" clients/areas/etc. and update the penalty bar accordingly
			schedule = self.find_schedule(_id)
			if not schedule:
				return
			if schedule.display in [1, 2]:
				if schedule.target == "area":
					if schedule.affected == 'all':
						self.send_command('HP', schedule.display, val)
					else:
						for aid in schedule.affected:
							area = self.get_area_by_id(aid)
							if not area:
								continue
							area.send_command('HP', schedule.display, val)
				if schedule.target == "user":
					if schedule.affected == 'all':
						self.send_command('HP', schedule.display, val)
					else:
						for client in self.clients():
							if not client.id in schedule.affected:
								continue
							client.send_command('HP', schedule.display, val)
		
		def schedule_display(self, _id, val): 
			schedule = self.find_schedule(_id)
			if not schedule:
				return
			schedule.display = val
		
		def schedule_finish(self, _id):
			schedule = self.find_schedule(_id)
			if not schedule:
				return
			if schedule.target == "area":
				if schedule.affected == 'all':
					if schedule.msgtype == 'ooc':
						self.send_command('CT', '~Timer', schedule.message)
					elif schedule.msgtype == 'ic':
						msg_type, pre, folder, anim, msg, pos, sfx, anim_type, cid, sfx_delay, button, evi, flip, ding, color, showname, charid_pair, other_folder, other_emote, offset_pair, other_offset, other_flip, nonint_pre = schedule.message
						self.send_command('MS', msg_type, pre, folder, anim, msg, pos, sfx, anim_type, cid,
									sfx_delay, button, evi, flip, ding, color, showname,
									charid_pair, other_folder, other_emote, offset_pair, other_offset, other_flip,
									nonint_pre)
				else:
					for aid in schedule.affected:
						area = self.get_area_by_id(aid)
						if area:
							if schedule.msgtype == 'ooc':
								area.send_command('CT', '~Timer', schedule.message)
							elif schedule.msgtype == 'ic':
								msg_type, pre, folder, anim, msg, pos, sfx, anim_type, cid, sfx_delay, button, evi, flip, ding, color, showname, charid_pair, other_folder, other_emote, offset_pair, other_offset, other_flip, nonint_pre = schedule.message
								area.send_command('MS', msg_type, pre, folder, anim, msg, pos, sfx, anim_type, cid,
											sfx_delay, button, evi, flip, ding, color, showname,
											charid_pair, other_folder, other_emote, offset_pair, other_offset, other_flip,
											nonint_pre)
			if schedule.target == "user":
				if schedule.affected == 'all':
					if schedule.msgtype == 'ooc':
						self.send_command('CT', '~Timer', schedule.message)
					elif schedule.msgtype == 'ic':
						msg_type, pre, folder, anim, msg, pos, sfx, anim_type, cid, sfx_delay, button, evi, flip, ding, color, showname, charid_pair, other_folder, other_emote, offset_pair, other_offset, other_flip, nonint_pre = schedule.message
						self.send_command('MS', msg_type, pre, folder, anim, msg, pos, sfx, anim_type, cid,
									sfx_delay, button, evi, flip, ding, color, showname,
									charid_pair, other_folder, other_emote, offset_pair, other_offset, other_flip,
									nonint_pre)
				else:
					for client in self.clients():
						if not client.id in schedule.affected:
							continue
						if schedule.msgtype == 'ooc':
							client.send_command('CT', '~Timer', schedule.message)
						elif schedule.msgtype == 'ic':
							msg_type, pre, folder, anim, msg, pos, sfx, anim_type, cid, sfx_delay, button, evi, flip, ding, color, showname, charid_pair, other_folder, other_emote, offset_pair, other_offset, other_flip, nonint_pre = schedule.message
							client.send_command('MS', msg_type, pre, folder, anim, msg, pos, sfx, anim_type, cid,
                                        sfx_delay, button, evi, flip, ding, color, showname,
                                        charid_pair, other_folder, other_emote, offset_pair, other_offset, other_flip,
                                        nonint_pre)
			self.destroy_schedule(_id)

	def __init__(self, server):
		self.server = server
		self.cur_id = 0
		self.hubs = []
		self.load_hubs()

	def load_hubs(self):
		with open('config/areas.yaml', 'r') as chars:
			hubs = yaml.load(chars)

		for hub in hubs:
			print(self.cur_id, hub['hub'])
			#create new hub
			#update it with data
			#append it to hubs list and increase cur_id
			_hub = self.Hub(self.cur_id, self.server, 'Hub {}'.format(self.cur_id))
			_hub.update_from_yaml(hub)
			self.hubs.append(_hub)
			self.cur_id += 1

	def default_hub(self):
		return self.hubs[0]

	def get_hub_by_name(self, name):
		for hub in self.hubs:
			if hub.name.lower() == name.lower():
				return hub
		raise AreaError('Hub not found.')

	def get_hub_by_id(self, num):
		for hub in self.hubs:
			if hub.id == num:
				return hub
		raise AreaError('Hub not found.')

	def get_hub_by_id_or_name(self, args):
		try:
			return self.get_hub_by_name(args)
		except:
			try:
				return self.get_hub_by_id(int(args))
			except:
				raise AreaError('Hub not found.')

	def send_arup_players(self):
		players_list = [0]
		for hub in self.hubs:
			players_list.append(len(hub.clients()))
		self.server.send_arup(players_list)

	def send_arup_status(self):
		status_list = [1]
		for hub in self.hubs:
			status_list.append(hub.status)
		self.server.send_arup(status_list)

	def send_arup_cms(self):
		cms_list = [2]
		for hub in self.hubs:
			cm = 'FREE'
			if hub.master != None:
				cm = hub.master.name
			cms_list.append(cm)
		self.server.send_arup(cms_list)

	def send_arup_lock(self):
		lock_list = [3]
		for hub in self.hubs:
			lock_list.append(hub.rpmode)
		self.server.send_arup(lock_list)