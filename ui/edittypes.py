import gettext
from typing import Union

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog

t = gettext.translation("tsuserver_config", "translations")
_ = t.gettext

def get(t: Union[str, type]):
    return {
        str: String,
        int: Number,
        dict: Object,
        bool: Boolean,
        list: List,
        'none': EditType,
        'string': String,
        'number': Number,
        'object': Object,
        'boolean': Boolean,
        'list': List,
        'music': Music,
        'rooms': Rooms,
        'mod': Mod,
        'modentry': ModEntry,
        'multiline': Multiline
    }[t]

class EditType:
    def __init__(self, etv, metadata):
        self.etv = etv
        self.meta = metadata

    def preprocess(self, val):
        pass

    def row(self, val):
        return (val,)

    def on_edit(self, col, item, proxy):
        pass

    def value(self, val):
        return None

class String(EditType):
    def on_edit(self, col, item, proxy):
        self.etv.inplace_entry(col, item)

    def value(self, val):
        return val

class Number(EditType):
    def on_edit(self, col, item, proxy):
        self.etv.inplace_spinbox(col, item, 0, 65536, 1)

    def value(self, val):
        return int(val)

class Object(EditType):
    def row(self, val):
        return ('',)

class Boolean(EditType):
    def on_edit(self, col, item, proxy):
        self.etv.inplace_checkbutton(col, item)

    def value(self, val):
        return True if val == 'True' else False

class List(EditType):
    def row(self, val):
        return ('',)

class Music(List):
    def preprocess(self, val):
        self.meta['key_name'] = 'category'
        for category in val:
            category['$songs'] = { 'key_name': 'name' }

class Rooms(List):
    def preprocess(self, val):
        self.meta['key_name'] = 'area'

class Mod(Object):
    def preprocess(self, val):
        if not isinstance(val, str):
            for mod in val:
                val[f'${mod}'] = 'modentry'

    def on_edit(self, col, item, proxy):
        meta = self.meta
        option = proxy.option
        if isinstance(option, str):
            # Old-style modpass. Ask if user wants to convert it to a
            # new-style pass.
            msg = _('You have an old-style modpass. Do you wish to convert ' \
                    'it to a multi-profile modpass?')
            if 'ignore_prompt' not in meta and \
                    tk.messagebox.askyesno(message=msg, icon='warning'):
                option = proxy.option = {
                    '$default': { 'type': 'modentry' },
                    'default': { 'password': option }
                }
                proxy.unpack_dict(option, item)
                values = self.etv.item(item, 'values')
                values = ('', *values[1:])
                self.etv.item(item, values=values)
            else:
                # Fine. Screw you then.
                meta['ignore_prompt'] = True
                self.etv.inplace_entry(col, item)
                return

        # Show a button.
        def add_mod_entry():
            msg = _('Enter the profile name of the mod:')
            profile = tk.simpledialog.askstring(_('New Mod'), msg)
            if profile is None:
                return
            profile = profile.strip()
            if profile == '':
                return

            modpass_list = proxy.option
            if profile in modpass_list:
                msg = _('That profile already exists.')
                tk.messagebox.showerror(_('New Mod'), msg)

            modpass_list[profile] = {
                'password': 'modpass'
            }
            proxy.unpack_dict({
                f'${profile}': { 'type': 'modentry' },
                profile: modpass_list[profile]
            }, item)

        self.etv.inplace_custom(col, item, ttk.Button(self.etv, text='+', command=add_mod_entry))
        self.etv.forceUpdateWnds()

    def row(self, val):
        if type(val) == str:
            return val

    def value(self, val):
        if type(val) == str:
            return val

class ModEntry(Object):
    def on_edit(self, col, item, proxy):
        def remove_mod_entry():
            profile = item.split('/')[-1]
            msg = _(f'Mod profile \'{profile}\' will be deleted.')
            if tk.messagebox.askokcancel('Delete Mod', msg):
                del proxy.option
                self.etv.delete(item)

        self.etv.inplace_custom(col, item, ttk.Button(self.etv, text='-', command=remove_mod_entry))
        self.etv.forceUpdateWnds()

class Multiline(EditType):
    def on_edit(self, col, item, proxy):
        def edit_multiline():
            option = proxy.option
            class MultilineDialog(tk.simpledialog.Dialog):
                def body(self, master):
                    self.text = tk.Text(master, width=50, height=12, wrap=tk.WORD)
                    self.text.grid(row=0)
                    self.text.insert(tk.END, option)
                    return self.text

                def apply(self):
                    self.result = self.text.get(1.0, tk.END)

            dialog = MultilineDialog(self.etv, title='Edit Multiline')
            if dialog.result is not None:
                option = proxy.option = dialog.result.strip()
                self.etv._inplace_vars[col].set(option)
                self.etv.item(item, values=(option,))

        self.etv.inplace_custom(col, item, ttk.Button(self.etv, text='...', command=edit_multiline))
