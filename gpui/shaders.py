from collections import namedtuple


ShaderText = namedtuple('ShaderText', 'vertex, fragment')

widget=ShaderText(
'''#version 130
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
in vec4 color_id;
in vec4 offset_uv;

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform sampler2D pos_scale;
uniform sampler2D clips;

out vec2 uv;
out vec4 uv_offset;
flat out vec4 vtx_color_id;
flat out vec4 clip;

void main()
    {
    int id =int(color_id.w);
    vec4 pos_scale= texelFetch(pos_scale, ivec2(mod(id, 128), 127-(id/128)), 0);
    clip = texelFetch(clips, ivec2(mod(id, 128), 127-(id/128)), 0);

    vec4 vert = p3d_Vertex;
    vert.xy*=pos_scale.zw;
    vert.xy+=pos_scale.xy;

    gl_Position = p3d_ModelViewProjectionMatrix * vert;
    uv=p3d_MultiTexCoord0;
    vtx_color_id=color_id;
    uv_offset=offset_uv;
    }
''',
'''#version 130
uniform sampler2D mouse_tex;
uniform sampler2D atlas;
uniform float click;

in vec2 uv;
in vec4 uv_offset;
flat in vec4 vtx_color_id;
flat in vec4 clip;

void main()
    {
    vec4 color_id=vtx_color_id;
    color_id.w=1.0;

    //clip from bottom
    //if (gl_FragCoord.y < clip.y)
    //    discard;
    //clip from top
    //if (gl_FragCoord.y > clip.x)
    //    discard;

    vec4 mouse_color=texture(mouse_tex, vec2(0.5, 0.5));
    vec2 final_uv=uv;

    if (distance(vtx_color_id.rgb, mouse_color.rgb)<0.0001)
        {
        final_uv.xy-=uv_offset.xy*(1.0-click);
        final_uv.xy-=uv_offset.zw*click;
        }
    vec4 final_color=texture(atlas, final_uv);
    color_id*=step(0.005,final_color.a);
    gl_FragData[0] =color_id;
    gl_FragData[1] =final_color;
    }
''')
