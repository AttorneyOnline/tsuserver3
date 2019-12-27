import gettext
import warnings
import yaml
from copy import deepcopy
from types import MethodType
from typing import Iterable

import pygubu
from pygubu.widgets.editabletreeview import EditableTreeview

import jsonpatch

import tkinter as tk
import tkinter.messagebox

from . import edittypes

t = gettext.translation("tsuserver_config", "translations")
_ = t.gettext


def hack_etv(etv: EditableTreeview):
    """Hack up Pygubu's half-decent EditableTreeview in various ways:
     - Make the in-place widgets only trigger on double click, not single click.
     - Make a way for the created inplace widget to be accessed (and
       focused to).
    """
    # Had to look up what the heck a double underscore meant. Apparently
    # it makes a textual substitution for an abomination.
    updateWnds = etv._EditableTreeview__updateWnds
    etv._EditableTreeview__updateWnds = lambda: None
    etv.bind('<Double-Button-1>', updateWnds)
    etv.bind('<Return>', updateWnds)
    etv.forceUpdateWnds = updateWnds

    def inplace_widget(self, col):
        return self._inplace_widgets[col]
    etv.inplace_widget = MethodType(inplace_widget, etv)

def walk(d: dict, path):
    """Walks a dictionary and then returns a class that references the
    element at the path.
    """
    elem = d
    path = path.split('/')[1:]
    for x in path[:-1]:
        elem = elem[x]

    class DictValue:
        """This is really stupid."""
        @property
        def value(self):
            return elem[path[-1]]
        @value.setter
        def value(self, val):
            elem[path[-1]] = val
        @value.deleter
        def value(self):
            del elem[path[-1]]

    return DictValue()

