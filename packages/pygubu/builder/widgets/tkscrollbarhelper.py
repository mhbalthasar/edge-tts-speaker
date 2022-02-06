# encoding: utf8

from __future__ import unicode_literals

try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk

from pygubu.builder.builderobject import *
from pygubu.widgets.tkscrollbarhelper import TkScrollbarHelper


class TKSBHelperBO(BuilderObject):
    class_ = TkScrollbarHelper
    container = True
    maxchildren = 1
    allowed_children = ('tk.Entry', 'ttk.Entry', 'tk.Text', 'tk.Canvas',
                        'tk.Listbox', 'ttk.Treeview')
    OPTIONS_STANDARD = ('borderwidth', 'cursor', 'highlightbackground',
                        'highlightcolor', 'highlightthickness',
                        'padx', 'pady', 'relief', 'takefocus')
    OPTIONS_SPECIFIC = ('background', 'class_', 'container',
                        'height', 'width')
    OPTIONS_CUSTOM = ('scrolltype', 'usemousewheel')
    properties = OPTIONS_STANDARD + OPTIONS_SPECIFIC + OPTIONS_CUSTOM
    ro_properties = ('class_', 'scrolltype')
    allow_bindings = False

    def get_child_master(self):
        return self.widget.container

    def add_child(self, bobject):
        cwidget = bobject.widget
        self.widget.add_child(cwidget)

    #
    # Code generation methods
    #
    def code_child_master(self):
        return '{0}.container'.format(self.code_identifier())

    def code_child_add(self, childid):
        lines = []
        line = '{0}.add_child({1})'.format(self.code_identifier(), childid)
        lines.append(line)
        return lines

    def _code_set_property(self, targetid, pname, value, code_bag):
        if pname == 'usemousewheel':
            code_bag[pname] = '{0}'.format(tk.getboolean(value))
        else:
            super(
                TKSBHelperBO,
                self)._code_set_property(
                targetid,
                pname,
                value,
                code_bag)


register_widget('pygubu.builder.widgets.tkscrollbarhelper', TKSBHelperBO,
                'ScrollbarHelper', ('Pygubu Helpers', 'tk'))
