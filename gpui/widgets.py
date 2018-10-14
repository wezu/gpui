import traceback
from panda3d.core import *

__all__=['Button', 'Thumb', 'Slider']

class Widget:
    def __init__(self, gui, name=None, parent=None, group=None, quads=[], *args, **kwargs):
        self.gui=gui
        if name is None:
            name='widget_'+str(self.gui.next_id)
        self.name=name
        self.parent=parent
        self.children=[]
        self.id=self.gui.get_id(name)
        self.clip=False
        if group is None:
            if self.gui.groups:
                group_name=None
                for name in self.gui.groups:
                    if name not in self.gui.nodes:
                        group_name=name
                        break
                if group_name:
                    group=group_name
                else:
                    group_name = 'group_0'
                    i=0
                    while group_name in self.gui.groups:
                        i+=1
                        group_name = 'group_'+str(i)
                    self.gui.make_group(group_name)
                    group=group_name
            else:
                self.gui.make_group('group_0')
                group= 'group_0'
        elif group not in self.gui.groups:
            self.gui.make_group(group)
        for quad in quads:
            self.gui.add_quad(group_name=group, id=self.id, **quad)
        #pass on init...
        super().__init__(*args, **kwargs)

    def set_pos(self, x,y):
        self.gui.set_pos_scale(id=self.id, x=x, y=y)

    def set_pos_delta(self, x=None, y=None):
        self.gui.set_delta_pos(id=self.id, x=x, y=y)

    def set_scale(self, sx,sy):
        pass

    def set_pos_acale(self, x,y, sx, sy):
        pass

    def hide(self):
        pass

    def show(self):
        pass

    def set_clip(self, top, bottom, left, right):
        pass

class Clickable:
    def __init__(self, on_click_cmd=None, *args, **kwargs ):
        #pass on init...
        super().__init__(*args, **kwargs)
        self.on_click_cmd=on_click_cmd
        self.gui.click_commands[self.id]=self.on_click

    def on_click(self):
        try:
            exec(self.on_click_cmd)
        except Exception as err:
            trbck=traceback.format_exception_only(err.__class__, err)[0]
            print('ERROR: Could not run command:\n{0}\n{1}'.format(self.on_click_cmd, trbck))

class Movable:
    def __init__(self, x_limit=None, y_limit=None, on_move_cmd=None, *args, **kwargs ):
        #pass on init...
        super().__init__(*args, **kwargs)
        self.gui.hold_commands[self.id]=self.on_move
        self.x_limit=x_limit
        self.y_limit=y_limit
        self.total_delta=Vec2(0,0)
        self.on_move_cmd=on_move_cmd

    def on_move(self, delta):
        delta.x=int(round(delta.x))
        delta.y=int(round(delta.y))
        total_delta=self.total_delta+delta
        if self.x_limit is not None:
            if total_delta.x < self.x_limit[0] or total_delta.x > self.x_limit[1]:
                delta.x=0
        if self.y_limit is not None:
            if total_delta.y < self.y_limit[0] or total_delta.y > self.y_limit[1]:
                delta.y=0

        self.total_delta+=delta
        self.set_pos_delta(*delta)
        if self.on_move_cmd is not None:
            try:
                exec(self.on_move_cmd)
            except Exception as err:
                trbck=traceback.format_exception_only(err.__class__, err)[0]
                print('ERROR: Could not run command:\n{0}\n{1}'.format(self.on_move_cmd, trbck))

class Slider:
    def __init__(self, gui, parent, group, name, width, on_move_cmd=None):
        #rail
        #left end cap
        quads=[{'size':32, 'pos':(0,0), 'uv':(0.125, 0.75,  0.1875, 0.8125)}]
        end_cap_offset=32
        if width > 32:
            for i in range((width-32)//32):
                quads.append({'size':32, 'pos':(32+i*32,0), 'uv':(0.1875, 0.75,  0.25, 0.8125)})
                end_cap_offset+=32
        #right end cap
        quads.append({'size':32, 'pos':(end_cap_offset,0), 'uv':(0.1875, 0.75,  0.125, 0.8125)})
        self.rail=Widget(gui=gui, name=name+'_rail', parent=name, group=group, quads=quads)
        self.thumb=Thumb(gui=gui,
                         x_limit=(0, width),
                         y_limit=(0,0),
                         name=name+'_thumb',
                         parent=name,
                         group=group,
                         on_move_cmd=on_move_cmd)

class Thumb(Widget, Movable):
    def __init__(self, *, gui, x_limit=None, y_limit=None, name=None, parent=None, group=None, on_move_cmd=None):
        quads=[{'size':32, 'pos':(0,0), 'uv':(0.125, 0.9375,  0.1875, 1.0), 'hover_uv':(0, 0.0625), 'click_uv':(0, 0.125)}]
        super().__init__(gui=gui, name=name, parent=parent, group=group, quads=quads, x_limit=x_limit, y_limit=y_limit, on_move_cmd=on_move_cmd)

class Button(Widget, Clickable):
    def __init__(self, *, gui, width=32, txt=None, txt_props=None,
                 name=None, parent=None, group=None, on_click_cmd=None):
        #left end cap
        quads=[{'size':32, 'pos':(0,0), 'uv':(0, 0.9375,  0.0625, 1.0), 'hover_uv':(0, 0.0625), 'click_uv':(0, 0.125)}]
        end_cap_offset=32
        if width > 32:
            for i in range((width-32)//32):
                quads.append({'size':32, 'pos':(32+i*32,0), 'uv':(0.0625, 0.9375,  0.125, 1.0), 'hover_uv':(0, 0.0625), 'click_uv':(0, 0.125)})
                end_cap_offset+=32
        #right end cap
        quads.append({'size':32, 'pos':(end_cap_offset,0), 'uv':(0.0625, 0.9375,  0.0, 1.0), 'hover_uv':(0, 0.0625), 'click_uv':(0, 0.125)})
        #init base class
        super().__init__(gui=gui, name=name, parent=parent, group=group, quads=quads, on_click_cmd=on_click_cmd)

