from server.client_manager import ClientManager
from dataclasses import dataclass
from collections import Counter
from typing import Union, Tuple
from threading import Timer
import random
import asyncio
@dataclass
class JukeboxVote:
    """Represents a single vote cast for the jukebox."""
    client: ClientManager.Client
    name: str
    length: int
    showname: str
    chance: int = 1

class Jukebox:
    def __init__(self, area):
        self.area = area
        self.votes = []
        self.jukebox_prev_char_id = -1
        self.music_looper = None
        self.playing = False

    def add_jukebox_vote(self, client: ClientManager.Client, music_name: str, length: int = -1, showname: str = ''):

        # If a length for a song doesn't exist, the server
        # doesn't know when to play the next song
        if length == -1:
            client.send_ooc(f'{music_name} needs a length set.')
            return

        # You can only have one vote 
        # in the queue at a time
        self.remove_jukebox_vote(client)

        self.votes.append(JukeboxVote(client, music_name, length, showname))
        client.send_ooc('Your song was added to the jukebox.')

        if len(self.votes) > 0:
            self.play()

    def play(self):
        song_picked, song_length = self.get_next_song_in_queue()
        if song_picked == '':
            self.area.broadcast_ooc('No other songs in the voting queue.')
            return 

        if self.playing is False:
            self.area.send_command('MC', song_picked, song_length)
            self.playing = True

            # Set not playing once song is done running
            asyncio.get_event_loop().call_later(song_length, self.set_not_playing)

    def find_length(self, song_name: str) -> int:
        vote: JukeboxVote

        for vote in self.votes:
            if vote.name == song_name:
                return vote.length
        return -1

    def get_next_song_in_queue(self) -> Tuple[str, int]:
        if len(self.votes) == 0:
            return '', -1

        picked_songs = [vote.name for vote in self.votes]
        song_frequency_occurrence = Counter(picked_songs)
        highest_occuring: tuple = song_frequency_occurrence.most_common(1)[0]
        highest_occuring_song = highest_occuring[0]

        if len(highest_occuring) == 0:
            highest_occuring_song = ''
        else:
            highest_occuring_song: str = highest_occuring[0]

        length = self.find_length(highest_occuring_song)
        return highest_occuring_song, length
    
    def set_not_playing(self):
        self.playing = False
        self.play()
        self.votes = []


    
    def remove_jukebox_vote(self, client: ClientManager.Client):
        """Removes a vote on the jukebox.
        Args:
            client (ClientManager.Client): client whose vote should be removed
        """
        vote: JukeboxVote

        for vote in self.votes:
            if vote.client.id == client.id:
                self.votes.remove(vote)