import os
import logging
import yaml
from time import gmtime, strftime

import requests
import json

from server import database


class Webhooks:
	"""
	Contains functions related to webhooks.
	"""
	def __init__(self, server):
		self.server = server

	def send_webhook(self, username=None, avatar_url=None, message=None, embed=False, title=None, description=None):
		is_enabled = self.server.config['webhooks_enabled']
		url = self.server.config['webhook_url']
		
		if not is_enabled:
			return
		
		data = {}
		data["content"] = message
		data["username"] = username if username is not None else "tsuserver webhook"
		if embed == True:
			data["embeds"] = []
			embed = {}
			embed["description"] = description
			embed["title"] = title
			data["embeds"].append(embed)
		result = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
		try:
			result.raise_for_status()
		except requests.exceptions.HTTPError as err:
			database.log_misc('webhook.err', data=err)
		else:
			database.log_misc('webhook.ok', data="successfully delivered payload, code {}".format(result.status_code))

	def modcall(self, char, ipid, area, reason=None):
		is_enabled = self.server.config['modcall_webhook']['enabled']
		username = self.server.config['modcall_webhook']['username']
		avatar_url = self.server.config['modcall_webhook']['avatar_url']
		no_mods_ping = self.server.config['modcall_webhook']['ping_on_no_mods']
		mod_role_id = self.server.config['modcall_webhook']['mod_role_id']
		mods = len(self.server.client_manager.get_mods())
		current_time = strftime("%H:%M", gmtime())
		
		if not is_enabled:
			return
		
		if mods == 0 and no_mods_ping:
			message = f"@{mod_role_id if mod_role_id != None else 'here'} A user called for a moderator, but there are none online!"
		else:
			if mods == 1:
				s = ''
			else:
				s = 's'
			message = f"New modcall received ({mods} moderator{s} online)"
		
		description = f"[{current_time} UTC] {char} ({ipid}) in hub {area.area_manager.name} [{area.id}] {area.name} {'without reason (using <2.6?)' if reason is None else f'with reason: {reason}'}"
		
		self.send_webhook(username=username, avatar_url=avatar_url, message=message, embed=True, title="Modcall", description=description)

	def kick(self, char, ipid, reason):
		is_enabled = self.server.config['kick_webhook']['enabled']
		username = self.server.config['kick_webhook']['username']
		avatar_url = self.server.config['kick_webhook']['avatar_url']
		
		if not is_enabled:
			return
		
		message = f"{char} ({ipid}) was kicked from the server with reason: {reason}"
		
		self.send_webhook(username=username, avatar_url=avatar_url, message=message)
		
	def ban(self, char, ipid, ban_id, reason, hdid=None):
		is_enabled = self.server.config['ban_webhook']['enabled']
		username = self.server.config['ban_webhook']['username']
		avatar_url = self.server.config['ban_webhook']['avatar_url']
		
		if not is_enabled:
			return
		
		message = f"{char} ({ipid}) {f'(hdid: {hdid}) was hardware-banned' if hdid != None else 'was banned'} from the server with reason: {reason} (Ban ID: {ban_id})"
		
		self.send_webhook(username=username, avatar_url=avatar_url, message=message)

	def warn(self, char, ipid, warn_id, reason):
		is_enabled = self.server.config['warn_webhook']['enabled']
		username = self.server.config['warn_webhook']['username']
		avatar_url = self.server.config['warn_webhook']['avatar_url']
		
		if not is_enabled:
			return
		
		message = f"{char} ({ipid}) was warned with reason: {reason} (Warn ID: {warn_id})"
		
		self.send_webhook(username=username, avatar_url=avatar_url, message=message)

	def unwarn(self, client, warn_id):
		is_enabled = self.server.config['unwarn_webhook']['enabled']
		username = self.server.config['unwarn_webhook']['username']
		avatar_url = self.server.config['unwarn_webhook']['avatar_url']
		
		if not is_enabled:
			return
		
		message = f"Warn entry with ID {warn_id} was revoked by IPID {client.ipid}."
		
		self.send_webhook(username=username, avatar_url=avatar_url, message=message)

	def unban(self, client, ban_id):
		is_enabled = self.server.config['unban_webhook']['enabled']
		username = self.server.config['unban_webhook']['username']
		avatar_url = self.server.config['unban_webhook']['avatar_url']
		
		if not is_enabled:
			return
		
		message = f"Ban ID {ban_id} was revoked by IPID {client.ipid}."
		
		self.send_webhook(username=username, avatar_url=avatar_url, message=message)