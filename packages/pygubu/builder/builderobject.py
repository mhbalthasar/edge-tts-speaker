# encoding: utf8
from __future__ import unicode_literals

import itertools
import json
import logging
from collections import defaultdict, namedtuple

try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk

__all__ = [
    'BuilderObject', 'EntryBaseBO', 'PanedWindowBO',
    'PanedWindowPaneBO', 'WidgetDescription', 'CLASS_MAP', 'CB_TYPES',
    'CUSTOM_PROPERTIES', 'register_widget', 'register_property',
    'register_custom_property'
]

logger = logging.getLogger(__name__)

#
# Utility functions
#
zip_longest = getattr(itertools, 'zip_longest', None)
if zip_longest is None:
    def zip_longest(*args, **kw):
        # zip_longest('ABCD', 'xy', fillvalue='-') --> Ax By C- D-
        fillvalue = kw.get('fillvalue', None)
        iterators = [iter(it) for it in args]
        num_active = len(iterators)
        if not num_active:
            return
        while True:
            values = []
            for i, it in enumerate(iterators):
                try:
                    value = next(it)
                except StopIteration:
                    num_active -= 1
                    if not num_active:
                        return
                    iterators[i] = itertools.repeat(fillvalue)
                    value = fillvalue
                values.append(value)
            yield tuple(values)
    itertools.zip_longest = zip_longest


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


# Python 2 issue:
try:
    isinstance(basestring, type)
except BaseException:
    basestring = str

#
# BuilderObject
#

WidgetDescription = namedtuple('WidgetDescription',
                               ['classname', 'builder', 'label', 'tags'])

CLASS_MAP = {}


def register_widget(classname, builder, label=None, tags=None):
    if label is None:
        label = classname
    if tags is None:
        tags = tuple()

    CLASS_MAP[classname] = WidgetDescription(classname, builder, label, tags)


CUSTOM_PROPERTIES = {}


def register_property(name, description):
    if name in CUSTOM_PROPERTIES:
        CUSTOM_PROPERTIES[name].update(description)
        logger.debug('Updating registered property %s', name)
    else:
        CUSTOM_PROPERTIES[name] = description
        logger.debug('Registered property %s', name)


def register_custom_property(
        builder_uid, prop_name,
        editor, default_value=None, help=None,
        **editor_params):
    '''Helper function to register a custom property.
    All custom properties are created using internal dynamic editor.
    '''
    description = {
        'editor': 'dynamic',
        builder_uid: {
            'params': {
                'mode': editor,
            }
        }
    }
    description[builder_uid]['params'].update(editor_params)
    if default_value is not None:
        description[builder_uid]['default'] = default_value
    if help is not None:
        description[builder_uid]['help'] = help
    register_property(prop_name, description)


class CB_TYPES:
    '''Callback types'''
    SIMPLE = 'simple'
    WITH_WID = 'with_wid'
    ENTRY_VALIDATE = 'entry_validate'
    SCROLL = 'scroll'
    SCROLLSET = 'scrollset'
    SCALE = 'scale'
    BIND_EVENT = 'bind_event'

#
# Base class
#


