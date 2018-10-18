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
        #stress test, make 1000 buttons - may not fit screen
        for x in range(50):
            for y in range(20):
                Button(gui=self.gui, width=32, group='test', pos=(-16+x*32, y*32), on_click_cmd='print("button id:{0} clicked!".format(self.id))')

        self.gui.close_group('test')


#Run it
app=App()
base.run()
