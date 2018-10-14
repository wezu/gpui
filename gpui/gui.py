from collections import namedtuple
from panda3d.core import *
from direct.showbase.DirectObject import DirectObject

from .widgets import *
from . import shaders

__all__=['Gui']

GeomData = namedtuple('GeomData', 'vdata, vertex, texcoord, offset_uv, color_id')

class Gui(DirectObject):
    def __init__(self, texture_atlas='tex/ui_atlas.png'):
        #vars
        self.mouse_is_down=False
        self.last_mouse_down_id=None
        self.last_frame_mouse_is_down=False
        self.last_frame_mouse_pos=Vec2(0)
        self.update_pos_scale=False
        self.update_clips=False
        self.element_id={}
        self.elements={}
        self.nodes={}
        self.groups={}
        self.click_commands={}
        self.hold_commands={}
        self.next_id=1
        self.win_focused=True
        self.win_minimized=False
        self.win_size=base.get_size()

        #root for the offscreen gui buff
        self.gui_root=NodePath("gui_root")
        #texture for color, this is the aux rgba tex
        self.gui_color_tex=Texture()
        self.gui_color_tex.set_wrap_u(Texture.WM_clamp)
        self.gui_color_tex.set_wrap_v(Texture.WM_clamp)
        #texture for id (as color), this is the default tex
        self.gui_id_tex=Texture()
        self.gui_id_tex.set_wrap_u(Texture.WM_clamp)
        self.gui_id_tex.set_wrap_v(Texture.WM_clamp)
        #main buff
        self.buff=self._make_buffer("gui_canvas", self.win_size, self.gui_id_tex, self.gui_color_tex)
        self.gui_cam=base.make_camera(win=self.buff)
        self.gui_cam.reparent_to(self.gui_root)
        self.gui_cam.set_pos(self.win_size[0]//2,self.win_size[1]//2,100)
        self.gui_cam.set_p(-90)
        lens = OrthographicLens()
        lens.set_film_size(*self.win_size)
        self.gui_cam.node().set_lens(lens)
        #mouse pixel buff
        self.mouse_tex=Texture()
        self.mouse_buff=self._make_buffer("mouse_spy", (1,1), self.mouse_tex)
        self.mouse_cam=base.make_camera(win=self.mouse_buff)
        self.mouse_cam.reparent_to(self.gui_root)
        self.mouse_cam.set_pos(0, 0, 100)
        self.mouse_cam.set_p(-90)
        lens = OrthographicLens()
        lens.set_film_size(1, 1)
        self.mouse_cam.node().set_lens(lens)

        #pfm for dynamic data
        #clip planes
        self.pfm_clips=PfmFile()
        self.pfm_clips.clear(x_size=128, y_size=128, num_channels=4)
        self.pfm_clips.fill(Point4(600.0, 0.0, 800.0, 0.0))#top, bottom, left, right in gl_FragCoord
        #pos, scale
        self.pfm_pos_scale=PfmFile()
        self.pfm_pos_scale.clear(x_size=128, y_size=128, num_channels=4)
        self.pfm_pos_scale.fill(Point4(0.0, 0.0, 1.0, 1.0))

        #set some default shader inputs
        self.tex_atlas=loader.load_texture(texture_atlas)
        self.tex_atlas.setMagfilter(SamplerState.FT_linear)
        self.tex_atlas.setMinfilter(SamplerState.FT_linear)
        self.gui_root.set_shader_input('atlas', self.tex_atlas)
        self.clip_tex=Texture()
        self.clip_tex.load(self.pfm_clips)
        self.gui_root.set_shader_input('clips', self.clip_tex)
        self.pos_scale_tex=Texture()
        self.pos_scale_tex.load(self.pfm_pos_scale)
        self.gui_root.set_shader_input('pos_scale', self.pos_scale_tex)
        self.gui_root.set_shader_input('click', 0.0)
        self.gui_root.set_shader_input('mouse_tex', self.mouse_tex)

        #quad to display the gui on-screen
        cm = CardMaker("plane")
        cm.set_frame_fullscreen_quad()
        cm.set_uv_range(Point2(0,1), Point2(1,0))
        self.quad = NodePath(cm.generate())
        self.quad.set_texture(self.gui_color_tex)
        self.quad.reparent_to(render2d)
        self.quad.set_transparency(TransparencyAttrib.MAlpha, 1)

        #tasks:
        taskMgr.add(self.update, 'update_tsk')
        #events:
        self.accept('mouse1', self.on_mouse_down)
        self.accept('mouse1-up', self.on_mouse_up)
        self.accept( 'window-event', self.on_window_event)

    def __getitem__(self, item):
        if item in element_id:
            return self.elements[item]
        elif item in self.element_id:
            return self.elements[self.element_id[item]]
        return None

    def get_id(self, name):
        if name not in self.element_id:
            self.element_id[name]=self.next_id
            self.next_id+=1
        return self.element_id[name]

    def on_window_resize(self):
        ##ToDo: resize buff
        pass
    def on_window_minimize(self):
        pass
    def on_window_focus(self):
        pass

    def on_window_event(self, window=None):
        if window is not None: # window is none if panda3d is not started
            if self.win_size != base.get_size():
                self.on_window_resize()
            elif window.get_properties().get_minimized() !=  self.win_minimized:
                self.on_window_minimize()
            elif window.get_properties().get_foreground() !=  self.win_focused:
                self.on_window_focus()

            self.win_size = base.get_size()

    def on_mouse_down(self):
        '''Fired when the mouse button is pressed'''
        self.mouse_is_down=True
        self.gui_root.set_shader_input('click', 1.0)
        base.graphicsEngine.render_frame()
        p=PNMImage(1, 1,4)
        base.graphicsEngine.extract_texture_data(self.mouse_tex, base.win.getGsg())
        self.mouse_tex.store(p)
        c=p.getXelA(0,0)
        self.last_mouse_down_id=self.color_to_id(c)

    def on_mouse_up(self):
        '''Fired when the mouse button is released'''
        if not self.last_frame_mouse_is_down:
            #the mouse down/held has not yet been processed
            #common for touchscreen mouse
            self.update()
        self.mouse_is_down=False
        self.gui_root.set_shader_input('click', 0.0)

    def on_mouse_hold(self, delta):
        '''Fired each frame when the mouse button is held'''
        if delta.length_squared()>0.0:
            id=self.last_mouse_down_id
            if id != 0 and id in self.hold_commands:
                self.hold_commands[id](delta)


    def on_mouse_click(self):
        '''Fired on mouse click'''
        base.graphicsEngine.render_frame()
        p=PNMImage(1, 1,4)
        base.graphicsEngine.extract_texture_data(self.mouse_tex, base.win.getGsg())
        self.mouse_tex.store(p)
        c=p.getXelA(0,0)
        id=self.color_to_id(c)
        if id != 0 and id == self.last_mouse_down_id:
            if id in self.click_commands:
                self.click_commands[id]()

    def set_clip(self, id, top, bottom, left=0, right=0):
        x=id%128
        y=id//128
        self.pfm_clips.set_point4(x, y, Point4(top, bottom, left, right))
        self.update_clips=True
        #self.clip_tex.load(self.pfm_clips)
        #self.gui_root.set_shader_input('clips', t)

    def set_pos_scale(self, id, x=None, y=None, sx=None, sy=None):
        uv_x=id%128
        uv_y=id//128
        data=self.pfm_pos_scale.modify_point4(uv_x, uv_y)
        if x is not None:
            data[0]=x
        if y is not None:
            data[1]=y
        if sx is not None:
            data[2]=sy
        if sy is not None:
            data[3]=sy
        self.update_pos_scale=True

    def set_delta_pos(self, id, x=None, y=None):
        uv_x=id%128
        uv_y=id//128
        data=self.pfm_pos_scale.modify_point4(uv_x, uv_y)
        if x is not None:
            data[0]+=x
        if y is not None:
            data[1]+=y
        self.update_pos_scale=True

    def color_to_id(self, color):
        ap = int(color[0] * 255)
        bp = int(color[1] * 255)
        cp = int(color[2] * 255)
        return ap << 16 | bp << 8 | cp

    def id_to_color(self, id):
        r = (id >> 16)
        g = (id ^ (r << 16)) >> 8
        b = (id ^ (r << 16) ^ (g << 8))
        color = Vec4(r,g,b, 1.0) / 255.0
        color.w = id
        return color

    def update(self, task=None):
        ''' Update task run every frame, or more often (on_mouse_up)'''
        #update inputs
        if self.update_clips:
            self.update_clips=False
            self.clip_tex.load(self.pfm_clips)
            self.gui_root.set_shader_input('clips', self.clip_tex)
        if self.update_pos_scale:
            self.update_pos_scale=False
            self.pos_scale_tex.load(self.pfm_pos_scale)
            self.gui_root.set_shader_input('pos_scale', self.pos_scale_tex)
        #track mouse
        if base.mouseWatcherNode.hasMouse():
            mouse_pos = (base.mouseWatcherNode.get_mouse()+Point2(1.0, 1.0))/2.0
            mouse_pos.x=mouse_pos.x*800
            mouse_pos.y=600-(mouse_pos.y*600)
            self.mouse_cam.set_pos(mouse_pos.x, mouse_pos.y, 100)
            #dispatch click events if any
            if not self.mouse_is_down and self.last_frame_mouse_is_down:
                self.on_mouse_click()
            elif self.mouse_is_down:
                delta=mouse_pos-self.last_frame_mouse_pos
                self.on_mouse_hold(delta)
            #store for next frame
            self.last_frame_mouse_pos=mouse_pos
            self.last_frame_mouse_is_down=self.mouse_is_down
        #run task again, if called from a task
        if task:
            return task.again

    def _get_vertex_format(self):
        try:
            vtx_format=self._vtx_format
        except AttributeError:
            array = GeomVertexArrayFormat()
            array.add_column("vertex", 4, Geom.NT_float32, Geom.C_point)
            array.add_column("texcoord", 2, Geom.NT_float32, Geom.C_texcoord)
            array.add_column("offset_uv", 4, Geom.NT_float32, Geom.C_other)
            array.add_column("color_id", 4, Geom.NT_float32, Geom.C_other)
            self._vtx_format = GeomVertexFormat()
            self._vtx_format.add_array(array)
            self._vtx_format = GeomVertexFormat.registerFormat(self._vtx_format)
            vtx_format=self._vtx_format
        return vtx_format

    def make_group(self, name):
        vtx_format=self._get_vertex_format()
        vdata = GeomVertexData('quad', vtx_format, Geom.UHDynamic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        offset_uv = GeomVertexWriter(vdata, 'offset_uv')
        color_id = GeomVertexWriter(vdata, 'color_id')
        self.groups[name]=GeomData(vdata, vertex, texcoord, offset_uv, color_id)

    def add_quad(self, group_name, id, size=32, pos=(0,0),
                   uv=(0,0, 1,1), hover_uv=(0,0), click_uv=(0,0)):

        group=self.groups[group_name]
        #color(_id) is the same for all vertex
        color=self.id_to_color(id)
        #geom tristrip cheat sheet:
        #
        #  0---2     3---1
        #  |  /|     |  /|
        #  | / |     | / |
        #  |/  |     |/  |
        #  1---3     2---0
        #
        # uv: uv=(0,0, 1,1)
        #
        #  [0][3]---[2][3]
        #  |       /|
        #  |      / |
        #  |     /  |
        #  |    /   |
        #  |   /    |
        #  |  /     |
        #  | /      |
        #  [0][1]---[2][1]

        #vert 0
        group.vertex.add_data4(pos[0], pos[1], 0, 1)
        group.texcoord.add_data2(uv[0], uv[3])
        group.offset_uv.add_data4(*hover_uv, *click_uv)
        group.color_id.add_data4(*color)
        #vert 1
        group.vertex.add_data4(pos[0], pos[1]+size, 0, 1)
        group.texcoord.add_data2(uv[0], uv[1])
        group.offset_uv.add_data4(*hover_uv, *click_uv)
        group.color_id.add_data4(*color)
        #vert 2
        group.vertex.add_data4(pos[0]+size, pos[1], 0, 1)
        group.texcoord.add_data2(uv[2], uv[3])
        group.offset_uv.add_data4(*hover_uv, *click_uv)
        group.color_id.add_data4(*color)
        #vert 3
        group.vertex.add_data4(pos[0]+size, pos[1]+size, 0, 1)
        group.texcoord.add_data2(uv[2], uv[1])
        group.offset_uv.add_data4(*hover_uv, *click_uv)
        group.color_id.add_data4(*color)

    def close_all_groups(self):
        for name in self.groups:
            if name not in self.nodes:
                self.close_group(name)

    def close_group(self, group_name):
        group=self.groups[group_name]
        geom = Geom(group.vdata)
        tris = GeomTriangles(Geom.UHDynamic)
        for i in range(group.vdata.get_num_rows()//4):
            tris.add_vertex((i*4)+0)
            tris.add_vertex((i*4)+2)
            tris.add_vertex((i*4)+1)
            tris.close_primitive()
            tris.add_vertex((i*4)+2)
            tris.add_vertex((i*4)+3)
            tris.add_vertex((i*4)+1)
            tris.close_primitive()

        geom.add_primitive(tris)
        gnode =GeomNode('quad')
        gnode.add_geom(geom)
        size=base.get_size()
        gnode.set_bounds(BoundingBox((0,0,0), (size[0], size[1], 1000)))
        np=self.gui_root.attach_new_node(gnode)
        np.set_shader(Shader.make(Shader.SLGLSL, shaders.widget.vertex, shaders.widget.fragment),1)
        np.set_transparency(TransparencyAttrib.MAlpha, 1)
        self.nodes[group_name]=np

    def _make_buffer(self, name, size=[512, 512], tex=None, aux_tex=None,
                    rgba_bits=(8, 8, 8, 8), clear_color=(0,0,0.0,0)):
        winprops = WindowProperties()
        winprops.set_size(*size)
        props = FrameBufferProperties()
        props.set_rgb_color(True)
        props.set_rgba_bits(*rgba_bits)
        props.set_srgb_color(False)
        if aux_tex is not None:
            props.set_aux_rgba(True)
        flags=GraphicsPipe.BF_refuse_window | GraphicsPipe.BF_rtt_cumulative
        buff= base.graphicsEngine.make_output(pipe = base.pipe,
                                             name = name,
                                             sort = -2,
                                             fb_prop = props,
                                             win_prop = winprops,
                                             flags= flags,
                                             gsg=base.win.get_gsg(),
                                             host = base.win)
        if tex is None:
            tex=Texture()
        buff.set_clear_color(clear_color)
        buff.add_render_texture(tex=tex,
                                mode=GraphicsOutput.RTMBindOrCopy,
                                bitplane=GraphicsOutput.RTPColor)
        if aux_tex is not None:
            buff.set_clear_active(GraphicsOutput.RTP_aux_rgba_0, True)
            buff.add_render_texture(tex=aux_tex,
                                    mode=GraphicsOutput.RTMBindOrCopy,
                                    bitplane=GraphicsOutput.RTPAuxRgba0)

        return buff
