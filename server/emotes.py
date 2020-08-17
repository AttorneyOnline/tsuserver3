from os import path
from configparser import ConfigParser

import logging
logger = logging.getLogger('debug')

char_dir = 'characters'


class Emotes:
    """
    Represents a list of emotes read in from a character INI file
    used for validating which emotes can be sent by clients.
    """

    def __init__(self, name):
        self.name = name
        self.emotes = set()
        self.read_ini()

    def read_ini(self):
        char_ini = ConfigParser(comment_prefixes=('-', '#', ';', '//', '\\\\'),
                                strict=False, empty_lines_in_values=False)
        try:
            char_path = path.join(char_dir, self.name, 'char.ini')
            with open(char_path, encoding='utf-8-sig') as f:
                char_ini.read_file(f)
        except FileNotFoundError:
            logger.warn(f'Character file {char_path} not found')
            return

        # cuz people making char.ini's don't care for no case in sections
        char_ini = dict((k.lower(), v) for k, v in char_ini.items())
        try:
            for emote_id in range(1, int(char_ini['emotions']['number']) + 1):
                emote_id = str(emote_id)
                _name, preanim, anim, _mod = char_ini['emotions'][str(emote_id)].split('#')[:4]
                if emote_id in char_ini['soundn']:
                    sfx = char_ini['soundn'][str(emote_id)]
                    if len(sfx) == 1:
                        # Often, a one-character SFX is a placeholder for no sfx,
                        # so allow it
                        sfx = None
                else:
                    sfx = None
                self.emotes.add((preanim, anim, sfx))

                # No SFX should always be allowed
                self.emotes.add((preanim, anim, None))
        except KeyError as e:
            logger.warn(f'Unknown key {e.args[0]} in character file {char_path}. '
                        'This indicates a malformed character INI file.')
            return

    def validate(self, preanim, anim, sfx):
        """
        Determines whether or not an emote canonically belongs to this
        character (that is, it is defined server-side).
        """
        # There are no emotes loaded, so allow anything
        if len(self.emotes) == 0:
            return True

        if len(sfx) <= 1:
            sfx = None
        return (preanim, anim, sfx) in self.emotes
