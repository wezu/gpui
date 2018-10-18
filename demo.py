from panda3d.core import *
from direct.showbase.DirectObject import DirectObject
load_prc_file_data("", "sync-video 0")
load_prc_file_data("", "show-frame-rate-meter  1")
load_prc_file_data('','textures-power-2 None')
load_prc_file_data("", "show-buffers 1")
load_prc_file_data("", "gl-version 3 2")
from direct.showbase import ShowBase

from gpui import *

class App(DirectObject):
    def __init__(self):
        base = ShowBase.ShowBase()

        self.gui=Gui()
        #debug
        self.accept('tab', base.bufferViewer.toggleEnable)

        #make some sample data
        self.gui.make_group('test')

        b=Button(gui=self.gui, width=128, group='test', on_click_cmd='print("button id:{0} clicked!".format(self.id))')
        b.set_pos(0, 32)

        s=Slider(gui=self.gui, parent=None, group='test', name='slider', width=128, pos=(0, 128), on_move_cmd='print("slider value: {0:.2f}".format(*self.value))')

        f=MovableFrame(gui=self.gui, parent=None, group='test', name='frame', size=(256,256))
        f.set_pos(200, 0)

        b2=Button(gui=self.gui, width=128, group='test', parent='frame', pos=(0, 32), on_click_cmd='print("button id:{0} clicked!".format(self.id))')


        self.gui.close_group('test')


#Run it
app=App()
base.run()
