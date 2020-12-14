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

class Testimony:
    """Represents a complete group of statements to be pressed or objected to."""
    
    def __init__(self, title):
        self.title = title
        self.statements = []
    
    def add_statement(self, message):
        """Add a statement and return whether successful."""
        if len(self.statements) + 1 >= 30: # if you write a testimony longer than 30 statements, don't
            return False
        self.statements = self.statements.append(message)
        return True
    
    def remove_statement(self, index):
        """Remove the statement at index [index]."""
        if index < 1 or index > len(self.statements) + 1:
            return False
        for statement in self.statements:
            if statement.index() == index - 1:
                statement.remove()
                return True
        return False # shouldn't happen
                
    def amend_statement(self, index, message):
        """Amend the statement at index [index] to instead contain [message]."""
        if index < 1 or index > len(self.statements) + 1:
            return False
        self.statements = [x if x.index() == index - 1 else message for x in self.statements]
        return True

    