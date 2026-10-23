# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Screencast Keys",
    "author": "Paulo Gomes, Bart Crouch, John E. Herrenyo, Gaia Clary, "
              "Pablo Vazquez",
    "version": (2, 1),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar (N) > Screencast Keys",
    "warning": "",
    "description": "Display keys pressed in the 3D View, "
                   "useful for screencasts.",
    "category": "3D View"}

import blf
import bpy
import gpu
import time
import datetime
from gpu_extras.batch import batch_for_shader


MOUSE_RATIO = 0.535

_shader = None


def get_shader():
    global _shader
    if _shader is None:
        _shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    return _shader


def draw_tris(points, indices, color):
    shader = get_shader()
    batch = batch_for_shader(shader, 'TRIS', {"pos": points}, indices=indices)
    gpu.state.blend_set('ALPHA')
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def draw_polygon_fill(points, color):
    # fan-triangulate from the first vertex (mouse shapes are near-convex)
    if len(points) < 3:
        return
    indices = [(0, i, i + 1) for i in range(1, len(points) - 1)]
    draw_tris(points, indices, color)


def draw_line_strip(points, color):
    if len(points) < 2:
        return
    shader = get_shader()
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": points})
    gpu.state.blend_set('ALPHA')
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set('NONE')


ALIGN_FACTOR = {'left': 0.0, 'center': 0.5, 'right': 1.0}


def get_visible_bounds(context):
    # with Region Overlap on, the toolbar and sidebar float over the 3D View,
    # so keep the display out from under them
    left, right = 0, context.region.width
    if context.preferences.system.use_region_overlap:
        for r in context.area.regions:
            if r.type not in {'TOOLS', 'UI'} or r.width <= 1:
                continue
            if r.alignment == 'LEFT':
                left = max(left, r.width)
            elif r.alignment == 'RIGHT':
                right = min(right, context.region.width - r.width)
    return(left, right)


