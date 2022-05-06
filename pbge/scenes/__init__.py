""" Barebones scene handling for an isometric RPG. For game-specific data,
    either subclass the Scene or just declare whatever extra bits are needed.
"""

    # I feel like this unit isn't very Pythonic, since it's full of setters
    # and getters and various other walls to keep the user away from the
    # data.


from .. import image,KeyObject

import katagames_engine as kengi
pygame = kengi.pygame


Tilesets = kengi.tmx.data.Tilesets
Layers = kengi.tmx.data.Layers

import math
from . import movement, tileset
import weakref

from zlib import decompress
from base64 import b64decode

from xml.etree import ElementTree

import struct


class PlaceableThing( KeyObject ):
    """A thing that can be placed on the map."""
    # By default, a hidden thing just isn't displayed.
    def __init__(self, hidden=False, **keywords):
        self.hidden = hidden
        self.pos = None
        self.offset_pos = None
        super(PlaceableThing, self).__init__(**keywords)
    def place( self, scene, pos=None, team=None ):
        if hasattr( self, "container" ) and self.container:
            self.container.remove( self )
        scene.contents.append( self )
        self.pos = pos
        if team:
            scene.local_teams[self] = team
    imagename = ""
    colors = None
    imageheight = 64
    imagewidth = 64
    frame = 0
    altitude = None
    def get_sprite(self):
        """Generate the sprite for this thing."""
        return image.Image(self.imagename,self.imagewidth,self.imageheight,self.colors)
    def render( self, foot_pos, view ):
        if self.hidden:
            self.render_hidden( foot_pos, view )
        else:
            self.render_visible( foot_pos, view )
    def render_visible( self, foot_pos, view ):
        spr = view.get_sprite(self)
        mydest = spr.get_rect(self.frame)
        mydest.midbottom = foot_pos
        if self.offset_pos:
            mydest.x += self.offset_pos[0]
            mydest.y += self.offset_pos[1]
        spr.render( mydest, self.frame )
    def render_hidden( self, foot_pos, view ):
        pass
    def move( self, dest, view, speed=0.25 ):
        view.anim_list.append( animobs.MoveModel( self, dest=dest, speed=speed))
    # Define an update_graphics method if you need to change this object's appearance
    # after invoking effects.



from . import pathfinding
from . import pfov
from . import terrain
from . import viewer
from . import animobs
from . import targetarea
from . import waypoints
from . import areaindicator
from . import mapcursor


