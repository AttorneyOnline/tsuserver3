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

import asyncio

class GamemodeYTTD:
    """Your Turn To Die Main-Game test gamemode for future abstraction."""

    def __init__(self, area):
        self.name = "YTTD Main Game"
        self.area = area
        self.area.change_doc('Rules - https://docs.google.com/document/d/1TqKej4TCaclWd2TFH4KEU-SYi8wQWSB6_UB6bosvjeg/edit#')
        self.current_timer = None
        self.signup_length = 5*60 #5 minutes
        self.signups = [] #clients who signed up

    def start_building(self):
        """
        Begin the sign-up process and start the game when done.

        """
        self.area.broadcast_ooc('Building has started. Round will begin in {} seconds.'.format(self.signup_length))
        if self.current_timer:
            self.current_timer.cancel()
        self.current_timer = asyncio.get_event_loop().call_later(self.signup_length, lambda: self.round_start())

    def round_start(self):
        """
        Make the area spectate only and begin the round.
        If there are not enough players, restart the sign-ups timer.

        """
        if self.current_timer:
            self.current_timer.cancel()
        self.start_building()
        self.area.broadcast_ooc('based')

    def round_end(self):
        """
        End the round, nuking any data we collected.

        """
        if self.current_timer:
            self.current_timer.cancel()
        self.area.broadcast_ooc('gay')
