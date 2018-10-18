from panda3d.core import *
from direct.showbase.DirectObject import DirectObject
load_prc_file_data("", "sync-video 0")
load_prc_file_data("", "show-frame-rate-meter  1")
from direct.showbase import ShowBase

from direct.gui.DirectGui import *


class App(DirectObject):
    def __init__(self):
        base = ShowBase.ShowBase()
        #stress test
        for x in range(32):
            for y in range(32):
                DirectButton(
                            frameSize=(32, 0, 0, -32),
                            pos=(x*32, 0, -y*32),
                            scale=32,
                            command=self.print_id,
                            extraArgs=[x, y],
                            parent=pixel2d
                            )
    def print_id(self, x, y):
        print("button id:{0}{1} clicked!".format(x, y))
#Run it
app=App()
base.run()
