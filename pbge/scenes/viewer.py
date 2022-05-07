import katagames_engine as kengi

pygame = kengi.pygame  # alias to keep on using pygame, easily

import collections
import weakref

from .. import wait_event, TIMEREVENT


SCROLL_STEP = 12

def anim_delay():
    while wait_event().type != TIMEREVENT:
        pass


FLIPPED_HORIZONTALLY_FLAG  = 0x80000000
FLIPPED_VERTICALLY_FLAG    = 0x40000000
FLIPPED_DIAGONALLY_FLAG    = 0x20000000
ROTATED_HEXAGONAL_120_FLAG = 0x10000000

NOT_ALL_FLAGS = ~(FLIPPED_HORIZONTALLY_FLAG | FLIPPED_VERTICALLY_FLAG | FLIPPED_DIAGONALLY_FLAG |
                  ROTATED_HEXAGONAL_120_FLAG)


class SceneView( object ):
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
        self.half_tile_width = isometric_map.tile_width // 2
        self.half_tile_height = isometric_map.tile_height // 2

        # _mouse_tile contains the actual tile the mouse is hovering over. However, in most cases what we really want
        # is the location of the mouse cursor. Time to make a property!
        self._mouse_tile = (-1,-1)

        self.postfx = postfx

        self.cursor = cursor

    @property
    def mouse_tile(self):
        if self.cursor:
            return self.cursor.x, self.cursor.y
        else:
            return self._mouse_tile

    def relative_x( self, x, y ):
        """Return the relative x position of this tile, ignoring offset."""
        return (x * self.half_tile_width) - (y * self.half_tile_width)

    def relative_y( self, x, y ):
        """Return the relative y position of this tile, ignoring offset."""
        return (y * self.half_tile_height) + (x * self.half_tile_height)

    def screen_coords(self, x, y):
        return (self.relative_x(x - 1, y - 1) + self.x_off, self.relative_y(x - 1, y - 1) + self.y_off)

    def map_x( self, sx, sy ):
        """Return the map x column for the given screen coordinates."""
        return int(float( sx - self.x_off ) / self.half_tile_width + float(sy - self.y_off) / self.half_tile_height - 1) // 2 - 1

    def fmap_x( self, sx, sy ):
        """Return the map x column for the given screen coordinates."""
        return (float( sx - self.x_off ) / self.half_tile_width + float(sy - self.y_off) / self.half_tile_height - 1) / 2 - 1

    def map_y( self, sx, sy ):
        """Return the map y row for the given screen coordinates."""
        return int(float( sy - self.y_off ) / self.half_tile_height - float(sx - self.x_off) / self.half_tile_width - 1) // 2

    def fmap_y( self, sx, sy ):
        """Return the map y row for the given screen coordinates."""
        return (float( sy - self.y_off ) / self.half_tile_height - float(sx - self.x_off) / self.half_tile_width - 1) / 2


    def check_origin( self ):
        """Make sure the offset point is within map boundaries."""
        if -self.x_off < self.relative_x(0 , self.isometric_map.height - 1):
            self.x_off = -self.relative_x(0, self.isometric_map.height - 1)
        elif -self.x_off > self.relative_x(self.isometric_map.width - 1 , 0):
            self.x_off = -self.relative_x(self.isometric_map.width - 1, 0)
        if -self.y_off < self.relative_y( 0 , 0 ):
            self.y_off = -self.relative_y( 0 , 0 )
        elif -self.y_off > self.relative_y(self.isometric_map.width - 1 , self.isometric_map.height - 1):
            self.y_off = -self.relative_y(self.isometric_map.width - 1, self.isometric_map.height - 1)

    def focus( self, x, y ):
        self.x_off = self.screen.get_width()//2 - self.relative_x( x,y )
        self.y_off = self.screen.get_height()//2 - self.relative_y( x,y )
        self.check_origin()

    def next_tile( self, x0,y0,x, y, line, sx, sy, screen_area ):
        """Locate the next map tile, moving left to right across the screen. """
        keep_going = True
        if (sx + self.tile_width) > (screen_area.x + screen_area.w):
            if ( sy+self.half_tile_height) > (screen_area.y + screen_area.h):
                keep_going = False
            x = x0 + line // 2
            y = y0 + ( line + 1 ) // 2
            line += 1
        else:
            x += 1
            y -= 1
        return x,y,line,keep_going

    def get_line(self, x0, y0, line_number, visible_area):
        mylist = list()
        x = x0 + line_number // 2
        y = y0 + (line_number + 1) // 2

        if self.relative_y(x,y) + self.y_off > visible_area.bottom:
            return ()

        while self.relative_x(x - 1, y - 1) + self.x_off < visible_area.right:
            if self.isometric_map.on_the_map(x,y):
                mylist.append((x,y))
            x += 1
            y -= 1
        return mylist

    def next_line(self):
        # Return the coordinates of the next line
        pass

    def handle_anim_sequence( self, record_anim=False ):
        # Disable widgets while animation playing.
        tick = 0
        while self.anim_list:
            should_delay = False
            self.anims.clear()
            for a in list(self.anim_list):
                if a.needs_deletion:
                    self.anim_list.remove( a )
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

    def PosToKey( self, pos ):
        # Convert the x,y coordinates to a model_map key...
        if pos:
            x,y = pos
            return ( int(round(x)), int(round(y)) )
        else:
            return "IT'S NOT ON THE MAP ALRIGHT?!"

    def model_depth( self, model ):
        return self.relative_y( model.pos[0], model.pos[1] )
    
    def __call__( self ):
        """Draws this mapview to the provided screen."""
        screen_area = self.screen.get_rect()
        mouse_x,mouse_y = pygame.mouse.get_pos()
        self.screen.fill( (0,0,0) )

        # Check for map scrolling, depending on mouse position.
        if mouse_x < 20:
            self.x_off += SCROLL_STEP
            self.check_origin()
        elif mouse_x > ( screen_area.right - 20 ):
            self.x_off -= SCROLL_STEP
            self.check_origin()
        if mouse_y < 20:
            self.y_off += SCROLL_STEP
            self.check_origin()
        elif mouse_y > ( screen_area.bottom - 20 ):
            self.y_off -= SCROLL_STEP
            self.check_origin()

        x,y = self.map_x(0,0)-2, self.map_y(0,0)-1
        x0,y0 = x,y
        keep_going = True
        line_number = 1
        line_cache = list()

        # The visible area describes the region of the map we need to draw. It is bigger than the physical screen
        # because we probably have to draw cells that are not fully on the map.
        visible_area = self.screen.get_rect()
        visible_area.inflate_ip(self.tile_width, self.isometric_map.tile_height)
        visible_area.h += self.isometric_map.tile_height - self.isometric_map.layers[-1].offsety

        # Record all of the isometric_map contents for display when their tile comes up.
        """
        self.modelmap.clear()
        self.uppermap.clear()
        self.undermap.clear()
        self.waypointmap.clear()
        for m in self.isometric_map.contents:
            if hasattr( m , 'render' ) and self.PosToKey(m.pos) in self.isometric_map.in_sight:
                d_pos = self.PosToKey(m.pos)
                if not m.hidden:
                    self.modelmap[d_pos].append(m)
                if self.isometric_map.model_altitude(m, *d_pos) >= 0:
                    self.uppermap[ d_pos ].append( m )
                else:
                    self.undermap[ d_pos ].append( m )
            elif isinstance( m, waypoints.Waypoint ) and m.name:
                # Nameless waypoints are hidden. They probably serve some
                # utility purpose, but the player doesn't have to know they're
                # there.
                self.waypointmap[m.pos].append(m)
        """

        while keep_going:
            # In order to allow smooth sub-tile movement of stuff, we have
            # to draw everything in a particular order.
            nuline = self.get_line(x0, y0, line_number, visible_area)
            line_cache.append(nuline)
            keep_going = bool(nuline)
            current_y_offset = self.isometric_map.layers[0].offsety
            current_line = len(line_cache) - 1

            for layer_num, layer in enumerate(self.isometric_map.layers):
                if current_line >= 0:
                    for x,y in line_cache[current_line]:
                        gid = layer[x, y]
                        tile_id = gid & NOT_ALL_FLAGS
                        if tile_id > 0:
                            my_tile = self.isometric_map.tilesets[tile_id]
                            sx, sy = self.screen_coords(x,y)
                            my_tile(self.screen, sx, sy + current_y_offset, gid & FLIPPED_HORIZONTALLY_FLAG,
                                    gid & FLIPPED_VERTICALLY_FLAG)
                else:
                    break

                if layer.offsety < current_y_offset:
                    current_line -= 1
                    current_y_offset = layer.offsety

            line_number += 1



        self.phase = ( self.phase + 1 ) % 600
        self._mouse_tile = (self.map_x(mouse_x,mouse_y),self.map_y(mouse_x,mouse_y))

        if self.postfx:
            self.postfx()

    def check_event(self, ev):
        if self.cursor:
            self.cursor.update(self, ev)