class IsometricLayer:
    def __init__(self, name, visible, map):
        self.name = name
        self.visible = visible
        self.position = (0, 0)
        # TODO get from TMX?
        self.tile_width = map.tile_width
        self.tile_height = map.tile_height
        self.width = map.width
        self.height = map.height
        self.tilesets = map.tilesets
        self.group = pygame.sprite.Group()
        self.properties = {}
        self.cells = {}

    def __repr__(self):
        return '<Layer "%s" at 0x%x>' % (self.name, id(self))

    def __getitem__(self, pos):
        return self.cells.get(pos)

    def __setitem__(self, pos, value):
        self.cells[pos] = value

    @classmethod
    def fromxml(cls, tag, givenmap):
        layer = cls(tag.attrib['name'], int(tag.attrib.get('visible', 1)), givenmap)

        data = tag.find('data')
        if data is None:
            raise ValueError('layer %s does not contain <data>' % layer.name)

        data = data.text.strip()
        data = data.encode()  # Convert to bytes
        # Decode from base 64 and decompress via zlib
        data = decompress(b64decode(data))
        data = struct.unpack('<%di' % (len(data) / 4,), data)
        assert len(data) == layer.width * layer.height
        for idx, gid in enumerate(data):
            if gid >= 1:  # otherwise its not set
                tile = givenmap.tilesets[gid]
                x = idx % layer.width
                y = idx // layer.width
                layer.cells[x, y] = tile

        return layer

    def update(self, dt, *args):
        pass

    def set_view(self, x, y, w, h, viewport_ox=0, viewport_oy=0):
        self.view_x, self.view_y = x, y
        self.view_w, self.view_h = w, h
        x -= viewport_ox
        y -= viewport_oy
        self.position = (x, y)

    def draw(self, surface):
        """
        Draw this layer, limited to the current viewport, to the Surface.
        """
        ox, oy = self.position
        w, h = self.view_w, self.view_h
        for x in range(ox, ox + w + self.tile_width, self.tile_width):
            i = x // self.tile_width
            for y in range(oy, oy + h + self.tile_height, self.tile_height):
                j = y // self.tile_height
                if (i, j) not in self.cells:
                    continue
                cell = self.cells[i, j]
                surface.blit(cell.tile.surface, (cell.px - ox, cell.py - oy))

    def find(self, *properties):
        """
        Find all cells with the given properties set.
        """
        r = []
        for propname in properties:
            for cell in list(self.cells.values()):
                if cell and propname in cell:
                    r.append(cell)
        return r

    def match(self, **properties):
        """
        Find all cells with the given properties set to the given values.
        """
        r = []
        for propname in properties:
            for cell in list(self.cells.values()):
                if propname not in cell:
                    continue
                if properties[propname] == cell[propname]:
                    r.append(cell)
        return r

    def collide(self, rect, propname):
        """
        Find all cells the rect is touching that have the indicated property
        name set.
        """
        r = []
        for cell in self.get_in_region(rect.left, rect.top, rect.right,
                                       rect.bottom):
            if not cell.intersects(rect):
                continue
            if propname in cell:
                r.append(cell)
        return r

    def get_in_region(self, x1, y1, x2, y2):
        """
        Return cells (in [column][row]) that are within the map-space
        pixel bounds specified by the bottom-left (x1, y1) and top-right
        (x2, y2) corners.
        Return a list of Cell instances.
        """
        i1 = max(0, x1 // self.tile_width)
        j1 = max(0, y1 // self.tile_height)
        i2 = min(self.width, x2 // self.tile_width + 1)
        j2 = min(self.height, y2 // self.tile_height + 1)
        return [self.cells[i, j]
                for i in range(int(i1), int(i2))
                for j in range(int(j1), int(j2))
                if (i, j) in self.cells]

    def get_at(self, x, y):
        """
        Return the cell at the nominated (x, y) coordinate.
        Return a Cell instance or None.
        """
        i = x // self.tile_width
        j = y // self.tile_height
        return self.cells.get((i, j))

    def neighbors(self, index):
        """
        Return the indexes of the valid (ie. within the map) cardinal (ie.
        North, South, East, West) neighbors of the nominated cell index.
        Returns a list of 2-tuple indexes.
        """
        i, j = index
        n = []
        if i < self.width - 1:
            n.append((i + 1, j))
        if i > 0:
            n.append((i - 1, j))
        if j < self.height - 1:
            n.append((i, j + 1))
        if j > 0:
            n.append((i, j - 1))
        return n


class IsometricMap():
    def __init__(self):
        self.px_width = 0
        self.px_height = 0
        self.tile_width = 0
        self.tile_height = 0
        self.width = 0
        self.height = 0
        self.properties = {}
        self.layers = Layers()
        self.tilesets = Tilesets()

    @classmethod
    def load(cls, filename, hack_tsxfile=None, hack_ts=None):
        with open(filename) as f:
            tminfo_tree = ElementTree.fromstring(f.read())

        # get most general map informations and create a surface
        tilemap = cls()

        tilemap.width = int(tminfo_tree.attrib['width'])
        tilemap.height = int(tminfo_tree.attrib['height'])
        tilemap.tile_width = int(tminfo_tree.attrib['tilewidth'])
        tilemap.tile_height = int(tminfo_tree.attrib['tileheight'])
        tilemap.px_width = tilemap.width * tilemap.tile_width
        tilemap.px_height = tilemap.height * tilemap.tile_height

        for tag in tminfo_tree.findall('tileset'):
            tilemap.tilesets.add(
                tileset.IsometricTileset.fromxml(tag, hacksource=hack_tsxfile, hacktileset=hack_ts)
                # hacks work only if no more than 1 ts
            )
            print('tilesets added')

        for tag in tminfo_tree.findall('layer'):
            layer = IsometricLayer.fromxml(tag, tilemap)
            tilemap.layers.add_named(layer, layer.name)


        return tilemap

class Scene( object ):
    DELTA8 = ( (-1,-1), (0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1) )
    ANGDIR = ( (-1,-1), (0,-1), (1,-1), (1,0), (1,1), (0,1), (-1,1), (-1,0) )
    def __init__(self,width=128,height=128,name="",player_team=None,exit_scene_wp=None):
        self.name = name
        self.width = width
        self.height = height
        self.player_team = player_team

        # The data dict is primarily used to hold frames for TerrSetTerrain
        # tiles, but I guess you could put anything you want in there.
        self.data = dict()
        self.in_sight = set()

        self.contents = list()

        self.last_updated = 0
        self.exit_scene_wp = exit_scene_wp

        # Fill the map with empty tiles
        self._map = None

        self.local_teams = dict()


    def on_the_map( self , x , y ):
        # Returns true if on the map, false otherwise
        return ( ( x >= 0 ) and ( x < self.width ) and ( y >= 0 ) and ( y < self.height ) )


    def get_floor( self, x, y ):
        """Safely return floor of tile x,y, or None if off map."""
        if self.on_the_map(x,y):
            return self._map[x][y].floor
        else:
            return None

    def get_wall( self, x, y ):
        """Safely return wall of tile x,y, or None if off map."""
        if self.on_the_map(x,y):
            return self._map[x][y].wall
        else:
            return None

    def set_wall( self, x, y, terr ):
        """Safely set wall of tile x,y."""
        if self.on_the_map(x,y):
            self._map[x][y].wall = terr

    def get_decor( self, x, y ):
        """Safely return decor of tile x,y, or None if off map."""
        if self.on_the_map(x,y):
            return self._map[x][y].decor
        else:
            return None

    def set_decor( self, x, y, terr ):
        """Safely set decor of tile x,y."""
        if self.on_the_map(x,y):
            self._map[x][y].decor = terr

    def get_visible( self, x, y ):
        """Safely return visibility status of tile x,y, or None if off map."""
        if self.on_the_map(x,y):
            return self._map[x][y].visible
        else:
            return False

    def set_visible( self, x, y, v=True ):
        """Safely return visibility status of tile x,y, or None if off map."""
        if self.on_the_map(x,y):
            self._map[x][y].visible = v


    def tile_blocks_vision( self, x, y ):
        if self.on_the_map(x,y):
            return self._map[x][y].blocks_vision()
        else:
            return True

    def tile_blocks_walking( self, x, y ):
        if self.on_the_map(x,y):
            return self._map[x][y].blocks_walking()
        else:
            return True

    def tile_blocks_movement( self, x, y, mmode ):
        if self.on_the_map(x,y):
            return self._map[x][y].blocks_movement(mmode)
        else:
            return True


    def distance( self, pos1, pos2 ):
        return round( math.sqrt( ( pos1[0]-pos2[0] )**2 + ( pos1[1]-pos2[1] )**2 ) )

    def __str__( self ):
        if self.name:
            return self.name
        else:
            return repr( self )

    def wall_wont_block( self, x, y ):
        """Return True if a wall placed here won't block movement."""
        if self.tile_blocks_walking(x,y):
            # This is a wall now. Changing it from a wall to a wall really won't
            # change anything, as should be self-evident.
            return True
        else:
            # Adding a wall will block a passage if there are two or more spaces
		    # in the eight surrounding tiles which are separated by walls.
            was_a_space = not self.tile_blocks_walking(x-1,y)
            n = 0
            for a in self.ANGDIR:
                is_a_space = not self.tile_blocks_walking(x+a[0],y+a[1])
                if is_a_space != was_a_space:
                    # We've gone from wall to space or vice versa.
                    was_a_space = is_a_space
                    n += 1
            return n <= 2

    def fill( self, dest, floor=-1, wall=-1, decor=-1 ):
        # Fill the provided area with the provided terrain.
        for x in range( dest.x, dest.x + dest.width ):
            for y in range( dest.y, dest.y + dest.height ):
                if self.on_the_map(x,y):
                    if floor != -1:
                        self._map[x][y].floor = floor
                    if wall != -1:
                        self._map[x][y].wall = wall
                    if decor != -1:
                        self._map[x][y].decor = decor

    def fill_blob( self, dest, floor=-1, wall=-1, decor=-1 ):
        # Fill the provided area with the provided terrain.
        midpoint = dest.center
        for x in range( dest.x, dest.x + dest.width ):
            for y in range( dest.y, dest.y + dest.height ):
                if self.on_the_map(x,y) and self.distance((x,y),midpoint) <= dest.width//2:
                    if floor != -1:
                        self._map[x][y].floor = floor
                    if wall != -1:
                        self._map[x][y].wall = wall
                    if decor != -1:
                        self._map[x][y].decor = decor

    def get_move_cost( self, a, b, movemode ):
        # a and b should be adjacent tiles.
        if self.on_the_map(b[0],b[1]) and self.on_the_map(a[0],a[1]):
            base_cost = 5 * (abs(a[0]-b[0]) + abs(a[1]-b[1]) + 1)
            # Modify by terrain.
            base_cost *= self._map[b[0]][b[1]].get_movement_multiplier(movemode)
            # Modify for climbing.
            if (movemode.climb_penalty > 1.0) and movemode.altitude is not None and (max(self._map[b[0]][b[1]].altitude(),movemode.altitude)>max(self._map[a[0]][a[1]].altitude(),movemode.altitude)):
                base_cost *= movemode.climb_penalty
            return int(base_cost)
        else:
            return 100
    def tile_altitude(self,x,y):
        if self.on_the_map(x,y):
            return self._map[int(x)][int(y)].altitude()
        else:
            return 0
    def model_altitude( self, m,x,y ):
        if not hasattr(m,"mmode") or not m.mmode or m.mmode.altitude is None:
            return self.tile_altitude(x,y)
        else:
            return max(self._map[x][y].altitude(),m.mmode.altitude)

    def get_cover(self,x1,y1,x2,y2,vmode=movement.Vision):
        # x1,y1 is the viewer, x2,y2 is the target
        my_line = animobs.get_line(x1,y1,x2,y2)
        it = 0
        for p in my_line[1:]:
            if self.on_the_map(*p):
                it += self._map[p[0]][p[1]].get_cover(vmode)
        return it

    def get_waypoint(self,pos):
        # Return the first waypoint found at this position. If more than one
        # waypoint is there, tough cookies.
        for a in self.contents:
            if a.pos == pos and isinstance(a,waypoints.Waypoint):
                return a

    def get_waypoints(self,pos):
        # Return all of the waypoints found at this position.
        return [a for a in self.contents if isinstance(a,waypoints.Waypoint) and a.pos == pos]

    def get_bumpable(self,pos):
        # Return the first bumpable found at this position. If more than one
        # bumpable is there, tough cookies.
        for a in self.contents:
            if hasattr(a,"pos") and a.pos == pos and hasattr(a,'bump'):
                return a

    def get_bumpables(self,pos):
        # Return all of the bumpables found at this position.
        return [a for a in self.contents if hasattr(a,"pos") and a.pos == pos and hasattr(a,'bump')]

    def get_root_scene(self):
        if hasattr(self, "container") and self.container and hasattr(self.container.owner, "get_root_scene"):
            return self.container.owner.get_root_scene()
        else:
            return self

