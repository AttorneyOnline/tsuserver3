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

def reload():
    """Reload all submodules."""
    import sys, inspect, importlib
    me = sys.modules[__name__]
    for _, v in inspect.getmembers(me):
        if inspect.ismodule(v):
            m = importlib.reload(v)
            for f in m.__all__:
                me.__dict__[f] = m.__dict__[f]


def help(command):
    import sys
    try:
        return getattr(sys.modules[__name__], command).__doc__
    except AttributeError:
        return 'No help found for that command.'


def mod_only(area_owners=False):
    import functools
    from ..exceptions import ClientError
    def decorator(func):
        @functools.wraps(func)
        def wrapper_mod_only(client, arg, *args, **kwargs):
            if not client.is_mod and (not area_owners or not client in area_owners):
                raise ClientError('You must be authorized to do that.')
            func(client, arg, *args, **kwargs)
        return wrapper_mod_only
    return decorator


# Note that only the members of __all__ in each module will be imported.
# There must be an __all__ in each module in order for reloading
# to work properly.
from .admin import *
from .area import *
from .casing import *
from .character import *
from .fun import *
from .messaging import *
from .music import *
from .roleplay import *
