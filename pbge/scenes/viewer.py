import collections
import weakref

import katagames_engine as kengi

from . import image
from .tileset import FLIPPED_HORIZONTALLY_FLAG
from .tileset import FLIPPED_VERTICALLY_FLAG
from .tileset import NOT_ALL_FLAGS
from .. import wait_event, TIMEREVENT

pygame = kengi.pygame  # alias to keep on using pygame, easily
SCROLL_STEP = 12


def anim_delay():
    while wait_event().type != TIMEREVENT:
        pass


class IsometricMapViewer(object):
    def __init__(self, isometric_map, screen, postfx=None, cursor=None):
        self.anim_list = list()
        self.anims = collections.defaultdict(list)

        self.modelmap = collections.defaultdict(list)
        self.uppermap = collections.defaultdict(list)
        self.undermap = collections.defaultdict(list)
        self.waypointmap = collections.defaultdict(list)
        self.fieldmap = dict()
        self.modelsprite = weakref.WeakKeyDictionary()
        self.namedsprite = dict()
        self.darksprite = dict()

        self.isometric_map = isometric_map
        self.screen = screen
        self.x_off = 600
        self.y_off = -200
        self.phase = 0

        self.tile_width = isometric_map.tile_width
        self.tile_height = isometric_map.tile_height
        self.half_tile_width = isometric_map.tile_width // 2
        self.half_tile_height = isometric_map.tile_height // 2

        # _mouse_tile contains the actual tile the mouse is hovering over. However, in most cases what we really want
        # is the location of the mouse cursor. Time to make a property!
        self._mouse_tile = (-1, -1)

        self.postfx = postfx

        self.cursor = cursor

        self.debug_sprite = image.Image("assets/half-floor-tile.png")
        # add-on
        self.debug_sprite.bitmap.set_colorkey((255, 0, 255))

    @property
    def mouse_tile(self):
        if self.cursor:
            return self.cursor.x, self.cursor.y
        else:
            return self._mouse_tile

    def relative_x(self, x, y):
        """Return the relative x position of this tile, ignoring offset."""
        return (x * self.half_tile_width) - (y * self.half_tile_width)

    def relative_y(self, x, y):
        """Return the relative y position of this tile, ignoring offset."""
        return (y * self.half_tile_height) + (x * self.half_tile_height)

    def screen_coords(self, x, y, extra_x_offset=0, extra_y_offset=0):
        return (self.relative_x(x - 1, y - 1) + self.x_off + extra_x_offset,
                self.relative_y(x - 1, y - 1) + self.y_off + extra_y_offset)

    def _default_offsets_case(self, a, b):
        if a is None:
            a = self.x_off
        if b is None:
            b = self.y_off
        return a, b

    @staticmethod
    def static_map_x(rx, ry, tile_width, tile_height, half_tile_width, half_tile_height, return_int=True):
        # Return the map coordinates for the relative_x, relative_y coordinates. All x,y offsets- including both
        # the view offset and the layer offset- should already have been applied. This method is needed for calculating
        # the layer coords of objects imported from Tiled, which have pixel coords.
        #
        # Calculate the x position of map_x tile -1 at ry. There is no tile -1, but this is the origin from which we
        # measure everything.
        ox = float(-ry * half_tile_width) / half_tile_height - tile_width

        # Because of the way Python handles division, we need to apply a little nudge right here.
        if rx - ox < 0 and return_int:
            ox += tile_width

        # Now that we have that x origin, we can determine this screen position's x coordinate by dividing by the
        # tile width. Fantastic.
        if return_int:
            return int((rx - ox) / tile_width) + 1
        else:
            return (rx - ox) / tile_width + 1

    def map_x(self, sx, sy, xoffset_override=None, yoffset_override=None, return_int=True):
        """Return the map x row for the given screen coordinates."""
        x_off, y_off = self._default_offsets_case(xoffset_override, yoffset_override)

        # I was having a lot of trouble with this function, I think because GearHead coordinates use the top left
        # of a square 64x64px cell and for this viewer the map coordinates refer to the midbottom of an arbitrarily
        # sized image. So I broke out some paper and rederived the equations from scratch.

        # We're going to use the relative coordinates of the tiles instead of the screen coordinates.
        rx = sx - x_off
        ry = sy - y_off

        return self.static_map_x(rx, ry, self.tile_width, self.tile_height, self.half_tile_width, self.half_tile_height,
                                 return_int=return_int)

    @staticmethod
    def static_map_y(rx, ry, tile_width, tile_height, half_tile_width, half_tile_height, return_int=True):
        # Return the map coordinates for the relative_x, relative_y coordinates. All x,y offsets- including both
        # the view offset and the layer offset- should already have been applied. This method is needed for calculating
        # the layer coords of objects imported from Tiled, which have pixel coords.
        #
        # Calculate the x position of map_x tile -1 at ry. There is no tile -1, but this is the origin from which we
        # measure everything.
        oy = float(rx * half_tile_height) / half_tile_width - tile_height

        # Because of the way Python handles division, we need to apply a little nudge right here.
        if ry - oy < 0 and return_int:
            oy += tile_height

        # Now that we have that x origin, we can determine this screen position's x coordinate by dividing by the
        # tile width. Fantastic.
        if return_int:
            return int((ry - oy) / tile_height) + 1
        else:
            return (ry - oy) / tile_height + 1

    def map_y(self, sx, sy, xoffset_override=None, yoffset_override=None, return_int=True):
        """Return the map y row for the given screen coordinates."""
        x_off, y_off = self._default_offsets_case(xoffset_override, yoffset_override)

        # We're going to use the relative coordinates of the tiles instead of the screen coordinates.
        rx = sx - x_off
        ry = sy - y_off

        return self.static_map_y(rx, ry, self.tile_width, self.tile_height, self.half_tile_width, self.half_tile_height,
                                 return_int=return_int)

    # -useful?
    # def new_offset_is_within_bounds(self, nuxoff, nuyoff):
    #     mx = self.map_x(self.screen.get_width() // 2, self.screen.get_height() // 2)
    #     my = self.map_y(self.screen.get_width() // 2, self.screen.get_height() // 2)

    def check_origin(self):
        """Make sure the offset point is within map boundaries."""
        mx = self.map_x(self.screen.get_width() // 2, self.screen.get_height() // 2)
        my = self.map_y(self.screen.get_width() // 2, self.screen.get_height() // 2)

        if not self.isometric_map.on_the_map(mx, my):
            if mx < 0:
                mx = 0
            elif mx >= self.isometric_map.width:
                mx = self.isometric_map.width - 1
            if my < 0:
                my = 0
            elif my >= self.isometric_map.height:
                my = self.isometric_map.height - 1
            self.focus(mx, my)

    def focus(self, x, y):
        if self.isometric_map.on_the_map(x, y):
            self.x_off = self.screen.get_width() // 2 - self.relative_x(x, y)
            self.y_off = self.screen.get_height() // 2 - self.relative_y(x, y)

    def next_tile(self, x0, y0, x, y, line, sx, sy, screen_area):
        """Locate the next map tile, moving left to right across the screen. """
        keep_going = True
        if (sx + self.tile_width) > (screen_area.x + screen_area.w):
            if (sy + self.half_tile_height) > (screen_area.y + screen_area.h):
                keep_going = False
            x = x0 + line // 2
            y = y0 + (line + 1) // 2
            line += 1
        else:
            x += 1
            y -= 1
        return x, y, line, keep_going

    def get_line(self, x0, y0, line_number, visible_area):
        mylist = list()
        x = x0 + line_number // 2
        y = y0 + (line_number + 1) // 2

        if self.relative_y(x, y) + self.y_off > visible_area.bottom:
            return None

        while self.relative_x(x - 1, y - 1) + self.x_off < visible_area.right:
            if self.isometric_map.on_the_map(x, y):
                mylist.append((x, y))
            x += 1
            y -= 1
        return mylist

    def handle_anim_sequence(self, record_anim=False):
        # Disable widgets while animation playing.
        tick = 1 if record_anim else 0  # trick to ensure record_anim is used

        while self.anim_list:
            should_delay = False
            self.anims.clear()
            for a in list(self.anim_list):
                if a.needs_deletion:
                    self.anim_list.remove(a)
                    self.anim_list += a.children
                else:
                    should_delay = True
                    a.update(self)
            if should_delay:
                self()
                kengi.flip()

            tick += 1
        self.anims.clear()

    def play_anims(self, *args):
        self.anim_list += args
        self.handle_anim_sequence()

    # - useful?
    # def pos_to_key(self, pos):
    #     # Convert the x,y coordinates to a model_map key...
    #     if pos:
    #         x, y = pos
    #         return int(round(x)), int(round(y))
    #     else:
    #         return "IT'S NOT ON THE MAP ALRIGHT?!"

    def model_depth(self, model):
        return self.relative_y(model.x, model.y)

    def update_camera(self, screen_area, mouse_x, mouse_y):
        # Check for map scrolling, depending on mouse position.
        if mouse_x < 20:
            nu_x_off = self.x_off + SCROLL_STEP
        elif mouse_x > (screen_area.right - 20):
            nu_x_off = self.x_off - SCROLL_STEP
        else:
            nu_x_off = self.x_off

        if mouse_y < 20:
            nu_y_off = self.y_off + SCROLL_STEP
        elif mouse_y > (screen_area.bottom - 20):
            nu_y_off = self.y_off - SCROLL_STEP
        else:
            nu_y_off = self.y_off

        mx = self.map_x(self.screen.get_width() // 2, self.screen.get_height() // 2, nu_x_off, nu_y_off)
        my = self.map_y(self.screen.get_width() // 2, self.screen.get_height() // 2, nu_x_off, nu_y_off)

        if self.isometric_map.on_the_map(mx, my):
            self.x_off = nu_x_off
            self.y_off = nu_y_off

    def __call__(self):
        """Draws this mapview to the provided screen."""
        screen_area = self.screen.get_rect()
        mouse_x, mouse_y = kengi.core.proj_to_vscreen(pygame.mouse.get_pos())

        self.screen.fill('black')
        self.update_camera(screen_area, mouse_x, mouse_y)
        x, y = self.map_x(0, 0) - 2, self.map_y(0, 0) - 1
        x0, y0 = x, y
        keep_going = True
        line_number = 1
        line_cache = list()

        # The visible area describes the region of the map we need to draw. It is bigger than the physical screen
        # because we probably have to draw cells that are not fully on the map.
        visible_area = self.screen.get_rect()
        visible_area.inflate_ip(self.tile_width, self.isometric_map.tile_height)
        visible_area.h += self.isometric_map.tile_height - self.isometric_map.layers[-1].offsety

        # Record all of the objectgroup contents for display when their tile comes up.
        objectgroup_contents = dict()
        for k, v in self.isometric_map.objectgroups.items():
            objectgroup_contents[k] = collections.defaultdict(list)
            for ob in v.contents:
                sx, sy = self.screen_coords(ob.x, ob.y, k.offsetx + v.offsetx, k.offsety + v.offsety)
                obkey = (self.map_x(sx, sy, return_int=True), self.map_y(sx, sy, return_int=True))
                objectgroup_contents[k][obkey].append(ob)

        while keep_going:
            # In order to allow smooth sub-tile movement of stuff, we have
            # to draw everything in a particular order.
            nuline = self.get_line(x0, y0, line_number, visible_area)
            line_cache.append(nuline)
            current_y_offset = self.isometric_map.layers[0].offsety
            current_line = len(line_cache) - 1

            for layer_num, layer in enumerate(self.isometric_map.layers):
                if current_line >= 0:
                    if line_cache[current_line]:
                        for x, y in line_cache[current_line]:
                            gid = layer[x, y]
                            tile_id = gid & NOT_ALL_FLAGS
                            if tile_id > 0:
                                my_tile = self.isometric_map.tilesets[tile_id]
                                sx, sy = self.screen_coords(x, y)
                                my_tile(self.screen, sx, sy + layer.offsety, gid & FLIPPED_HORIZONTALLY_FLAG,
                                        gid & FLIPPED_VERTICALLY_FLAG)

                            if current_line > 1 and layer in objectgroup_contents and (x - 1, y) in \
                                    objectgroup_contents[layer]:
                                # After drawing the terrain, draw any objects in the previous cell.
                                objectgroup_contents[layer][(x - 1, y)].sort(key=self.model_depth)
                                for ob in objectgroup_contents[layer][(x - 1, y)]:
                                    sx, sy = self.screen_coords(
                                        ob.x, ob.y,
                                        layer.offsetx + self.isometric_map.objectgroups[layer].offsetx,
                                        layer.offsety + self.isometric_map.objectgroups[layer].offsety
                                    )
                                    ob(self.screen, sx, sy, self.isometric_map)

                    elif line_cache[current_line] is None and layer == self.isometric_map.layers[-1]:
                        keep_going = False

                else:
                    break

                if layer.offsety < current_y_offset:
                    current_line -= 1
                    current_y_offset = layer.offsety

            mx = self.map_x(mouse_x, mouse_y)
            my = self.map_y(mouse_x, mouse_y)
            if self.isometric_map.on_the_map(mx, my):
                mydest = self.debug_sprite.bitmap.get_rect(midbottom=self.screen_coords(mx, my))
                self.debug_sprite.render(mydest, 0)

            line_number += 1

        self.phase = (self.phase + 1) % 600
        self._mouse_tile = (self.map_x(mouse_x, mouse_y), self.map_y(mouse_x, mouse_y))

        if self.postfx:
            self.postfx()

    def check_event(self, ev):
        if self.cursor:
            self.cursor.update(self, ev)