def draw_callback_px(self, context):
    wm = context.window_manager
    sc = context.scene
    if not wm.screencast_keys_keys:
        return

    region = context.region
    font_size = sc.screencast_keys_font_size
    mouse_size = sc.screencast_keys_mouse_size
    fade_time = sc.screencast_keys_fade_time
    align = ALIGN_FACTOR[sc.screencast_keys_align]
    line_h = font_size * 1.3
    now = time.time()

    # recent key-presses, newest first
    lines = []
    for i in range(len(self.key)):
        label_time = now - self.time[i]
        if label_time >= fade_time:
            break
        alpha = min(1.0, max(0.0, fade_time * (fade_time - label_time)))
        lines.append((self.key[i], alpha))

    # get rid of status texts that aren't displayed anymore
    self.key = self.key[:len(lines)]
    self.time = self.time[:len(lines)]

    # measure everything first, so the box, keys, mouse icon and last
    # operator always line up with each other
    blf.size(0, font_size)
    text_w = sc.screencast_keys_box_width
    for text, alpha in lines:
        text_w = max(text_w, blf.dimensions(0, text)[0])
    text_h = len(lines) * line_h

    show_icon = sc.screencast_keys_mouse == 'icon'
    icon_w = mouse_size * MOUSE_RATIO if show_icon else 0
    icon_h = mouse_size if show_icon else 0
    gap = icon_w * 0.7 if show_icon and text_w > 0 else 0
    row_w = icon_w + gap + text_w
    row_h = max(icon_h, text_h)

    op_text = None
    op_size = font_size * 0.5
    op_w = op_h = 0
    if sc.screencast_keys_show_operator and wm.operators:
        op_text = "Last: %s" % (wm.operators[-1].bl_label)
        blf.size(0, op_size)
        op_w = blf.dimensions(0, op_text)[0]
        op_h = op_size * 1.6

    content_w = max(row_w, op_w)
    content_h = row_h + op_h
    if content_h == 0:
        content_h = line_h  # keep an empty box visible

    # Position X/Y picks an anchor point; the alignment decides whether the
    # display grows to the right of it, around it, or to the left of it
    pad_x, pad_y = 16, 12
    left, right = get_visible_bounds(context)
    x0 = left + (right - left) * sc.screencast_keys_pos_x / 100 - \
        content_w * align
    x0 = max(left + pad_x, min(x0, right - content_w - pad_x))
    y0 = region.height * sc.screencast_keys_pos_y / 100
    y0 = max(pad_y, min(y0, region.height - content_h - pad_y))

    if sc.screencast_keys_box_draw and \
    (lines or not sc.screencast_keys_box_hide):
        bx0, by0 = x0 - pad_x, y0 - pad_y
        bx1, by1 = x0 + content_w + pad_x, y0 + content_h + pad_y
        draw_tris([(bx0, by0), (bx0, by1), (bx1, by1), (bx1, by0)],
            [(0, 1, 2), (0, 2, 3)], tuple(sc.screencast_keys_box_color))

    # keys and mouse icon sit side by side, above the last operator
    row_x = x0 + (content_w - row_w) * align
    row_y = y0 + op_h
    if sc.screencast_keys_mouse_position == 'left':
        icon_x, text_x = row_x, row_x + icon_w + gap
    else:
        text_x, icon_x = row_x, row_x + text_w + gap

    if show_icon:
        draw_mouse_icon(self, sc, icon_x, row_y + (row_h - icon_h) / 2)
    else:
        self.mouse = []
        self.mouse_time = []

    font_color_r, font_color_g, font_color_b, font_color_alpha = \
        sc.screencast_keys_text_color
    blf.size(0, font_size)
    blf.enable(0, blf.SHADOW)
    blf.shadow_offset(0, 1, -1)
    blf.shadow(0, 5, 0.0, 0.0, 0.0, 0.8)

    text_y = row_y + (row_h - text_h) / 2 + font_size * 0.3
    for i, (text, alpha) in enumerate(lines):
        w = blf.dimensions(0, text)[0]
        blf.position(0, text_x + (text_w - w) * align, text_y + i * line_h, 0)
        blf.color(0, font_color_r, font_color_g, font_color_b,
            font_color_alpha * alpha)
        blf.draw(0, text)

    if op_text:
        blf.size(0, op_size)
        blf.position(0, x0 + (content_w - op_w) * align,
            y0 + op_size * 0.3, 0)
        blf.color(0, font_color_r, font_color_g, font_color_b,
            font_color_alpha * 0.8)
        blf.draw(0, op_text)

    # disable shadows so they don't appear all over blender
    blf.disable(0, blf.SHADOW)

    if sc.screencast_keys_timer_show:
        draw_timer(context, right)


def draw_timer(context, right):
    sc = context.scene
    # calculate overall time
    overall_time = datetime.timedelta(seconds=int(
        time.time() - ScreencastKeysStatus.overall_time[0]))
    text = "Elapsed Time: %s" % (overall_time)

    timer_color_r, timer_color_g, timer_color_b, timer_color_alpha = \
        sc.screencast_keys_timer_color

    # draw time in the bottom-right corner
    blf.size(0, sc.screencast_keys_timer_size)
    blf.position(0, right - blf.dimensions(0, text)[0] - 12, 10, 0)
    blf.color(0, timer_color_r, timer_color_g, timer_color_b,
        timer_color_alpha)
    blf.draw(0, text)


def bezier_segment_points(segment, steps=10):
    # sample a cubic bezier segment (replaces the old glMap1f evaluator)
    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = segment
    points = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        b0 = u * u * u
        b1 = 3.0 * u * u * t
        b2 = 3.0 * u * t * t
        b3 = t * t * t
        points.append((b0 * x0 + b1 * x1 + b2 * x2 + b3 * x3,
                       b0 * y0 + b1 * y1 + b2 * y2 + b3 * y3))
    return points


def draw_mouse_icon(self, sc, offset_x, offset_y):
    alpha = sc.screencast_keys_text_color[3]
    for shape in ["mouse", "left_button", "middle_button", "right_button"]:
        draw_mouse(sc, shape, "outline", alpha * 0.4, offset_x, offset_y)

    final = 0
    for i in range(len(self.mouse)):
        click_time = time.time() - self.mouse_time[i]
        if click_time < 2:
            shape = map_mouse_event(self.mouse[i])
            if shape:
                draw_mouse(sc, shape, "filled",
                    min(1.0, max(0.0, 2 * (2 - click_time))),
                    offset_x, offset_y)
            final = i + 1
        else:
            break

    # get rid of mouse clicks that aren't displayed anymore
    self.mouse = self.mouse[:final]
    self.mouse_time = self.mouse_time[:final]


