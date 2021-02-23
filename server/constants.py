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


ESCAPE_CHARACTERS = {
    '%': '<percent>',
    '#': '<num>',
    '$': '<dollar>',
    '&': '<and>'
}