class BuilderObject(object):
    """Base class for Widgets created with Builder"""

    OPTIONS_STANDARD = tuple()
    OPTIONS_SPECIFIC = tuple()
    OPTIONS_CUSTOM = tuple()
    class_ = None
    container = False
    allowed_parents = None
    allowed_children = None
    maxchildren = None
    properties = tuple()
    ro_properties = tuple()
    layout_required = True
    command_properties = tuple()
    allow_bindings = True
    tkvar_properties = ('listvariable', 'textvariable', 'variable')
    tkimage_properties = ('image', 'selectimage', 'iconphoto')
    tkfont_properties = ('font',)
    virtual_events = tuple()

    @classmethod
    def factory(cls, builder, wdata):
        clsobj = cls(builder, wdata)
        wdata.layout_required = clsobj.layout_required
        return clsobj

    @classmethod
    def add_allowed_parent(cls, builder_uid):
        if cls.allowed_parents is None:
            cls.allowed_parents = (builder_uid,)
        else:
            cls.allowed_parents = cls.allowed_parents + (builder_uid,)

    @classmethod
    def add_allowed_child(cls, builder_uid):
        if cls.allowed_children is None:
            cls.allowed_children = (builder_uid,)
        else:
            cls.allowed_children = cls.allowed_children + (builder_uid,)

    def __init__(self, builder, wmeta):
        super(BuilderObject, self).__init__()
        self.widget = None
        self.builder = builder
        self.wmeta = wmeta
        self._code_identifier = None

    def realize(self, parent):
        args = self._get_init_args()
        master = parent.get_child_master()
        self.widget = self.class_(master, **args)
        return self.widget

    def _get_init_args(self):
        """Creates dict with properties marked as readonly"""

        args = {}
        for rop in self.ro_properties:
            if rop in self.wmeta.properties:
                pvalue = self._process_property_value(
                    rop, self.wmeta.properties[rop])
                args[rop] = pvalue
        return args

    def configure(self, target=None):
        if target is None:
            target = self.widget
        for pname, value in self.wmeta.properties.items():
            if (pname not in self.ro_properties
                    and pname not in self.command_properties):
                self._set_property(target, pname, value)

    def _process_property_value(self, pname, value):
        propvalue = value
        if pname in self.tkvar_properties:
            propvalue = self.builder.create_variable(value)
            if 'text' in self.wmeta.properties and pname == 'textvariable':
                propvalue.set(self.wmeta.properties['text'])
            elif 'value' in self.wmeta.properties and pname == 'variable':
                propvalue.set(self.wmeta.properties['value'])
        elif pname in self.tkimage_properties:
            propvalue = self.builder.get_image(value)
        elif pname == 'takefocus':
            if value:
                propvalue = tk.getboolean(value)
        return propvalue

    def _set_property(self, target_widget, pname, value):
        if pname not in self.__class__.properties:
            msg = "Attempt to set an unknown property '%s' on class '%s'"
            logger.warning(msg, pname, repr(self.class_))
        else:
            propvalue = self._process_property_value(pname, value)
            try:
                logger.debug('setting property %s = %s', pname, propvalue)
                target_widget[pname] = propvalue
            except tk.TclError as e:
                msg = "Failed to set property '%s' on class '%s'. TclError: %s"
                logger.error(msg, pname, repr(self.class_), str(e))
                # logger.exception(e)

    def layout(self, target=None, configure_gridrc=True):
        if self.layout_required:
            if target is None:
                target = self.widget

            # Check manager
            manager = self.wmeta.manager
            logger.debug(
                'Applying %s layout to %s',
                manager,
                self.wmeta.identifier)
            if manager == 'grid':
                self._grid_layout(target)
            elif manager == 'pack':
                self._pack_layout(target)
            elif manager == 'place':
                self._place_layout(target)
            else:
                msg = 'Invalid layout manager: {0}'.format(manager)
                raise Exception(msg)
        if configure_gridrc:
            logger.debug('Configurying grid-rc')
            parent = target.nametowidget(target.winfo_parent())
            self._gridrc_config(parent)

    def _pack_layout(self, target):
        properties = dict(self.wmeta.layout_properties)
        propagate = properties.pop('propagate', 'true')
        # Do pack
        target.pack(**properties)
        if propagate.lower() != 'true':
            target.pack_propagate(0)

    def _place_layout(self, target):
        # Do place
        target.place(**self.wmeta.layout_properties)

    def _grid_layout(self, target):
        properties = dict(self.wmeta.layout_properties)
        propagate = properties.pop('propagate', 'true')
        propagate = propagate.lower()
        target.grid(**properties)
        if propagate != 'true':
            target.grid_propagate(0)

    def _gridrc_config(self, target):
        # configure grid row/col properties:
        for type_, num, pname, value in self.wmeta.gridrc_properties:
            if type_ == 'row':
                target.rowconfigure(num, **{pname: value})
            else:
                target.columnconfigure(num, **{pname: value})

    def get_child_master(self):
        return self.widget

    def add_child(self, bobject):
        pass

    def _create_callback(self, cmd, command):
        callback = command
        cmd_type = cmd['cbtype']
        if cmd_type == CB_TYPES.WITH_WID:
            def widget_callback(button_id=self.wmeta.identifier):
                command(button_id)
            callback = widget_callback
        if cmd_type == CB_TYPES.ENTRY_VALIDATE:
            args = cmd['args']
            if args:
                args = args.split(' ')
                callback = (self.widget.register(command),) + tuple(args)
            else:
                callback = self.widget.register(command)
        return callback

    def _connect_command(self, cmd_pname, callback):
        prop = {cmd_pname: callback}
        self.widget.configure(**prop)

    def connect_commands(self, cmd_bag):
        notconnected = []
        commands = {}
        for cmd_pname in self.command_properties:
            cmd = self.wmeta.properties.get(cmd_pname, None)
            if cmd is not None:
                cmd = json.loads(cmd)
                cmd_name = (cmd['value']).strip()
                if cmd_name:
                    commands[cmd_pname] = cmd
                else:
                    msg = "%s: invalid value for property '%s'."
                    logger.warning(msg, self.wmeta.identifier, cmd_pname)

        if isinstance(cmd_bag, dict):
            for cmd_pname, cmd in commands.items():
                cmd_name = cmd['value']
                if cmd_name in cmd_bag:
                    callback = self._create_callback(cmd, cmd_bag[cmd_name])
                    self._connect_command(cmd_pname, callback)
                else:
                    notconnected.append(cmd_name)
        else:
            for cmd_pname, cmd in commands.items():
                cmd_name = cmd['value']
                if hasattr(cmd_bag, cmd_name):
                    callback = self._create_callback(
                        cmd, getattr(cmd_bag, cmd_name))
                    self._connect_command(cmd_pname, callback)
                else:
                    notconnected.append(cmd_name)
        if notconnected:
            return notconnected
        else:
            return None

    def connect_bindings(self, cb_bag):
        notconnected = []

        if isinstance(cb_bag, dict):
            for bind in self.wmeta.bindings:
                cb_name = bind.handler
                if cb_name in cb_bag:
                    callback = cb_bag[cb_name]
                    self.widget.bind(bind.sequence, callback, add=bind.add)
                else:
                    notconnected.append(cb_name)
        else:
            for bind in self.wmeta.bindings:
                cb_name = bind.handler
                if hasattr(cb_bag, cb_name):
                    callback = getattr(cb_bag, cb_name)
                    self.widget.bind(bind.sequence, callback, add=bind.add)
                else:
                    notconnected.append(cb_name)
        if notconnected:
            return notconnected
        else:
            return None

    #
    # Code generation methods
    #
    def _code_get_init_args(self, code_identifier):
        """Creates dict with properties marked as readonly"""
        args = {}
        for rop in self.ro_properties:
            if rop in self.wmeta.properties:
                pvalue = self._code_process_property_value(
                    code_identifier, rop, self.wmeta.properties[rop])
                args[rop] = pvalue
        return args

    def code_realize(self, boparent, code_identifier=None):
        if code_identifier is not None:
            self._code_identifier = code_identifier
        lines = []
        master = boparent.code_child_master()
        init_args = self._code_get_init_args(self.code_identifier())
        bag = []
        for pname, value in init_args.items():
            s = "{0}={1}".format(pname, value)
            bag.append(s)
        kwargs = ''
        if bag:
            kwargs = ', {0}'.format(', '.join(bag))
        s = "{0} = {1}({2}{3})".format(self.code_identifier(),
                                       self._code_class_name(), master, kwargs)
        lines.append(s)
        return lines

    def code_identifier(self):
        if self._code_identifier is None:
            return self.wmeta.identifier
        return self._code_identifier

    def code_child_master(self):
        return self.code_identifier()

    def code_child_add(self, childid):
        return []

    def code_configure(self, targetid=None):
        if targetid is None:
            targetid = self.code_identifier()
        code_bag, kwproperties, complex_properties = \
            self._code_process_properties(self.wmeta.properties, targetid)
        lines = []
        prop_stmt = "{0}.configure({1})"
        arg_stmt = "{0}={1}"
        for g in grouper(sorted(kwproperties), 4):
            args_bag = []
            for p in g:
                if p is not None:
                    args_bag.append(arg_stmt.format(p, code_bag[p]))
            args = ', '.join(args_bag)
            line = prop_stmt.format(targetid, args)
            lines.append(line)
        for pname in complex_properties:
            lines.extend(code_bag[pname])

        return lines

    def code_layout(self, targetid=None, parentid=None):
        if targetid is None:
            targetid = self.code_identifier()
        if parentid is None:
            parentid = targetid
        if self.layout_required:
            lines = []
            layout_stmt = "{0}.{1}({2})"
            arg_stmt = "{0}='{1}'"
            layout = self.wmeta.layout_properties
            args_bag = []
            for p, v in sorted(layout.items()):
                if p not in ('propagate', ):
                    args_bag.append(arg_stmt.format(p, v))
            args = ', '.join(args_bag)

            manager = self.wmeta.manager
            line = layout_stmt.format(targetid, manager, args)
            lines.append(line)

            pvalue = str(layout.get('propagate', '')).lower()
            if 'propagate' in layout and pvalue == 'false':
                line = '{0}.{1}_propagate({2})'
                line = line.format(targetid, manager, 0)
                lines.append(line)

            lrow_stmt = "{0}.rowconfigure('{1}', {2})"
            lcol_stmt = "{0}.columnconfigure('{1}', {2})"
            rowbag = defaultdict(list)
            colbag = defaultdict(list)
            for type_, num, pname, value in self.wmeta.gridrc_properties:
                arg = "{0}='{1}'".format(pname, value)
                if type_ == 'row':
                    rowbag[num].append(arg)
                else:
                    colbag[num].append(arg)
            for k, bag in rowbag.items():
                args = ', '.join(bag)
                line = lrow_stmt.format(parentid, k, args)
                lines.append(line)
            for k, bag in colbag.items():
                args = ', '.join(bag)
                line = lcol_stmt.format(parentid, k, args)
                lines.append(line)
            return lines
        else:
            return []

    def _code_class_name(self):
        cname = None
        # try here ?
        cname = self.builder.code_classname_for(self)
        if cname is None:
            if self.class_ is not None:
                prefix = self.class_.__module__
                name = self.class_.__name__
                cname = '{0}.{1}'.format(prefix, name)
            else:
                cname = 'ClassNameNotDefined'
        return cname

    def _code_process_properties(self, properties, targetid):
        code_bag = {}
        for pname, value in properties.items():
            if (pname not in self.ro_properties
                    and pname not in self.command_properties):
                self._code_set_property(targetid, pname, value, code_bag)

        # properties
        # determine kw properties or complex properties
        kwproperties = []
        complex_properties = []
        for pname, value in code_bag.items():
            if isinstance(value, str) or isinstance(value, basestring):
                kwproperties.append(pname)
            else:
                complex_properties.append(pname)

        return (code_bag, kwproperties, complex_properties)

    def _code_process_property_value(self, targetid, pname, value):
        propvalue = "'{}'".format(value)
        if pname in self.tkvar_properties:
            propvalue = self._code_set_tkvariable_property(pname, value)
        elif pname in self.command_properties:
            cmd = json.loads(value)
            propvalue = self._code_define_callback(pname, cmd)
        elif pname in self.tkimage_properties:
            propvalue = self.builder.code_create_image(value)
        elif pname == 'takefocus':
            propvalue = str(tk.getboolean(value))
        return propvalue

    def _code_set_property(self, targetid, pname, value, code_bag):
        code_bag[pname] = self._code_process_property_value(
            targetid, pname, value)

    def _code_set_tkvariable_property(self, pname, value):
        '''Create code for tk variable property.
        Can be used from subclases for custom tk variable properties.'''
        varvalue = None
        if 'text' in self.wmeta.properties and pname == 'textvariable':
            varvalue = self.wmeta.properties['text']
        elif 'value' in self.wmeta.properties and pname == 'variable':
            varvalue = self.wmeta.properties['value']
        propvalue = self.builder.code_create_variable(value, varvalue)
        return propvalue

    def code_connect_commands(self):
        commands = {}
        for cmd_pname in self.command_properties:
            cmd = self.wmeta.properties.get(cmd_pname, None)
            if cmd is not None:
                #print('on_code_connect_commands', cmd)
                cmd = json.loads(cmd)
                cmd_name = (cmd['value']).strip()
                if cmd_name:
                    commands[cmd_pname] = cmd
                else:
                    msg = "%s: invalid callback name for property '%s'."
                    logger.warning(msg, self.wmeta.identifier, cmd_pname)
        lines = []
        for cmd_pname, cmd in commands.items():
            callback = self._code_define_callback(cmd_pname, cmd)
            cmd_code = self._code_connect_command(cmd_pname, cmd, callback)
            if cmd_code:
                lines.extend(cmd_code)
        return lines

    def _code_define_callback_args(self, cmd_pname, cmd):
        cmdtype = cmd['cbtype']
        args = None
        if cmdtype == CB_TYPES.WITH_WID:
            args = ('widget_id', )
        if cmdtype == CB_TYPES.SCALE:
            args = ('scale_value', )
        if cmdtype == CB_TYPES.SCROLLSET:
            args = ('first', 'last')
        if cmdtype == CB_TYPES.SCROLL:
            args = ('mode', 'value', 'units')
        if cmdtype == CB_TYPES.ENTRY_VALIDATE:
            cb_args = cmd['args']
            if cb_args:
                cb_args = cb_args.replace('%', '')
                args = cb_args.split()
        return args

    def _code_define_callback(self, cmd_pname, cmd):
        cmdname = cmd['value']
        cmdtype = cmd['cbtype']
        args = self._code_define_callback_args(cmd_pname, cmd)
        wid = self.code_identifier()
        return self.builder.code_create_callback(wid, cmdname, cmdtype, args)

    def _code_connect_command(self, cmd_pname, cmd, cbname):
        target = self.code_identifier()
        args = self._code_define_callback_args(cmd_pname, cmd)
        lines = []
        cmdtype = cmd['cbtype']
        if args is not None:
            if cmdtype == CB_TYPES.WITH_WID:
                wid = self.wmeta.identifier
                fdef = "_wcmd = lambda wid='{0}': {1}(wid)".format(
                    wid, cbname)
                cbname = '_wcmd'
                lines.append(fdef)
            if cmdtype == CB_TYPES.ENTRY_VALIDATE:
                original_cb = cbname
                tk_args = ["'%{0}'".format(a) for a in args]
                tk_args = ','.join(tk_args)
                fdef = "_validatecmd = ({0}.register({1}), {2})"
                fdef = fdef.format(target, original_cb, tk_args)
                cbname = '_validatecmd'
                lines.append(fdef)
        line = '{0}.configure({1}={2})'.format(target, cmd_pname, cbname)
        lines.append(line)
        return lines

    def code_connect_bindings(self):
        lines = []
        target = self.code_identifier()
        for bind in self.wmeta.bindings:
            cb_name = self.builder.code_create_callback(
                target, bind.handler, CB_TYPES.BIND_EVENT)
            add_arg = '+' if bind.add else ''
            line = "{0}.bind('{1}', {2}, add='{3}')"
            line = line.format(target, bind.sequence, cb_name, add_arg)
            lines.append(line)
        return lines