def draw_mouse(sc, shape, style, alpha, offset_x, offset_y):
    mouse_size = sc.screencast_keys_mouse_size
    shape_data = get_shape_data(shape)

    # color
    r, g, b, a = sc.screencast_keys_text_color
    color = (r, g, b, alpha)

    # build the full outline polygon from the bezier segments
    outline = []
    for segment in shape_data:
        points = bezier_segment_points(segment)
        for px, py in points:
            outline.append((offset_x + mouse_size * px,
                            offset_y + mouse_size * py))

    if style == "outline":
        draw_line_strip(outline, color)
    else:  # style == "filled"
        draw_polygon_fill(outline, color)


# hardcoded data to draw the graphical represenation of the mouse
def get_shape_data(shape):
    data = []
    if shape == "mouse":
        data = [[[0.404, 0.032, 0.0],
            [0.096, 0.002, 0.0],
            [0.059, 0.126, 0.0],
            [0.04, 0.213, 0.0]],
            [[0.04, 0.213, 0.0],
            [-0.015, 0.465, 0.0],
            [-0.005, 0.564, 0.0],
            [0.032, 0.87, 0.0]],
            [[0.032, 0.87, 0.0],
            [0.05, 0.973, 0.0],
            [0.16, 1.002, 0.0],
            [0.264, 1.002, 0.0]],
            [[0.264, 1.002, 0.0],
            [0.369, 1.002, 0.0],
            [0.478, 0.973, 0.0],
            [0.497, 0.87, 0.0]],
            [[0.497, 0.87, 0.0],
            [0.533, 0.564, 0.0],
            [0.554, 0.465, 0.0],
            [0.499, 0.213, 0.0]],
            [[0.499, 0.213, 0.0],
            [0.490, 0.126, 0.0],
            [0.432, 0.002, 0.0],
            [0.404, 0.032, 0.0]]]
    elif shape == "left_button":
        data = [[[0.154, 0.763, 0.0],
            [0.126, 0.755, 0.0],
            [0.12, 0.754, 0.0],
            [0.066, 0.751, 0.0]],
            [[0.066, 0.751, 0.0],
            [0.043, 0.75, 0.0],
            [0.039, 0.757, 0.0],
            [0.039, 0.767, 0.0]],
            [[0.039, 0.767, 0.0],
            [0.047, 0.908, 0.0],
            [0.078, 0.943, 0.0],
            [0.155, 0.97, 0.0]],
            [[0.155, 0.97, 0.0],
            [0.174, 0.977, 0.0],
            [0.187, 0.975, 0.0],
            [0.191, 0.972, 0.0]],
            [[0.191, 0.972, 0.0],
            [0.203, 0.958, 0.0],
            [0.205, 0.949, 0.0],
            [0.199, 0.852, 0.0]],
            [[0.199, 0.852, 0.0],
            [0.195, 0.77, 0.0],
            [0.18, 0.771, 0.0],
            [0.154, 0.763, 0.0]]]
    elif shape == "middle_button":
        data = [[[0.301, 0.8, 0.0],
            [0.298, 0.768, 0.0],
            [0.231, 0.768, 0.0],
            [0.228, 0.8, 0.0]],
            [[0.228, 0.8, 0.0],
            [0.226, 0.817, 0.0],
            [0.225, 0.833, 0.0],
            [0.224, 0.85, 0.0]],
            [[0.224, 0.85, 0.0],
            [0.222, 0.873, 0.0],
            [0.222, 0.877, 0.0],
            [0.224, 0.9, 0.0]],
            [[0.224, 0.9, 0.0],
            [0.225, 0.917, 0.0],
            [0.226, 0.933, 0.0],
            [0.228, 0.95, 0.0]],
            [[0.228, 0.95, 0.0],
            [0.231, 0.982, 0.0],
            [0.298, 0.982, 0.0],
            [0.301, 0.95, 0.0]],
            [[0.301, 0.95, 0.0],
            [0.302, 0.933, 0.0],
            [0.303, 0.917, 0.0],
            [0.305, 0.9, 0.0]],
            [[0.305, 0.9, 0.0],
            [0.307, 0.877, 0.0],
            [0.307, 0.873, 0.0],
            [0.305, 0.85, 0.0]],
            [[0.305, 0.85, 0.0],
            [0.303, 0.833, 0.0],
            [0.302, 0.817, 0.0],
            [0.301, 0.8, 0.0]]]
    elif shape == "middle_down_button":
        data = [[[0.301, 0.8, 0.0],
            [0.298, 0.768, 0.0],
            [0.231, 0.768, 0.0],
            [0.228, 0.8, 0.0]],
            [[0.228, 0.8, 0.0],
            [0.226, 0.817, 0.0],
            [0.225, 0.833, 0.0],
            [0.224, 0.85, 0.0]],
            [[0.224, 0.85, 0.0],
            [0.264, 0.873, 0.0],
            [0.284, 0.873, 0.0],
            [0.305, 0.85, 0.0]],
            [[0.305, 0.85, 0.0],
            [0.303, 0.833, 0.0],
            [0.302, 0.817, 0.0],
            [0.301, 0.8, 0.0]]]
    elif shape == "middle_up_button":
        data = [[[0.270, 0.873, 0.0],
            [0.264, 0.873, 0.0],
            [0.222, 0.877, 0.0],
            [0.224, 0.9, 0.0]],
            [[0.224, 0.9, 0.0],
            [0.225, 0.917, 0.0],
            [0.226, 0.933, 0.0],
            [0.228, 0.95, 0.0]],
            [[0.228, 0.95, 0.0],
            [0.231, 0.982, 0.0],
            [0.298, 0.982, 0.0],
            [0.301, 0.95, 0.0]],
            [[0.301, 0.95, 0.0],
            [0.302, 0.933, 0.0],
            [0.303, 0.917, 0.0],
            [0.305, 0.9, 0.0]],
            [[0.305, 0.9, 0.0],
            [0.307, 0.877, 0.0],
            [0.284, 0.873, 0.0],
            [0.270, 0.873, 0.0]]]
    elif shape == "right_button":
        data = [[[0.375, 0.763, 0.0],
            [0.402, 0.755, 0.0],
            [0.408, 0.754, 0.0],
            [0.462, 0.751, 0.0]],
            [[0.462, 0.751, 0.0],
            [0.486, 0.75, 0.0],
            [0.49, 0.757, 0.0],
            [0.489, 0.767, 0.0]],
            [[0.489, 0.767, 0.0],
            [0.481, 0.908, 0.0],
            [0.451, 0.943, 0.0],
            [0.374, 0.97, 0.0]],
            [[0.374, 0.97, 0.0],
            [0.354, 0.977, 0.0],
            [0.341, 0.975, 0.0],
            [0.338, 0.972, 0.0]],
            [[0.338, 0.972, 0.0],
            [0.325, 0.958, 0.0],
            [0.324, 0.949, 0.0],
            [0.329, 0.852, 0.0]],
            [[0.329, 0.852, 0.0],
            [0.334, 0.77, 0.0],
            [0.348, 0.771, 0.0],
            [0.375, 0.763, 0.0]]]

    return(data)