class TsuserverConfig:
    def __init__(self):
        self.builder = builder = pygubu.Builder(_)
        builder.add_from_file("ui/main.ui")
        self.main_window = builder.get_object("tsuserver_config_toplevel")
        self.etv: EditableTreeview = builder.get_object("etv")
        self.btn_apply = builder.get_object('btn_apply')
        self.btn_revert = builder.get_object('btn_revert')
        hack_etv(self.etv)
        builder.connect_callbacks(self)

        self._reload_config()
        self.etv.bind('<<TreeviewInplaceEdit>>', self._on_inplace_edit)
        #self.etv.bind('<Double-Button-1>', self._on_inplace_edit)
        self.etv.bind('<<TreeviewCellEdited>>', self._on_cell_edited)

    def run(self):
        self.main_window.mainloop()

    def quit(self, event=None):
        self.main_window.quit()

    def _reload_config(self):
        # msg = _('This will discard all changes.')
        # if not tk.messagebox.askokcancel(_('Reload Config'), msg):
        #     return

        self.etv.delete(*self.etv.get_children())
        self._delete_inplace_widgets()

        self.etv_meta_dict = {}
        self.options_orig = {
            '$config': { 'name': 'General' },
            'config': yaml.safe_load(open('config/config.yaml')),
            '$music': { 'name': 'Music', 'type': 'music' },
            'music': yaml.safe_load(open('config/music.yaml')),
            '$areas': { 'name': 'Rooms', 'type': 'rooms' },
            'areas': yaml.safe_load(open('config/areas.yaml')),
            '$backgrounds': { 'name': 'Backgrounds' },
            'backgrounds': yaml.safe_load(open('config/backgrounds.yaml')),
            '$characters': { 'name': 'Characters' },
            'characters': yaml.safe_load(open('config/characters.yaml'))
        }
        self.options = deepcopy(self.options_orig)
        self.unpack_dict(self.options)
        self._check_config()

    def _make_patch(self):
        patch = jsonpatch.make_patch(self.options_orig,
                                     deepcopy(self.options)).patch

        # Ignore all patches involving metadata
        patch = [p for p in patch if '/$' not in p['path']]
        def prune_dollars(d: dict):
            for k, v in list(d.items()):
                if isinstance(k, str) and k[0] == '$':
                    del d[k]
                elif isinstance(v, dict):
                    prune_dollars(v)
                elif isinstance(v, list):
                    prune_dollars(enumerate(v))
        for p in patch:
            if 'value' in p:
                prune_dollars(p['value'])

        return patch

    def _apply_changes(self):
        patch = self._make_patch()
        changes_str = ''
        msg = _('The following changes will be COMMITTED:\n')
        for entry in patch:
            changes_str += _(f'- {entry["op"].upper()} {entry["path"]}')
            if entry['op'] == 'replace':
                changes_str += _(f' with value {entry["value"]}')
            changes_str += '\n'
        msg += changes_str
        msg += _('Do you wish to continue?')
        if tk.messagebox.askokcancel(_('Commit Changes'), msg, icon='warning'):
            self.options_orig = deepcopy(self.options)

    def _check_config(self):
        patch = self._make_patch()
        state = ['!disabled' if len(patch) > 0 else 'disabled']
        self.btn_apply.state(state)
        self.btn_revert.state(state)

    def unpack_items(self, it: Iterable, *args, key_name=None, **kwargs):
        if key_name is not None:
            kv = dict(
                **{str(k): v for k, v in enumerate(it)},
                **{f'${k}': { 'name': v[key_name] } for k, v in enumerate(it)}
            )
        else:
            kv = {str(k): v for k, v in enumerate(it)}
        return self.unpack_dict(kv, *args, **kwargs)

    def unpack_dict(self, d: dict, parent=''):
        for k, v in d.items():
            if k[0] == '$':
                continue

            id = f'{parent}/{k}'
            name = k
            desc = ''
            key_name = None

            try:
                metadata = d['$' + k]
            except KeyError:
                metadata = {}
            try:
                edit_type = metadata['type']
            except KeyError:
                edit_type = type(v)

            edit_type = edittypes.get(edit_type)(self.etv, metadata)

            edit_type.preprocess(v)

            if 'desc' in metadata:
                desc = metadata['desc']
            if 'name' in metadata:
                name = metadata['name']
            if 'key_name' in metadata:
                key_name = metadata['key_name']


            self.etv_meta_dict[id] = {
                'name': name,
                'desc': desc,
                'type': edit_type,
                'key_name': key_name
            }

            self.etv.insert(parent, tk.END, id, text=name,
                            values=edit_type.row(v))

            if isinstance(v, dict):
                self.unpack_dict(v, parent=id)
            elif isinstance(v, list):
                self.unpack_items(v, key_name=key_name, parent=id)

    def _on_inplace_edit(self, _event):
        """Called when an value is activated for editing."""
        col, item = self.etv.get_event_info()
        if col != 'col_value':
            return

        self._delete_inplace_widgets()

        meta = self.etv_meta_dict[item]
        edit_type = meta['type']

        me = self
        class Proxy:
            def unpack_dict(self, d, item):
                me.unpack_dict(d, item)
                me._check_config()

            @property
            def option(self):
                return walk(me.options, item).value

            @option.setter
            def option(self, value):
                walk(me.options, item).value = value
                me._check_config()

            @option.deleter
            def option(self):
                del walk(me.options, item).value
                me._check_config()

        edit_type.on_edit(col, item, Proxy())

        try:
            self.etv.inplace_widget(col).focus_force()
        except KeyError:
            pass

    def _on_cell_edited(self, _event):
        """Called when a value is done being edited."""
        _col, item = self.etv.get_event_info()

        val = self.etv.item(item, 'values')[0]
        edit_type = self.etv_meta_dict[item]['type']
        real_val = edit_type.value(val)
        if real_val is None:
            return

        walk(self.options, item).value = real_val
        self._check_config()

    def _delete_inplace_widgets(self):
        """This is stupid. I should NOT have to be doing this.
        I am this close to forking EditableTreeview.
        """
        col = 'col_value'
        try:
            self.etv.inplace_widget(col).destroy()
            del self.etv._inplace_widgets[col]
        except KeyError:
            pass

def main():
    application = TsuserverConfig()
    application.run()