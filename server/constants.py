# KFO-Server, an Attorney Online server
#
# Copyright (C) 2020 Crystalwarrior <varsash@gmail.com>
#
# Derivative of tsuserver3, an Attorney Online server. Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
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

import re
from enum import Enum
from enum import IntFlag


class TargetType(Enum):
    # possible keys: ip, OOC, id, cname, ipid, hdid, afk
    IP = 0
    OOC_NAME = 1
    ID = 2
    CHAR_NAME = 3
    IPID = 4
    HDID = 5
    ALL = 6
    AFK = 7


class MusicEffect(IntFlag):
    FADE_IN = 1
    FADE_OUT = 2
    SYNC_POS = 4


def dezalgo(input, tolerance=3):
    """
    Turns any string into a de-zalgo'd version, with a tolerance to allow for normal diacritic use.

    The following Unicode blocks are scrubbed:
    U+0300 - U+036F - COMBINING DIACRITICAL MARKS
    U+1AB0 - U+1AFF - COMBINING DIACRITICAL MARKS EXTENDED
    U+1DC0 - U+1DFF - COMBINING DIACRITICAL MARKS SUPPLEMENT
    U+20D0 - U+20FF - COMBINING DIACRITICAL MARKS FOR SYMBOLS
    U+FE20 - U+FE2F - COMBINING HALF MARKS
    U+115F          - HANGUL CHOSEONG FILLER
    U+1160          - HANGUL JUNGSEONG FILLER
    U+3164          - HANGUL FILLER
    """

    filtered = re.sub(
        "([\u0300-\u036f\u1ab0-\u1aff\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f"
        + "\u115f\u1160\u3164]"
        + "{"
        + re.escape(str(tolerance))
        + ",})",
        "",
        input,
    )
    return filtered


def censor(text, censor_list=[], replace="*", whole_words=True):
    """
    Checks if the string contains any of the passed restricted words and replaces them with the replace char.
    Returns a parsed string.
    :param censor_list: list of swear words to replace
    :param replace: what to replace every letter of the word with
    :param whole_word: if true, we'll only match full words instead of partial matches
    """
    if censor_list is None or len(censor_list) <= 0:
        return text
    regex = r"%s"
    if whole_words:
        regex = r"\b%s\b"
    for word in censor_list:
        text = re.sub(regex % word, len(word) * replace,
                      text, flags=re.IGNORECASE)
    return text


def remove_URL(sample):
    """Remove URLs from a sample string"""
    return re.sub(r"http\S+", "", sample)


def contains_URL(sample):
    """Determine if string contains a URL in sample string."""
    return re.match(r"http\S+", sample) is not None


def encode_ao_packet(params):
    new_params = []
    for arg in params:
        if type(arg) is tuple:
            encoded = []
            for tup in arg:
                encoded.append(
                    str(tup)
                    .replace("#", "<num>")
                    .replace("%", "<percent>")
                    .replace("$", "<dollar>")
                    .replace("&", "<and>")
                )
            new_params.append(tuple(encoded))
        else:
            new_params.append(
                str(arg)
                .replace("#", "<num>")
                .replace("%", "<percent>")
                .replace("$", "<dollar>")
                .replace("&", "<and>")
            )
    return new_params
