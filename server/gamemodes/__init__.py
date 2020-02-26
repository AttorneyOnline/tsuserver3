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
import random

music = {
    'preliminary': ['room escape and gameplay/[VLR] Lounge.ogg',
                'room escape and gameplay/[VLR] Data.ogg',
                'room escape and gameplay/[VLR] Director.ogg',
                'room escape and gameplay/[VLR] Dispensary.ogg',
            ],
    'finals': ['room escape and gameplay/[VLR] Pantry.ogg',
                'room escape and gameplay/[VLR] Gaulem.ogg',
                'room escape and gameplay/[VLR] Monitor.ogg',
                'room escape and gameplay/[VLR] Q.ogg',
            ],
    'voting': ['suspense/[999] Who is Zero.ogg',
                'suspense/[999] Eternitybox.ogg',
                'suspense/[VLR] Eeriness.ogg',
                'suspense/[VLR] Sinisterness.ogg',
                'tension/[VLR] Consternation.ogg',
                'realisation and logic/[VLR] Divulgation.ogg',
            ],
    'sacrifice': ['bad end/[ZTD] CQD_ BAD END.ogg',
                'bad end/[VLR] Demise.ogg',
                'bad end/[VLR] Sublimity.ogg',
                'tension/[999] Trepidation.ogg',
                'reminiscence and sorrow/[ZTD] Morphogenetic Sorrow.ogg',
            ],
    'relief': ['reminiscence and sorrow/[ZTD] Ustulate Pathos.ogg',
                'bad end/[VLR] Demise.ogg',
                'bad end/[VLR] Sublimity.ogg',
                'tension/[999] Trepidation.ogg',
                'reminiscence and sorrow/[VLR] Confession.ogg',
            ],
}

class GamemodeYTTD:
    """Your Turn To Die Main-Game test gamemode for future abstraction."""

    def __init__(self, area):
        self.name = "YTTD Main Game"
        self.area = area
        area.gamemode = self
        self.area.change_doc('Rules - https://docs.google.com/document/d/1TqKej4TCaclWd2TFH4KEU-SYi8wQWSB6_UB6bosvjeg/edit#')

        self.current_timer = None #Current timer going on, whether it be signups, prelim discussion or final discussion
        self.signups = [] #clients who signed up
        self.signup_length = 5 #* 60 #outputs in seconds
        self.min_signups = 1 #5 #minimum amount of clients needed for a single round
        self.prelim_coefficient = 0.5 #Half of the participants must make it into prelims (floored)
        self.minimum_required = 3 #minimum required candidates for preliminary
        self.prelim_discussion_time = 5 #30 #* 60 #outputs in seconds
        self.final_discussion_time = 5 #20 #* 60 #outputs in seconds

        self.current_phase = "" #The phase we're on
        self.votes = {} #The vote dictionary we collected
        self.voting_length = 5 #60 #One minute for the voting period

    def join(self, client):
        """
        signup
        """
        if not client.area.gamemode.current_phase == "signups":
            client.send_ooc('You can only join during the building phase.')
            return
        self.signups.append(client)
        self.area.broadcast_ooc(f'{client.char_name} has joined YTTD.')

    def unjoin(self, client):
        """
        unsignup
        """
        if not client.area.gamemode.current_phase == "signups":
            client.send_ooc('Too late, you are stuck with us now.')
            return
        self.signups.remove(client)
        self.area.broadcast_ooc(f'{client.char_name} has unjoined YTTD.')

    def start_building(self):
        """
        Begin the sign-up process and start the game when done.

        """
        self.area.broadcast_ooc(f'Building has started. Round will begin in {self.signup_length} seconds.')
        if self.current_timer:
            self.current_timer.cancel()
        self.current_timer = asyncio.get_event_loop().call_later(self.signup_length, lambda: self.round_start())
        self.current_phase = "signups"
        self.area.change_status('lfp')

    def round_start(self):
        """
        Make the area spectate only and begin the round.
        If there are not enough players, restart the sign-ups timer.

        """
        if self.current_timer:
            self.current_timer.cancel()
        if len(self.signups) < self.min_signups:
            self.start_building()
            return

        self.area.broadcast_ooc('based')
        self.area.change_status('rp')
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
        self.area.change_status('idle')
        self.votes.clear()

    def discussion_phase(self, length):
        """
        Start the discussion phase

        """
        if self.current_timer:
            self.current_timer.cancel()
        self.current_timer = asyncio.get_event_loop().call_later(length, lambda: self.voting_phase())
        self.area.broadcast_ooc('Discussion time!')
        self.area.play_music(random.choice(music[self.current_phase]), -1)

    def voting_phase(self):
        """
        Start the voting phase

        """
        if self.current_timer:
            self.current_timer.cancel()
        last_phase = self.current_phase
        self.current_timer = asyncio.get_event_loop().call_later(self.voting_length, lambda: self.voting_end(last_phase))
        self.area.broadcast_ooc('Voting time!')
        self.current_phase = "voting"
        self.area.play_music(random.choice(music[self.current_phase]), -1)

    def vote(self, client, arg):
        if len(arg) == 0:
            client.send_ooc('You must specify a target.')
            return
        try:
            targets = client.server.client_manager.get_targets(
                client, TargetType.ID, int(arg), False)
        except:
            client.send_ooc('You must specify a target. You can\'t vote for yourself. Use /vote <id>.')
            return

        if targets:
            c = targets[0]
            client.area.gamemode.vote(client, arg)
        else:
            client.send_ooc('No targets found.')
        if not client.area.gamemode.current_phase == "voting":
            client.send_ooc('You can only vote during the voting phase.')
            return
        if self.votes[client.id]:
            client.send_ooc('You already voted!')
            return
        client.send_ooc(f'You voted for {target.char_name}.')
        self.votes[client.id] = target.id

    def voting_end(self, last_phase):
        """
        End the voting phase and handle if we head to next discussion
        or handle the results

        """
        print(last_phase)
        if last_phase == "preliminary":
            self.current_phase = "finals"
            if self.current_timer:
                self.current_timer.cancel()
            self.current_timer = asyncio.get_event_loop().call_later(self.voting_length, lambda: self.discussion_phase(self.final_discussion_time))
        elif last_phase == "finals":
            if self.current_timer:
                self.current_timer.cancel()
            self.current_timer = asyncio.ensure_future(self.handle_winners())

    async def handle_winners(self):
        """
        Execute people who are losers, give winners their limelight

        """
        self.area.play_music(random.choice(music['sacrifice']), -1)
        self.area.broadcast_ooc('LOL!')
        await asyncio.sleep(1)
        self.area.broadcast_ooc('YOU!')
        await asyncio.sleep(1)
        self.area.broadcast_ooc('BOUTTA!')
        await asyncio.sleep(1)
        self.area.broadcast_ooc('DIE!')
        await asyncio.sleep(1)
        print(self.votes)