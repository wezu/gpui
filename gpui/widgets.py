import traceback
from panda3d.core import *

__all__=['Button', 'Dummy', 'Frame','MovableFrame', 'InputField',
 'MultilineInputField','ScrolledArea', 'Text','StaticText', 'Thumb', 'Slider']

class Widget:
    """Base class for most other widgets,
    This class implements:
    -creating geoms from a list of quads
    -set_pos, set_pos_delta that will also move child widgets
    -show/hide (not yet)
    -clip planes (not yet!)
    """
    def __init__(self, gui, name=None, parent=None, group=None, quads=[], pos=None, *args, **kwargs):
        self.gui=gui
        if name is None:
            name='widget_'+str(self.gui.next_id)
        self.name=name
        self.parent=parent
        self.children=[]
        self.id=self.gui.get_id(name)
        self.gui.elements[name]=self
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
        if parent in self.gui.elements:
            self.gui.elements[parent].children.append(name)
            self.set_pos(*self.gui.elements[parent].get_pos())
        if pos is not None:
            self.set_pos(*pos)
        #pass on init...
        super().__init__(*args, **kwargs)

    def set_pos(self, x,y):
        if self.parent in self.gui.elements:
            parent_pos=self.gui.elements[self.parent].get_pos()
            x+=parent_pos[0]
            y+=parent_pos[1]
        self.gui.set_pos_scale(id=self.id, x=x, y=y)
        delta=Vec2(x,y)-self.get_pos()
        for name in self.children:
            self.gui.elements[name].set_pos_delta(*delta)

    def get_pos(self):
        pos_scale=self.gui.get_pos_scale(self.id)
        return Vec2(pos_scale[0],pos_scale[1])

    def set_pos_delta(self, x=None, y=None):
        self.gui.set_delta_pos(id=self.id, x=x, y=y)
        for name in self.children:
            self.gui.elements[name].set_pos_delta(x, y)

    def hide(self):
        pass

    def show(self):
        pass

    def set_clip(self, top, bottom, left, right):
        pass

class Clickable:
    """This class implements the clickable interface,
    classes that inherit from it will exec the on_click_cmd string when clicked
    """
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
    """This class implements moving/dragging widgets with the mouse,
    classes the inherit from it can be moved with the mouse (hold and drag)
    x_limit and y_limit are the right-left or top-bottom limits in pixels
    eg. x_limit=(0, 128) will allow the widget to move up to 128 pixels right (from its initial pos)
    on_move_cmd will exec each frame
    if limits are set self.value can be used to get the current value in 0.0-1.0 scale or
    self.total_delta can be used to get the values in pixels
    """
    def __init__(self, x_limit=None, y_limit=None, on_move_cmd=None, *args, **kwargs ):
        #pass on init...
        super().__init__(*args, **kwargs)
        self.gui.hold_commands[self.id]=self.on_move
        self.x_limit=x_limit
        self.y_limit=y_limit
        self.x_range=1
        self.y_range=1
        if x_limit:
            self.x_range=max(1, x_limit[1]-x_limit[0])
        if y_limit:
            self.y_range=max(1, y_limit[1]-y_limit[0])
        self.total_delta=Vec2(0,0)
        self.on_move_cmd=on_move_cmd
        self.value=(0,0)

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
        if self.y_limit or self.x_limit:
            self.value=(self.total_delta[0]/self.x_range,
                   self.total_delta[1]/self.y_range)
        if self.on_move_cmd is not None:
            try:
                exec(self.on_move_cmd)
            except Exception as err:
                trbck=traceback.format_exception_only(err.__class__, err)[0]
                print('ERROR: Could not run command:\n{0}\n{1}'.format(self.on_move_cmd, trbck))
class Dummy:
    """A Dummy widget is a widget that has no visible elements"""
    def __init__(self, *, gui=None, parent=None, pos=None):
        self.gui=gui
        if name is None:
            name='widget_'+str(self.gui.next_id)
        self.name=name
        self.parent=parent
        self.children=[]
        self.id=self.gui.get_id(name)
        self.gui.elements[name]=self
        if parent in self.gui.elements:
            self.gui.elements[parent].children.append(name)
            self.set_pos(*self.gui.elements[parent].get_pos())
        self.pos=Vec2(*pos)

    def set_pos(self, x, y):
        if self.parent in self.gui.elements:
            parent_pos=self.gui.elements[self.parent].get_pos()
            x+=parent_pos[0]
            y+=parent_pos[1]
        delta=Vec2(x,y)-self.pos
        self.pos=Vec2(x,y)
        for name in self.children:
            self.gui.elements[name].set_pos_delta(*delta)

    def get_pos(self):
        return self.pos

    def set_pos_delta(self, x=0, y=0):
        self.pos+=Vec2(x,y)
        for name in self.children:
            self.gui.elements[name].set_pos_delta(x, y)

