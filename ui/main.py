import gettext
import warnings
import yaml
from copy import deepcopy
from types import MethodType

import pygubu
from pygubu.widgets.editabletreeview import EditableTreeview

import jsonpatch

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox
import tkinter.simpledialog


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

        # self.etv.insert('', tk.END, '/', text="Root", values=("root",))
        # self.etv.insert('/', tk.END, '/hello', text="Hello", values=("hello",))
        # self.etv.insert('/', tk.END, '/world', text="World", values=("world",))
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
        self.options_orig = yaml.safe_load(open('config/config.yaml'))
        self.options = deepcopy(self.options_orig)
        self.unpack_dict(self.options)
        self._check_config()

    def _apply_changes(self):
        patch = jsonpatch.make_patch(self.options_orig, self.options).patch
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
        patch = jsonpatch.make_patch(self.options_orig, self.options).patch
        state = ['!disabled' if len(patch) > 0 else 'disabled']
        self.btn_apply.state(state)
        self.btn_revert.state(state)

    def unpack_dict(self, d: dict, parent=''):
        for k, v in d.items():
            if k[0] == '$':
                continue

            id = f'{parent}/{k}'
            name = k
            desc = ''

            edit_types = {
                str: 'string',
                int: 'number',
                dict: 'object',
                bool: 'boolean'
            }
            edit_type = edit_types[type(v)]
            try:
                metadata = d['$' + k]
                if 'desc' in metadata:
                    desc = metadata['desc']
                if 'type' in metadata:
                    edit_type = metadata['type']
                if 'name' in metadata:
                    name = metadata['name']
            except KeyError:
                pass

            self.etv_meta_dict[id] = {
                'name': name,
                'desc': desc,
                'type': edit_type
            }

            if isinstance(v, dict):
                values = ('<object>', desc)
            else:
                values = (v, desc)

            self.etv.insert(parent, tk.END, id, text=name, values=values)

            if isinstance(v, dict):
                self.unpack_dict(v, parent=id)

    def _on_inplace_edit(self, _event):
        """Called when an value is activated for editing."""
        col, item = self.etv.get_event_info()
        if col != 'col_value':
            return

        self._delete_inplace_widgets()

        meta = self.etv_meta_dict[item]
        edit_type = meta['type']
        if edit_type == 'string':
            self.etv.inplace_entry(col, item)
        elif edit_type == 'number':
            self.etv.inplace_spinbox(col, item, 0, 65536, 1)
        elif edit_type == 'boolean':
            self.etv.inplace_checkbutton(col, item)
        elif edit_type == 'none':
            pass
        elif edit_type == 'mod':
            option = walk(self.options, item)
            if isinstance(option.value, str):
                # Old-style modpass. Ask if user wants to convert it to a
                # new-style pass.
                msg = _('You have an old-style modpass. Do you wish to convert ' \
                        'it to a multi-profile modpass?')
                if 'ignore_prompt' not in meta and \
                        tk.messagebox.askyesno(message=msg, icon='warning'):
                    modpass = option.value
                    option.value = {
                        'default': {
                            'password': modpass
                        }
                    }
                    self.unpack_dict(option.value, item)
                    values = self.etv.item(item, 'values')
                    values = ('<object>', *values[1:])
                    self.etv.item(item, values=values)
                    self._check_config()
                else:
                    # Fine. Screw you then.
                    meta['ignore_prompt'] = True
                    self.etv.inplace_entry(col, item)
                    return

            # Show a button.
            self.etv.inplace_custom(col, item, ttk.Button(self.etv, text='+'))
            def add_mod_entry(_event):
                msg = _('Enter the profile name of the mod:')
                profile = tk.simpledialog.askstring(_('New Mod'), msg)
                if profile is None:
                    return
                profile = profile.strip()
                if profile == '':
                    return

                modpass_list = walk(self.options, item).value
                if profile in modpass_list:
                    msg = _('That profile already exists.')
                    tk.messagebox.showerror(_('New Mod'), msg)

                modpass_list[profile] = {
                    'password': 'modpass'
                }
                self.unpack_dict({
                    profile: modpass_list[profile]
                }, item)
                self._check_config()

            self.etv.inplace_widget(col).bind('<Button-1>', add_mod_entry)
            self.etv.forceUpdateWnds()
        elif edit_type == 'object':
            # Special case for mod entries: Add a minus button.
            up = '/'.join(item.split('/')[:-1])
            if self.etv_meta_dict[up]['type'] == 'mod':
                self.etv.inplace_custom(col, item, ttk.Button(self.etv, text='-'))
                def remove_mod_entry(_event):
                    profile = item.split('/')[-1]
                    msg = _(f'Mod profile \'{profile}\' will be deleted.')
                    if tk.messagebox.askokcancel('Delete Mod', msg):
                        self.etv.delete(item)
                    self._check_config()

                self.etv.inplace_widget(col).bind('<Button-1>', remove_mod_entry)
                self.etv.forceUpdateWnds()
        else:
            warnings.warn(f'options dict has invalid edit type {edit_type}')

        try:
            self.etv.inplace_widget(col).focus_force()
        except KeyError:
            pass

    def _on_cell_edited(self, _event):
        """Called when a value is done being edited."""
        _col, item = self.etv.get_event_info()

        val = self.etv.item(item, 'values')[0]
        edit_type = self.etv_meta_dict[item]['type']
        if edit_type == 'string':
            pass
        elif edit_type == 'number':
            val = int(val)
        elif edit_type == 'boolean':
            val = True if val == 'True' else False
        elif edit_type == 'mod' and type(val) == str:
            pass
        else:
            return

        walk(self.options, item).value = val

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