# return the shape that belongs to the given event
def map_mouse_event(event):
    shape = False

    if event == 'LEFTMOUSE':
        shape = "left_button"
    elif event == 'MIDDLEMOUSE':
        shape = "middle_button"
    elif event == 'RIGHTMOUSE':
        shape = "right_button"
    elif event == 'WHEELDOWNMOUSE':
        shape = "middle_down_button"
    elif event == 'WHEELUPMOUSE':
        shape = "middle_up_button"

    return(shape)


class ScreencastKeysStatus(bpy.types.Operator):
    bl_idname = "view3d.screencast_keys"
    bl_label = "Screencast Keys"
    bl_description = "Display keys pressed in the 3D View"
    last_activity = 'NONE'

    _handle = None
    _timer = None

    @staticmethod
    def handle_add(self, context):
        ScreencastKeysStatus._handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')
        ScreencastKeysStatus._timer = context.window_manager.event_timer_add(
            0.075, window=context.window)

    @staticmethod
    def handle_remove(context):
        if ScreencastKeysStatus._handle is not None:
            context.window_manager.event_timer_remove(
                ScreencastKeysStatus._timer)
            bpy.types.SpaceView3D.draw_handler_remove(
                ScreencastKeysStatus._handle, 'WINDOW')
        ScreencastKeysStatus._handle = None
        ScreencastKeysStatus._timer = None

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        if event.type == 'TIMER':
            # no input, so no need to change the display
            return {'PASS_THROUGH'}

        scene = context.scene
        # keys that shouldn't show up in the 3D View
        mouse_keys = ['MOUSEMOVE', 'MIDDLEMOUSE', 'LEFTMOUSE',
         'RIGHTMOUSE', 'WHEELDOWNMOUSE', 'WHEELUPMOUSE']
        ignore_keys = ['LEFT_SHIFT', 'RIGHT_SHIFT', 'LEFT_ALT',
         'RIGHT_ALT', 'LEFT_CTRL', 'RIGHT_CTRL', 'TIMER',
         'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE']
        if scene.screencast_keys_mouse != 'text':
            ignore_keys.extend(mouse_keys)

        if event.value == 'PRESS' or (event.value == 'RELEASE' and
        self.last_activity == 'KEYBOARD' and event.type in mouse_keys):
            # add key-press to display-list
            sc_keys = []

            if event.ctrl:
                sc_keys.append("Ctrl ")
            if event.alt:
                sc_keys.append("Alt ")
            if event.shift:
                sc_keys.append("Shift ")

            sc_amount = ""

            if self.key:
                if event.type not in ignore_keys and \
                event.type in self.key[0]:
                    mods = "+ ".join(sc_keys)
                    old_mods = "+ ".join(self.key[0].split("+ ")[:-1])
                    if mods == old_mods:
                        amount = self.key[0].split(" x")
                        if len(amount) >= 2:
                            sc_amount = " x" + str(int(amount[-1]) + 1)
                        else:
                            sc_amount = " x2"
                        del self.key[0]
                        del self.time[0]

            if event.type not in ignore_keys:
                sc_keys.append(event.type)
                self.key.insert(0, "+ ".join(sc_keys) + sc_amount)
                self.time.insert(0, time.time())

            elif event.type in mouse_keys and \
            scene.screencast_keys_mouse == 'icon':
                self.mouse.insert(0, event.type)
                self.mouse_time.insert(0, time.time())

            if event.type in mouse_keys:
                self.last_activity = 'MOUSE'
            else:
                self.last_activity = 'KEYBOARD'

        if not context.window_manager.screencast_keys_keys:
            # stop script
            ScreencastKeysStatus.handle_remove(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def cancel(self, context):
        if context.window_manager.screencast_keys_keys:
            ScreencastKeysStatus.handle_remove(context)
            context.window_manager.screencast_keys_keys = False

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            if context.window_manager.screencast_keys_keys is False:
                # operator is called for the first time, start everything
                context.window_manager.screencast_keys_keys = True
                self.key = []
                self.time = []
                self.mouse = []
                self.mouse_time = []
                ScreencastKeysStatus.overall_time = []
                ScreencastKeysStatus.handle_add(self, context)
                ScreencastKeysStatus.overall_time.insert(0, time.time())
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
            else:
                # operator is called again, stop displaying
                context.window_manager.screencast_keys_keys = False
                self.key = []
                self.time = []
                self.mouse = []
                self.mouse_time = []
                ScreencastKeysStatus.overall_time = []
                return {'CANCELLED'}
        else:
            self.report({'WARNING'},
                "3D View not found, can't run Screencast Keys")
            return {'CANCELLED'}


class ScreencastKeysTimerReset(bpy.types.Operator):
    """Reset Timer"""
    bl_idname = "view3d.screencast_keys_timer_reset"
    bl_label = "Reset Timer"
    bl_description = "Set the timer back to zero"

    def execute(self, context):
        ScreencastKeysStatus.overall_time = [time.time()]
        return {'FINISHED'}


# properties used by the script
def init_properties():
    scene = bpy.types.Scene
    wm = bpy.types.WindowManager

    scene.screencast_keys_pos_x = bpy.props.IntProperty(
        name="Position X",
        description="Horizontal position, from the left (0) to the right "
                    "(100) of the 3D View",
        default=3,
        min=0,
        max=100)
    scene.screencast_keys_pos_y = bpy.props.IntProperty(
        name="Position Y",
        description="Vertical position, from the bottom (0) to the top "
                    "(100) of the 3D View",
        default=10,
        min=0,
        max=100)
    scene.screencast_keys_align = bpy.props.EnumProperty(
        items=(("left", "Left", "Line up on the left and grow to the right "
               "of Position X", 'ALIGN_LEFT', 0),
              ("center", "Center", "Center on Position X", 'ALIGN_CENTER', 1),
              ("right", "Right", "Line up on the right and grow to the left "
               "of Position X", 'ALIGN_RIGHT', 2)),
        name="Alignment",
        description="How the keys and mouse line up, and which way the "
                    "display grows from its position",
        default='left')
    scene.screencast_keys_font_size = bpy.props.IntProperty(
        name="Text Size",
        description="Text size displayed on 3D View",
        default=24, min=10, max=150)
    scene.screencast_keys_mouse_size = bpy.props.IntProperty(
        name="Mouse Size",
        description="Mouse size displayed on 3D View",
        default=33, min=10, max=150)
    scene.screencast_keys_text_color = bpy.props.FloatVectorProperty(
        name="Text / Icon Color",
        description="Color for the text and mouse icon",
        default=(1.0, 1.0, 1.0, 1.0),
        min=0.1,
        max=1,
        subtype='COLOR',
        size=4)
    scene.screencast_keys_box_color = bpy.props.FloatVectorProperty(
        name="Box Color",
        description="Box color",
        default=(0.0, 0.0, 0.0, 0.3),
        min=0,
        max=1,
        subtype='COLOR',
        size=4)
    scene.screencast_keys_box_width = bpy.props.IntProperty(
        name="Box Width",
        description="Box default width (resizes with text if needed)",
        default=0,
        min=0,
        max=2048,
        soft_max=1024)
    scene.screencast_keys_mouse = bpy.props.EnumProperty(
        items=(("none", "No Mouse", "Don't display mouse events"),
              ("icon", "Icon", "Display graphical representation of "
               "the mouse"),
              ("text", "Text", "Display mouse events as text lines")),
        name="Mouse Display",
        description="Display mouse events",
        default='icon')
    scene.screencast_keys_mouse_position = bpy.props.EnumProperty(
        items=(("left", "Left", "Mouse icon on the left of the keys"),
              ("right", "Right", "Mouse icon on the right of the keys")),
        name="Icon Side",
        description="Which side of the keys the mouse icon is on",
        default='left')
    scene.screencast_keys_box_draw = bpy.props.BoolProperty(
        name="Display Box",
        description="Display a bounding box behind the text",
        default=True)
    scene.screencast_keys_box_hide = bpy.props.BoolProperty(
        name="Hide Box",
        description="Hide the box when no key is pressed",
        default=False)
    scene.screencast_keys_fade_time = bpy.props.FloatProperty(
        name="Fade Out Time",
        description="Time in seconds for keys to last on screen",
        default=3.5,
        min=0.5,
        max=10.0,
        soft_max=5.0,
        step=10,
        subtype='TIME')
    scene.screencast_keys_show_operator = bpy.props.BoolProperty(
        name="Display Last Operator",
        description="Display the last operator used",
        default=True)
    scene.screencast_keys_timer_show = bpy.props.BoolProperty(
        name="Display Timer",
        description="Counter of the elapsed time in H:MM:SS since the "
                    "script started",
        default=False)
    scene.screencast_keys_timer_size = bpy.props.IntProperty(
        name="Time Size",
        description="Time size displayed on 3D View",
        default=12, min=8, max=100)
    scene.screencast_keys_timer_color = bpy.props.FloatVectorProperty(
        name="Time Color",
        description="Color for the time display",
        default=(1.0, 1.0, 1.0, 0.3),
        min=0,
        max=1,
        subtype='COLOR',
        size=4)

    # Runstate initially always set to False
    # note: it is not stored in the Scene, but in window manager:
    wm.screencast_keys_keys = bpy.props.BoolProperty(default=False)


# removal of properties when script is disabled
def clear_properties():
    scene_props = (
        "screencast_keys_mouse",
        "screencast_keys_font_size",
        "screencast_keys_mouse_size",
        "screencast_keys_mouse_position",
        "screencast_keys_fade_time",
        "screencast_keys_pos_x",
        "screencast_keys_pos_y",
        "screencast_keys_align",
        "screencast_keys_box_draw",
        "screencast_keys_text_color",
        "screencast_keys_box_color",
        "screencast_keys_box_hide",
        "screencast_keys_box_width",
        "screencast_keys_show_operator",
        "screencast_keys_timer_show",
        "screencast_keys_timer_color",
        "screencast_keys_timer_size",
    )

    for p in scene_props:
        if hasattr(bpy.types.Scene, p):
            delattr(bpy.types.Scene, p)
    if hasattr(bpy.types.WindowManager, "screencast_keys_keys"):
        delattr(bpy.types.WindowManager, "screencast_keys_keys")


# defining the panel
class OBJECT_PT_keys_status(bpy.types.Panel):
    bl_label = "Screencast Keys"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Screencast Keys"

    def draw(self, context):
        sc = context.scene
        wm = context.window_manager
        layout = self.layout

        if not wm.screencast_keys_keys:
            layout.operator("view3d.screencast_keys", text="Start Display",
                icon="PLAY")
        else:
            layout.operator("view3d.screencast_keys", text="Stop Display",
                icon="PAUSE")

            split = layout.split()

            col = split.column()
            sub = col.column(align=True)
            sub.label(text="Size:")
            sub.prop(sc, "screencast_keys_font_size", text="Text")
            sub.prop(sc, "screencast_keys_mouse_size", text="Mouse")

            col = split.column()
            sub = col.column(align=True)
            sub.label(text="Position:")
            sub.prop(sc, "screencast_keys_pos_x", text="X")
            sub.prop(sc, "screencast_keys_pos_y", text="Y")

            row = layout.row(align=True)
            row.prop(sc, "screencast_keys_align", expand=True)
            row = layout.row(align=True)
            row.prop(sc, "screencast_keys_text_color")
            row = layout.row(align=True)
            row.prop(sc, "screencast_keys_fade_time")

            layout.separator()

            row = layout.row(align=True)
            row.prop(sc, "screencast_keys_mouse", text="Mouse")
            row = layout.row(align=True)
            row.enabled = sc.screencast_keys_mouse == 'icon'
            row.label(text="Icon Side:")
            row.prop(sc, "screencast_keys_mouse_position", expand=True)

            layout.label(text="Display:")
            row = layout.row(align=True)
            row.prop(sc, "screencast_keys_box_draw", text="Box")
            row = layout.row(align=True)
            row.active = sc.screencast_keys_box_draw
            row.prop(sc, "screencast_keys_box_color", text="")
            row.prop(sc, "screencast_keys_box_hide", text="Hide")
            row = layout.row(align=True)
            row.active = sc.screencast_keys_box_draw
            row.prop(sc, "screencast_keys_box_width")
            row = layout.row(align=True)
            row.prop(sc, "screencast_keys_show_operator",
                text="Last Operator")

            split = layout.split()

            col = split.column()
            sub = col.column(align=True)
            sub.prop(sc, "screencast_keys_timer_show", text="Time")
            col = split.column()
            sub = col.column(align=True)
            sub.active = sc.screencast_keys_timer_show
            sub.prop(sc, "screencast_keys_timer_color", text="")

            row = layout.row(align=True)
            row.enabled = sc.screencast_keys_timer_show
            row.prop(sc, "screencast_keys_timer_size")
            row = layout.row(align=True)
            row.enabled = sc.screencast_keys_timer_show
            row.operator("view3d.screencast_keys_timer_reset", text="Reset")


classes = (ScreencastKeysStatus,
           ScreencastKeysTimerReset,
           OBJECT_PT_keys_status)


# store keymaps here to access after registration
addon_keymaps = []


def register():
    init_properties()
    for c in classes:
        bpy.utils.register_class(c)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('view3d.screencast_keys', 'C', 'PRESS',
            shift=True, alt=True)
        addon_keymaps.append((km, kmi))


def unregister():
    # in case its enabled
    ScreencastKeysStatus.handle_remove(bpy.context)

    for c in classes:
        bpy.utils.unregister_class(c)

    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    clear_properties()


if __name__ == "__main__":
    register()