#
# Base clases for some widgets
#
class EntryBaseBO(BuilderObject):
    """Base class for tk.Entry and ttk.Entry builder objects"""

    def _set_property(self, target_widget, pname, value):
        if pname == 'text':
            wstate = str(target_widget['state'])
            if wstate != 'normal':
                # change state temporarily
                target_widget['state'] = 'normal'
            target_widget.delete('0', tk.END)
            target_widget.insert('0', value)
            target_widget['state'] = wstate
        else:
            super(EntryBaseBO, self)._set_property(
                target_widget, pname, value)

    #
    # Code generation methods
    #
    def _code_set_property(self, targetid, pname, value, code_bag):
        if pname == 'text':
            lines = [
                "_text_ = '''{0}'''".format(value),
                "{0}.delete('0', 'end')".format(targetid),
                "{0}.insert('0', _text_)".format(targetid),
            ]
            if 'state' in self.wmeta.properties:
                state_value = self.wmeta.properties['state']
                if state_value != 'normal':
                    line = "{0}['state'] = 'normal'".format(targetid)
                    lines.insert(1, line)
                    line = "{0}['state'] = '{1}'".format(
                        targetid, state_value)
                    lines.append(line)
            code_bag[pname] = lines
        else:
            super(EntryBaseBO, self)._code_set_property(targetid, pname,
                                                        value, code_bag)


