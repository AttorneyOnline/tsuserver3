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

import json

from server.exceptions import ServerError


class BanManager:
    """Manages bans."""
    def __init__(self):
        self.bans = {}  # "ipid": {"Reason": "reason"}
        self.load_banlist()

    def load_banlist(self):
        """Load bans from persistence."""
        try:
            with open('storage/banlist.json', 'r') as banlist_file:
                self.bans = json.load(banlist_file)
                if type(self.bans) is not dict:
                    self.convert_to_modern_banlist()
        except FileNotFoundError:
            return

    def convert_to_modern_banlist(self):
        """Migrate an old ban list to one that supports ban reasons."""
        bantmp = self.bans
        self.bans = {}
        for ipid in bantmp:
            self.add_ban(str(ipid), 'N/A')

    def write_banlist(self):
        """Persist all bans to a file."""
        with open('storage/banlist.json', 'w') as banlist_file:
            json.dump(self.bans, banlist_file)

    def add_ban(self, ipid, reason):
        """
        Add a ban entry.
        :param ipid: IPID
        :param reason: reason for ban
        """
        ipid = str(ipid)
        if not self.is_banned(ipid):
            self.bans[ipid] = {'Reason': reason}
        else:
            raise ServerError('This IPID is already banned.')
        self.write_banlist()

    def remove_ban(self, ipid):
        """
        Remove a ban entry/
        :param ipid: IPID
        """
        ipid = str(ipid)
        if self.is_banned(ipid):
            del self.bans[ipid]
        else:
            raise ServerError('This IPID is not banned.')
        self.write_banlist()

    def is_banned(self, ipid):
        """
        Check if a user is banned.
        :param ipid: IPID
        """
        ipid = str(ipid)
        return ipid in self.bans

    def get_ban_reason(self, ipid):
        """
        Get the reason for a ban.
        :param ipid: IPID
        """
        ipid = str(ipid)
        if self.is_banned(ipid):
            return self.bans[ipid]["Reason"]
        else:
            raise ServerError('This IPID is not banned.')
