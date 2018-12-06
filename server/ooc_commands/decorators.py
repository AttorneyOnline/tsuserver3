# tsuserver3, an Attorney Online server
#
# Copyright (C) 2018 argoneus <argoneuscze@gmail.com>
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

"""
These decorators serve to avoid code repetition in common OOC command checks.

Note the order of the decorators matters, typically the message to be sent
to be user will be the outermost failing decorator.
"""

import functools

from server.exceptions import ClientError, ArgumentError


def mod_only(f):
    """ Command requires you to be logged in as a moderator. """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        client = args[0]
        if not client.is_mod:
            raise ClientError('You must be logged in as a moderator to do that.')
        return f(*args, **kwargs)

    return wrapper


def area_owner(f):
    """ Command requires you to be the current area owner (or a moderator). """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        client = args[0]
        if not client.is_mod and client not in client.area.owners:
            raise ClientError('You must be either a moderator or the area owner to do that.')
        return f(*args, **kwargs)

    return wrapper


def no_args(f):
    """ Command doesn't take any arguments. """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        arg = args[1]
        if len(arg) != 0:
            raise ArgumentError('This command takes no arguments.')
        return f(*args, **kwargs)

    return wrapper


def require_arg(error='This command requires an argument.'):
    """ Command requires an argument, you may provide a custom error message via the `error` kwarg.
     Note as this is a decorator factory, you need to call it as a function to get default arguments:
     @require_arg()
     @require_arg(error='Custom error')
    """

    def require_arg_func(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            arg = args[1]
            if len(arg) == 0:
                raise ArgumentError(error)
            return f(*args, **kwargs)

        return wrapper

    return require_arg_func