class PanedWindowBO(BuilderObject):
    """Base class for tk.PanedWindow and ttk.Panedwindow builder objects"""
    class_ = None
    container = True
    properties = []
    ro_properties = ('orient', )

    def realize(self, parent):
        master = parent.get_child_master()
        args = self._get_init_args()
        if 'orient' not in args:
            args['orient'] = 'vertical'
        self.widget = self.class_(master, **args)
        return self.widget


#
# Base clases for some widget Helpers
#
class PanedWindowPaneBO(BuilderObject):
    class_ = None
    container = True
    properties = []
    layout_required = False
    allow_bindings = False

    def realize(self, parent):
        self.widget = parent.get_child_master()
        return self.widget

    def configure(self):
        pass

    def layout(self):
        pass

    def add_child(self, bobject):
        self.widget.add(bobject.widget, **self.wmeta.properties)

    #
    # code generation functions
    #
    def code_realize(self, boparent, code_identifier=None):
        self._code_identifier = boparent.code_child_master()
        return tuple()

    def code_configure(self, targetid=None):
        return tuple()

    def code_layout(self, targetid=None, parentid=None):
        return tuple()

    def code_child_add(self, childid):
        config = []
        masterid = self.code_child_master()
        for pname, val in self.wmeta.properties.items():
            line = "{}='{}'".format(pname, val)
            config.append(line)
        kw = ''
        lines = []
        if config:
            kw = ', {0}'.format(', '.join(config))
        line = '{0}.add({1}{2})'.format(masterid, childid, kw)
        lines.append(line)
        return lines
