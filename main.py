from panda3d.core import *
from direct.showbase.DirectObject import DirectObject
load_prc_file_data("", "sync-video 0")
load_prc_file_data("", "show-frame-rate-meter  1")
load_prc_file_data('','textures-power-2 None')
load_prc_file_data("", "show-buffers 1")
load_prc_file_data("", "gl-version 3 2")
load_prc_file_data("", "buffer-viewer-position ulcorner")
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

        b=Button(gui=self.gui, width=128, group='test', on_click_cmd='print("button id:{0} clicked!".format(self.id))')#, name='test1', parent=None, group='group_0', on_click_cmd=None)
        b.set_pos(0, 32)
        s=Slider(gui=self.gui, parent=None, group='test', name='slider', width=128, on_move_cmd='print("slider pos:({0:.0f}, {1:.0f})".format(*self.total_delta))')

        self.gui.close_group('test')


#Run it
app=App()
base.run()
