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
import yaml

from server.exceptions import AreaError
from server.evidence import EvidenceList

class HubManager:
	class Hub:
		class Area:
			def __init__(self, area_id, server, hub, name, can_rename, background, bg_lock, pos_lock, evidence_mod = 'FFA', locking_allowed = False, iniswap_allowed = True, can_remove = False, accessible = [], desc = ''):
				self.iniswap_allowed = iniswap_allowed
				self.clients = set()
				self.invite_list = {}
				self.id = area_id
				self.name = name
				self.can_rename = can_rename
				self.background = background
				self.bg_lock = bg_lock
				self.pos_lock = pos_lock in ('def', 'pro', 'hld', 'hlp', 'jud', 'wit') or None
				self.server = server
				self.music_looper = None
				self.next_message_time = 0
				self.hp_def = 10
				self.hp_pro = 10
				self.judgelog = []
				self.current_music = ''
				self.current_music_player = ''
				self.evi_list = EvidenceList()
				self.is_recording = False
				self.record_start = 0
				self.recorded_messages = []
				self.evidence_mod = evidence_mod
				self.locking_allowed = locking_allowed
				self.hub = hub
				self.desc = desc
				self.mute_ic = False
				self.can_remove = can_remove
				self.accessible = accessible

				self.is_locked = False

			def save(self):
				desc = self.desc
				if len(self.desc) <= 0:
					desc = 'None'
				accessible = ','.join(map(str, self.accessible))
				if len(accessible) <= 0:
					accessible = 'None'
				return '{};{};{};{};{};{};{}'.format(
					self.id, self.name, desc, self.background, self.pos_lock, accessible, self.is_locked)

			def load(self, arg):
				# try:
				args = arg.split(';')
				print(args)
				self.name = str(args[1])
				self.desc = str(args[2])
				self.background = str(args[3])
				if str(args[4]).lower() in ('def', 'pro', 'hld', 'hlp', 'jud', 'wit'):
					self.pos_lock = str(args[4]).lower()
				else:
					self.pos_lock = None

				if args[5] == 'None':
					self.accessible = []
				else:
					self.accessible = [int(s) for s in str(args[5]).split(',')]
				self.is_locked = str(args[6]).lower() == 'true'
				# except:
				# 	return AreaError('Bad save file!')

			def new_client(self, client):
				self.clients.add(client)
				hidden = ''
				if client.hidden:
					hidden = ' [HIDDEN]'
				self.hub.send_to_cm('[{}] {} has entered area [{}] {}.{}'.format(
					client.id, client.get_char_name(), self.id, self.name, hidden), [client])

			def remove_client(self, client):
				if self.is_locked and client.ipid in self.invite_list:
					self.invite_list.pop(client.ipid)
				self.clients.remove(client)
				hidden = ''
				if client.hidden:
					hidden = ' [HIDDEN]'
				self.hub.send_to_cm('[{}] {} has left area [{}] {}.{}'.format(
					client.id, client.get_char_name(), self.id, self.name, hidden), [client])

			def lock(self):
				self.is_locked = True
				for c in self.clients:
					self.invite_list[c.ipid] = None
				self.send_host_message('This area is locked now.')

			def unlock(self):
				self.is_locked = False
				self.invite_list = {}
				self.send_host_message('This area is open now.')
			
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

			def set_next_msg_delay(self, msg_length):
				delay = min(3000, 100 + 60 * msg_length)
				self.next_message_time = round(time.time() * 1000.0 + delay)
			
			def is_iniswap(self, client, anim1, anim2, char):
				if self.iniswap_allowed:
					return False
				if '..' in anim1 or '..' in anim2:
					return True
				for char_link in self.server.allowed_iniswaps:
					if client.get_char_name() in char_link and char in char_link:
						return False
				return True
			
			def play_music(self, name, cid, length=-1):
				self.send_command('MC', name, cid)
				if self.music_looper:
					self.music_looper.cancel()
				if length > 0:
					self.music_looper = asyncio.get_event_loop().call_later(length,
																			lambda: self.play_music(name, -1, length))


			def can_send_message(self, client):
				if self.is_locked and not client.is_mod and not client.is_cm and not client.ipid in self.invite_list:
					client.send_host_message('This is a locked area - ask the CM to speak.')
					return False
				return (time.time() * 1000.0 - self.next_message_time) > 0

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
					raise AreaError('Invalid background name.')
				self.background = bg
				self.send_command('BN', self.background)

			def add_to_judgelog(self, client, msg):
				if len(self.judgelog) >= 10:
					self.judgelog = self.judgelog[1:]
				self.judgelog.append('{} ({}) {}.'.format(client.get_char_name(), client.get_ip(), msg))

			def add_music_playing(self, client, name):
				self.current_music_player = client.get_char_name()
				self.current_music = name

			def get_evidence_list(self, client):
				client.evi_list, evi_list = self.evi_list.create_evi_list(client)
				return evi_list

			def broadcast_evidence_list(self):
				"""
					LE#<name>&<desc>&<img>#<name>
					
				"""
				for client in self.clients:
					client.send_command('LE', *self.get_evidence_list(client))

		def __init__(self, hub_id, server, name, allow_cm=False, max_areas=1, doc='No document.', status='IDLE'):
			self.server = server
			self.id = hub_id
			self.cur_id = 0
			self.name = name
			self.allow_cm = allow_cm
			self.areas = []
			self.max_areas = max_areas
			self.master = None
			self.is_ooc_muted = False
			self.status = status
			self.doc = doc

			#Turn Based System
			# self.tbs_enabled = False
			# self.tbs_players = []
			# self.tbs_turns = 1
			# self.tbs_turnsleft = 1
			# self.tbs_current = 0

		def save(self):
			s = ''
			for area in self.areas:
				if not area.locking_allowed:
					continue
				s += area.save() + '\n'
			return s

		def load(self, arg):
			args = arg.split('\n')
			try:
				while len(self.areas) < len(args):
					self.create_area('Area {}'.format(self.cur_id), True,
											self.server.backgrounds[0], False, None, 'FFA', True, True, True, [], '')
				i = 1
				for a in args:
					if(len(a) < 7):
						continue
					self.areas[i].load(a)
					i += 1
			except:
				raise AreaError('Bad save file!')

		def create_area(self, name, can_rename, bg, bglock, poslock, evimod, lockallow, swapallow, removable, accessible, desc):
			self.areas.append(
				self.Area(self.cur_id, self.server, self, name, can_rename, bg, bglock, poslock, evimod, lockallow, swapallow, removable, accessible, desc))
			self.cur_id += 1

		def remove_area(self, area):
			if not (area in self.areas):
				raise AreaError('Area not found.')
			clients = area.clients.copy()
			for client in clients:
				client.change_area(self.default_area())
			self.areas.remove(area)
			self.update_area_ids()

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
			allowed_values = ('idle', 'building-open', 'building-full',
								'casing-open', 'casing-full', 'recess')
			if value.lower() not in allowed_values:
				raise AreaError('Invalid status. Possible values: {}'.format(
					', '.join(allowed_values)))
			self.status = value.upper()
			if value.lower().startswith('casing'):
				self.start_recording(True, True)
			else:
				self.stop_recording(True)

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

		def send_to_cm(self, msg, exceptions=[]):
			for area in self.areas:
				for client in area.clients:
					if not (client in exceptions) and client.is_cm:
						client.send_host_message(msg)

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

	def __init__(self, server):
		self.server = server
		self.cur_id = 0
		self.hubs = []
		self.load_hubs()

	def load_hubs(self):
		with open('config/areas.yaml', 'r') as chars:
			hubs = yaml.load(chars)

		for hub in hubs:
			if 'allow_cm' not in hub:
				hub['allow_cm'] = False
			if 'max_areas' not in hub:
				hub['max_areas'] = 1
			if 'doc' not in hub:
				hub['doc'] = 'No document.'
			if 'status' not in hub:
				hub['status'] = 'IDLE'
			_hub = self.Hub(self.cur_id, self.server,
							hub['hub'], hub['allow_cm'], hub['max_areas'], hub['doc'], hub['status'])
			self.hubs.append(_hub)
			self.cur_id += 1
			for area in hub['areas']:
				if 'can_rename' not in area:
					area['can_rename'] = False
				if 'bglock' not in area:
					area['bglock'] = False
				if 'poslock' not in area:
					area['poslock'] = None
				if 'evidence_mod' not in area:
					area['evidence_mod'] = 'FFA'
				if 'locking_allowed' not in area:
					area['locking_allowed'] = False
				if 'iniswap_allowed' not in area:
					area['iniswap_allowed'] = True
				if 'can_remove' not in area:
					area['can_remove'] = False
				if 'desc' not in area:
					area['desc'] = ''
				if 'accessible' not in area:
					area['accessible'] = []
				else:		
					area['accessible'] = [int(s) for s in str(area['accessible']).split(' ')]

				_hub.create_area(area['area'], area['can_rename'], area['background'], area['bglock'], area['poslock'], area['evidence_mod'], area['locking_allowed'], area['iniswap_allowed'], area['can_remove'], area['accessible'], area['desc'])

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
