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
    'prelim': ['room escape and gameplay/[VLR] Lounge.ogg',
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

        self.current_task = None #Current timer going on, whether it be signups, prelim discussion or final discussion
        self.signups = [] #clients who signed up
        self.signup_length = 5 #* 60 #outputs in seconds
        self.min_signups = 1 #5 #minimum amount of clients needed for a single round
        self.prelim_coefficient = 0.5 #Half of the participants must make it into prelims (floored)
        self.minimum_required = 3 #minimum required candidates for preliminary
        self.prelim_discussion_time = 5 #30 #* 60 #outputs in seconds
        self.final_discussion_time = 5 #20 #* 60 #outputs in seconds

        self.current_phase = "" #The phase we're on
        self.votes = {} #The vote dictionary we collected
        self.voting_length = 10 #60 #One minute for the voting period

        #index 0 highest priority, index 3 = lowest priority (for the tiebreaker). Anything not on the list has lowest priority (commoner)
        self.roles = ['keymaster', 'sacrifice', 'sage']

        self.distributed_roles = {} #dictionary containing everyone's role associations

        self.characters = {}

        self.candidates = [] #candidates for voting

    def cleanup(self):
        self.votes.clear()
        self.candidates.clear()
        self.distributed_roles.clear()
        self.characters.clear()
        self.current_phase = ""

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

    def start_timer(self, length, callback):
        print(f'starting timer with length {length} on callback {callback}')
        self.current_task = asyncio.get_event_loop().create_task(self.timer(length, callback))
    
    def cancel_timer(self):
        async def cancel_task(task):
            if task and not task.cancelled():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    print('Schedule succesfully cancelled')
        asyncio.ensure_future(cancel_task(self.current_task))
        self.current_task = None

    async def timer(self, length, callback):
        try:
            ticks = 10 #HP bar segments
            time_fraction = length/ticks #resulting loop until which ticks are exhausted
            self.area.change_hp(1, ticks)
            print('timer async exists now')
            while ticks > 0:
                await asyncio.sleep(time_fraction)
                ticks -= 1
                self.area.change_hp(1, ticks)
            print(f'callback {callback} called')
            callback()
        except asyncio.CancelledError:
            print(f'task {length} {callback} is being cancelled')
            raise

    def set_role(self, client, role):
        self.distributed_roles[client.id] = role
        msg = f'Your role is a {role}.'
        if role == 'sacrifice':
            msg += '\nAbility: Can cast two votes instead of one during any Voting Period without restriction.'
            msg += '\nMajority Vote: Everyone except you and your chosen survivor dies.'
            msg += '\nTo Survive: Get the Majority Vote.'
            client.send_ooc(msg)
        elif role == 'keymaster':
            msg += '\nAbility: Can be considered an Unsafe Vote due to the Majority Vote outcome.'
            msg += '\nMajority Vote: Everyone dies.'
            msg += '\nTo Survive: Avoid the Majority Vote.'
            msg += '\n      Prevent the Sacrifice from getting the Majority Vote.'
            msg += '\n      Alternatively, get chosen by the Sacrifice after Sacrifice victory.'
            client.send_ooc(msg)
        elif role == 'sage':
            msg += '\nAbility: Divination - learns the Keymaster\'s identity at the start of the Main Game. Cannot lie about their act of Divination.'
            msg += '\nMajority Vote: You and the Sacrifice die.'
            msg += '\nTo Survive: Avoid the Majority Vote.'
            msg += '\n      Prevent Keymaster and Sacrifice from getting the Majority Vote.'
            msg += '\n      Alternatively, get chosen by the Sacrifice after Sacrifice victory.'
            client.send_ooc(msg)
        else:
            msg += '\nAbility: Nothing.'
            msg += '\nMajority Vote: You and the Sacrifice die.'
            msg += '\nTo Survive: Avoid the Majority Vote.'
            msg += '\n      Prevent Keymaster and Sacrifice from getting the Majority Vote.'
            msg += '\n      Alternatively, get chosen by the Sacrifice after Sacrifice victory.'
        client.send_ooc(msg)

    def distribute_roles(self):
        roles_left = self.roles.copy().reverse()
        candidates = self.signups.copy()
        random.shuffle(candidates)
        for client in candidates:
            if len(roles_left) <= 0:
                self.set_role(client, 'commoner')
                continue
            self.set_role(client, roles_left.pop())

    def get_role_targets(self, target_role):
        targets = []
        for key in self.distributed_roles.keys():
            role = self.distributed_roles[key]
            if role == target_role:
                targets.append(key)
        return targets

    def divine(self):
        for client in self.get_role_targets('sage'):
            msg = 'You just received your divination!'
            keymaster = self.characters[self.get_role_targets('keymaster')[0]]
            msg += f'\nThe Keymaster is {keymaster}.'
            msg += '\nRemember: you cannot lie about your Divination.'
            client.send_ooc(msg)

    def start_building(self):
        """
        Begin the sign-up process and start the game when done.
        """
        self.area.broadcast_ooc(f'Building has started. Round will begin in {self.signup_length} seconds.')
        self.current_phase = "signups"
        self.area.change_status('lfp')
        self.start_timer(self.signup_length, lambda: self.round_start())

    def round_start(self):
        """
        Make the area spectate only and begin the round.
        If there are not enough players, restart the sign-ups timer.
        """
        if len(self.signups) < self.min_signups:
            self.start_building()
            return
        self.cleanup()
        msg = '==Participants=='
        for client in self.signups:
            self.characters[client.id] = client.char_name
            msg += f'\n[{client.id}] {client.char_name}'
        self.area.broadcast_ooc(msg)

        self.area.change_status('rp')
        self.distribute_roles()
        self.start_timer(10, lambda: self.discussion_phase("prelim"))

    def round_end(self):
        """
        End the round, nuking any data we collected.
        """
        self.cleanup()
        self.cancel_timer()
        self.area.change_hp(1, 10) #refill the HP bar
        self.area.broadcast_ooc('YTTD round has ended.')
        self.area.change_status('idle')

    def discussion_phase(self, phase):
        """
        Start the discussion phase
        """
        self.current_phase = phase
        time = self.prelim_discussion_time
        if phase == "finals":
            time = self.final_discussion_time
        else:
            self.divine() #since this is prelims, send the divination to the Sage.

        m, s = divmod(time, 60)
        self.area.broadcast_ooc(f'Discussion time!\nYou have {m:02d} minutes {s:02d} seconds to debate.')
        self.area.play_music(random.choice(music[phase]), -1)

        self.start_timer(time, lambda: self.voting_phase())

    def voting_phase(self):
        """
        Start the voting phase
        """
        self.votes.clear() #Clear the votes due to the start of a new voting period
        if self.current_phase != 'finals':
            self.candidates = self.signups.copy()
        self.start_timer(self.voting_length, lambda: self.handle_vote_results(self.current_phase))
        
        self.area.broadcast_ooc('Voting time!\nUse /vote <id> or /vote <charname> to cast your vote.\nYou can\'t vote for yourself.')
        self.current_phase = "voting"
        self.area.play_music(random.choice(music[self.current_phase]), -1)

    def handle_vote_results(self, phase):
        self.current_phase = "results"
        if phase == 'finals':
            self.start_timer(5, lambda: self.handle_winners())
            return

        votecount = {}
        for value in self.votes:
            if value not in votecount.keys():
                votecount[value] = 0
            votecount[value] += 1

        votecount = sorted(votecount.items(), key = lambda kv:(kv[1], kv[0]))

        for Set in votecount:
            self.area.broadcast_ooc(f'{self.characters[Set[0]]} has {votecount[Set[1]]} votes.')

        self.area.broadcast_ooc(f'lol so uhh these guys made it to finals {votecount[:self.minimum_required]}')        
        self.start_timer(5, lambda: self.discussion_phase('finals'))

    def vote(self, client, arg):
        """
        ?
        """
        if self.current_phase != "voting":
            client.send_ooc('You can only vote during the voting phase.')
            return

        if len(arg) == 0:
            client.send_ooc('You must specify a target. Use /vote <id> or /vote <charname>.')
            return

        target = None
        try:
            for c in self.candidates:
                if c == client:
                    continue
                if c.id == int(arg):
                    target = c
                    break
                if arg.lower().startswith(
                        c.char_name.lower()):
                    target = c
                    break
        except:
            client.send_ooc('You must specify a target. You can\'t vote for yourself. Use /vote <id> or /vote <charname>.')
            return

        if target:
            if client.id in self.votes.keys():
                client.send_ooc('You already voted!')
                return
            client.send_ooc(f'You voted for {target.char_name}.')
            self.votes[client.id] = target.id
        else:
            client.send_ooc('Invalid target. Use /vote <id> or /vote <charname>.')

    def handle_winners(self):
        """
        Execute people who are losers, give winners their limelight
        """
        self.area.play_music(random.choice(music['sacrifice']), -1)

        async def timer(gm):
            try:
                await asyncio.sleep(1)
                gm.area.broadcast_ooc('YOU!')
                await asyncio.sleep(1)
                gm.area.broadcast_ooc('BOUTTA!')
                await asyncio.sleep(1)
                gm.area.broadcast_ooc('DIE!')
                await asyncio.sleep(1)
                gm.display_results(True)
            except asyncio.CancelledError:
                gm.area.broadcast_ooc('aw i got cancelled :(')

        self.current_task = asyncio.get_event_loop().create_task(timer(self))

    def display_results(self, final=False):
        votecount = {}
        for value in self.votes:
            if value not in votecount.keys():
                votecount[value] = 0
            votecount[value] += 1
        
        for key in votecount.keys():
            self.area.broadcast_ooc(f'{self.characters[key]} has {votecount[key]} votes.')

        if final:
            for key in self.votes.keys():
                self.area.broadcast_ooc(f'{self.characters[key]} voted for {self.characters[self.votes[key]]}')