class StaticText:
    """StaticText is a type of text that can NOT be changed after creation (can only be moved, scaled,etc) """
    def __init__(self, *, gui=None, parent=None, name=None, txt='', font=None, text_scale=1.0, pos=None):
        pass

class Text:
    """This type of text can be changed.
    Uses TextNode internally.
    Each instance is a new geom so use wisely!
    """
    def __init__(self, *, gui=None, parent=None, name=None, txt='', font=None, text_scale=1.0, pos=None):
        pass

class ScrolledArea:
    """ """
    def __init__(self, *, gui=None, parent=None, name=None, size=(128, 128), inner_size=(128, 256), pos=None):
        pass

class ScrollBar:
    """ Scroll bar for ScrolledArea"""

class InputField:
    """A user input widget - I have no idea how to make it work """
    def __init__(self, *, gui=None, parent=None, name=None, width=32, txt='', font=None, text_scale=1.0, pos=None, on_submint_cmd=None):
        pass

class MultilineInputField:
    """A  multiline user input widget - I have no idea how to make it work """
    def __init__(self, *, gui=None, parent=None, name=None, size=(128, 128), txt='', font=None, text_scale=1.0, pos=None):
        pass

class Frame(Widget):
    """A non-interactive frame """
    def __init__(self, *, gui=None, parent=None, group=None, name=None, size=(128, 128), pos=None, **kwargs):
        quads=[]
        num_rows=size[0]//64
        num_columns=size[1]//64
        for row in range(num_rows):
            for column in range(num_columns):
                if row == 0 and column == 0: #top left
                    quads.append({'size':64, 'pos':(0,0), 'uv':(0.25, 0.875, 0.375, 1.0)})
                elif row == 0 and column == (num_columns-1):  #top right
                    quads.append({'size':64, 'pos':(64*column,0), 'uv':(0.375, 0.875, 0.25, 1.0)})
                elif row == (num_rows-1) and column == 0:  #bottom left
                    quads.append({'size':64, 'pos':(0,64*row), 'uv':(0.25, 1.0, 0.375, 0.875)})
                elif row == (num_rows-1) and column == (num_columns -1):  #bottom right
                    quads.append({'size':64, 'pos':(64*column,64*row), 'uv':(0.375, 1.0, 0.25, 0.875)})
                elif row == 0: #top
                    quads.append({'size':64, 'pos':(64*column,64*row), 'uv':(0.375, 0.875, 0.5, 1.0)})
                elif row == (num_rows-1): #bottom
                    quads.append({'size':64, 'pos':(64*column,64*row), 'uv':(0.375, 1.0, 0.5, 0.875)})
                elif column == 0: #left
                    quads.append({'size':64, 'pos':(64*column,64*row), 'uv':(0.25, 0.75, 0.375, 0.875)})
                elif column == (num_columns -1): #right
                    quads.append({'size':64, 'pos':(64*column,64*row), 'uv':(0.375, 0.75, 0.25, 0.875)})
                else:
                    quads.append({'size':64, 'pos':(64*column,64*row), 'uv':(0.375, 0.75, 0.5, 0.875)})

        #init base class
        super().__init__(gui=gui, name=name, parent=parent, group=group, pos=pos, quads=quads, **kwargs)

class MovableFrame(Frame, Movable):
    """A frame that can be moved with the mouse """
    def __init__(self, *, gui=None, parent=None, group=None, name=None, size=(128, 128), pos=None, **kwargs):
        super().__init__(gui=gui, parent=parent, group=group, name=name, size=size, pos=pos,**kwargs)

class Slider:
    """Horizontal slider """
    def __init__(self, *, gui=None, parent=None, group=None, name=None, width=64, pos=None, on_move_cmd=None):
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
        self.rail=Widget(gui=gui, name=name+'_rail', parent=name, group=group, pos=pos, quads=quads)
        self.thumb=Thumb(gui=gui,
                         x_limit=(0, width),
                         y_limit=(0,0),
                         name=name+'_thumb',
                         parent=name,
                         group=group,
                         pos=pos,
                         on_move_cmd=on_move_cmd)

class Thumb(Widget, Movable):
    """Thumb for sliders and scroll bars """
    def __init__(self, *, gui, x_limit=None, y_limit=None, name=None, parent=None, group=None, pos=None, on_move_cmd=None):
        quads=[{'size':32, 'pos':(0,0), 'uv':(0.125, 0.9375,  0.1875, 1.0), 'hover_uv':(0, 0.0625), 'click_uv':(0, 0.125)}]
        super().__init__(gui=gui, name=name, parent=parent, group=group, quads=quads, pos=pos, x_limit=x_limit, y_limit=y_limit, on_move_cmd=on_move_cmd)

class Button(Widget, Clickable):
    """ A button, will exec on_click_cmd when clicked"""
    def __init__(self, *, gui, width=32, pos=None, txt=None, txt_props=None,
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
        super().__init__(gui=gui, name=name, parent=parent, group=group, quads=quads, pos=pos, on_click_cmd=on_click_cmd)

