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
			def __init__(self, area_id, server, hub, name, can_rename, background, bg_lock, pos_lock, evidence_mod = 'FFA', locking_allowed = False, iniswap_allowed = True):
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
				self.doc = 'No document.'
				self.judgelog = []
				self.current_music = ''
				self.current_music_player = ''
				self.evi_list = EvidenceList()
				self.is_recording = False
				self.recorded_messages = []
				self.evidence_mod = evidence_mod
				self.locking_allowed = locking_allowed
				self.hub = hub

				self.is_locked = False

			def new_client(self, client):
				self.clients.add(client)

			def remove_client(self, client):
				if self.is_locked and client.ipid in self.invite_list:
					self.invite_list.pop(client.ipid)
				self.clients.remove(client)
			
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

			def change_background(self, bg):
				# if bg.lower() not in (name.lower() for name in self.server.backgrounds):
				# 	raise AreaError('Invalid background name.')
				self.background = bg
				self.send_command('BN', self.background)

			def change_doc(self, doc='No document.'):
				self.doc = doc

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

		def __init__(self, hub_id, server, name, allow_cm):
			self.server = server
			self.id = hub_id
			self.cur_id = 0
			self.name = name
			self.allow_cm = allow_cm
			self.areas = []
			self.master = None
			self.is_ooc_muted = False
			self.status = 'IDLE'

		def new_client(self, client):
			return

		def remove_client(self, client):
			if client.is_cm:
				client.is_cm = False
				client.broadcast_ic.clear()
				self.master = None

		def default_area(self):
			return self.areas[0]

		def get_area_by_name(self, name):
			for area in self.areas:
				if area.name == name:
					return area
			raise AreaError('Area not found.')

		def get_area_by_id(self, num):
			for area in self.areas:
				if area.id == num:
					return area
			raise AreaError('Area not found.')

		def change_status(self, value):
			allowed_values = ('idle', 'building-open', 'building-full',
								'casing-open', 'casing-full', 'recess')
			if value.lower() not in allowed_values:
				raise AreaError('Invalid status. Possible values: {}'.format(
					', '.join(allowed_values)))
			self.status = value.upper()

		def send_host_message(self, msg):
			for area in self.areas:
				area.send_host_message(msg)

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
			_hub = self.Hub(self.cur_id, self.server,
							hub['hub'], hub['allow_cm'])
			self.hubs.append(_hub)
			self.cur_id += 1
			for area in hub['areas']:
				if 'evidence_mod' not in area:
					area['evidence_mod'] = 'FFA'
				if 'locking_allowed' not in area:
					area['locking_allowed'] = False
				if 'iniswap_allowed' not in area:
					area['iniswap_allowed'] = True
				_hub.areas.append(
					_hub.Area(_hub.cur_id, _hub.server, _hub, area['area'], area['can_rename'], area['background'], area['bglock'], area['poslock'], area['evidence_mod'], area['locking_allowed'], area['iniswap_allowed']))
				_hub.cur_id += 1

	def default_hub(self):
		return self.hubs[0]

	def get_hub_by_name(self, name):
		for hub in self.hubs:
			if hub.name == name:
				return hub
		raise AreaError('Hub not found.')

	def get_hub_by_id(self, num):
		for hub in self.hubs:
			if hub.id == num:
				return hub
		raise AreaError('Hub not found.')

