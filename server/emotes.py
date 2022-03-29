from os import path
from configparser import ConfigParser

import logging

logger = logging.getLogger("debug")

char_dir = "characters"


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
        char_ini = ConfigParser(
            comment_prefixes=("=", "-", "#", ";", "//", "\\\\"),
            allow_no_value=True,
            strict=False,
            empty_lines_in_values=False,
        )
        try:
            char_path = path.join(char_dir, self.name, "char.ini")
            with open(char_path, encoding="utf-8-sig") as f:
                char_ini.read_file(f)
                logger.info(
                    f"Found char.ini for {char_path} that can be used for iniswap restrictions!"
                )
        except FileNotFoundError:
            return

        # cuz people making char.ini's don't care for no case in sections
        char_ini = dict((k.lower(), v) for k, v in char_ini.items())
        try:
            for emote_id in range(1, int(char_ini["emotions"]["number"]) + 1):
                try:
                    emote_id = str(emote_id)
                    _name, preanim, anim, _mod = char_ini["emotions"][
                        str(emote_id)
                    ].split("#")[:4]
                    # if "soundn" in char_ini and emote_id in char_ini["soundn"]:
                    #     sfx = char_ini["soundn"][str(emote_id)] or ""
                    #     if sfx != "" and len(sfx) == 1:
                    #         # Often, a one-character SFX is a placeholder for no sfx,
                    #         # so allow it
                    #         sfx = ""
                    # else:
                    #     sfx = ""

                    # sfx checking is not performed due to custom sfx being possible, so don't bother for now
                    sfx = ""
                    self.emotes.add(
                        (preanim.lower(), anim.lower(), sfx.lower()))
                except KeyError as e:
                    logger.warn(
                        f"Broken key {e.args[0]} in character file {char_path}. "
                        "This indicates a malformed character INI file."
                    )
        except KeyError as e:
            logger.warn(
                f"Unknown key {e.args[0]} in character file {char_path}. "
                "This indicates a malformed character INI file."
            )
            return
        except ValueError as e:
            logger.warn(
                f"Value error in character file {char_path}:\n{e}\n"
                "This indicates a malformed character INI file."
            )
            return

    def validate(self, preanim, anim, sfx):
        """
        Determines whether or not an emote canonically belongs to this
        character (that is, it is defined server-side).
        """
        # There are no emotes loaded, so allow anything
        if len(self.emotes) == 0:
            return True

        # if len(sfx) <= 1:
        #     sfx = ""

        # sfx checking is skipped due to custom sound list
        sfx = ""
        return (preanim.lower(), anim.lower(), sfx.lower()) in self.emotes
