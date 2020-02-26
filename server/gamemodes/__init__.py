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
        self.current_timer = None #Current timer going on, whether it be signups, prelim discussion or final discussion
        self.signups = [] #clients who signed up
        self.signup_length = 5 * 60 #outputs in seconds
        self.min_signups = 5 #minimum amount of clients needed for a single round
        self.prelim_coefficient = 0.5 #Half of the participants must make it into prelims (floored)
        self.minimum_required = 3 #minimum required candidates for preliminary
        self.prelim_discussion_time = 30 * 60 #outputs in seconds
        self.final_discussion_time = 20 * 60 #outputs in seconds

        self.current_phase = "" #The phase we're on
        self.votes = {} #The vote dictionary we collected

    def start_building(self):
        """
        Begin the sign-up process and start the game when done.

        """
        self.area.broadcast_ooc('Building has started. Round will begin in {} seconds.'.format(self.signup_length))
        if self.current_timer:
            self.current_timer.cancel()
        self.current_timer = asyncio.get_event_loop().call_later(self.signup_length, lambda: self.round_start())
        self.current_phase = "building"

    def round_start(self):
        """
        Make the area spectate only and begin the round.
        If there are not enough players, restart the sign-ups timer.

        """
        if self.current_timer:
            self.current_timer.cancel()
        if len(self.signups < self.min_signups):
            self.start_building()
            return

        self.area.broadcast_ooc('based')
        #begin the game loop
        self.current_phase = "preliminary"
        self.discussion_phase(self.prelim_discussion_time)

    def round_end(self):
        """
        End the round, nuking any data we collected.

        """
        if self.current_timer:
            self.current_timer.cancel()
        self.area.broadcast_ooc('gay')
        self.current_phase = ""

    def discussion_phase(self, length):
        """
        Start the discussion phase

        """
        if self.current_timer:
            self.current_timer.cancel()
        self.current_timer = asyncio.get_event_loop().call_later(length, lambda: self.voting_phase())
        self.area.broadcast_ooc('Discussion time!')

    def voting_phase(self):
        """
        Start the voting phase

        """
        if self.current_timer:
            self.current_timer.cancel()
        self.current_timer = asyncio.get_event_loop().call_later(self.voting_length, lambda: self.voting_end())
        self.area.broadcast_ooc('Voting time!')

    def voting_end(self):
        """
        End the voting phase and handle if we head to next discussion
        or handle the results

        """
        if self.current_phase == "preliminary":
            self.current_phase = "finals"
            if self.current_timer:
                self.current_timer.cancel()
            self.current_timer = asyncio.get_event_loop().call_later(self.voting_length, lambda: self.discussion_phase(self.final_discussion_time))
        elif self.current_phase == "finals":
            if self.current_timer:
                self.current_timer.cancel()
            self.current_timer = asyncio.get_event_loop().call_later(5, lambda: self.handle_winners())
            

    def handle_winners(self):
        """
        Execute people who are losers, give winners their limelight

        """
        self.area.broadcast_ooc('LOL!')
        await asyncio.sleep(1)
        self.area.broadcast_ooc('YOU!')
        await asyncio.sleep(1)
        self.area.broadcast_ooc('BOUTTA!')
        await asyncio.sleep(1)
        self.area.broadcast_ooc('DIE!')