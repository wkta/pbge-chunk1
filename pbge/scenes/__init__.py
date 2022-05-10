""" Barebones isometric_map handling for an isometric RPG. For game-specific data,
    either subclass the Scene or just declare whatever extra bits are needed.
"""

# I feel like this unit isn't very Pythonic, since it's full of setters
# and getters and various other walls to keep the user away from the
# data.


from .. import image, KeyObject

import katagames_engine as kengi

pygame = kengi.pygame

Tilesets = kengi.tmx.data.Tilesets
Layers = kengi.tmx.data.Layers

import math
from . import movement, tileset
import json

from zlib import decompress
from base64 import b64decode

from xml.etree import ElementTree

import struct


class IsometricMapObject(KeyObject):
    """A thing that can be placed on the map."""
    def __init__(self, **keywords):
        self.name = ""
        self.type = ""
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.gid = 0
        self.visible = 1
        super().__init__(**keywords)

    def move(self, dest, view, speed=0.25):
        view.anim_list.append(animobs.MoveModel(self, dest=dest, speed=speed))

    def __call__(self, dest_surface, sx, sy, mymap):
        if self.gid:
            tile_id = self.gid & tileset.NOT_ALL_FLAGS
            if tile_id > 0:
                my_tile = mymap.tilesets[tile_id]
                my_tile(dest_surface, sx, sy, self.gid & tileset.FLIPPED_HORIZONTALLY_FLAG,
                        self.gid & tileset.FLIPPED_VERTICALLY_FLAG)

    @staticmethod
    def deweirdify_coordinates(tx, ty, givenlayer):
        # It took ages to figure out the coordinate system that Tiled uses for objects on isometric maps. At first I
        # thought the pixel coordinate origin would be the upper left corner of the map's bounding box. It isn't.
        # In fact, it isn't a normal cartesian coordinate system at all. The pixel x,y values are the cell index
        # multiplied by the cell height. I cannot think of any situation for which this would be a useful way to store
        # pixel coordinates, but there you go.
        #
        # This function takes the Tiled pixel coordinates and changes them to tilemap cell coordinates. Feel free to
        # delete this long rant of a comment. Or leave it as a warning to others. I am just glad to finally understand
        # what's going on.

        mx = tx/givenlayer.tile_height - 1.0
        my = ty/givenlayer.tile_height - 1.0
        return mx, my

    @classmethod
    def fromxml(cls, tag, objectgroup, givenlayer):
        myob = cls()
        myob.name = tag.attrib.get("name")
        myob.type = tag.attrib.get("type")
        # Convert the x,y pixel coordinates to x,y map coordinates.
        x = float(tag.attrib.get("x", 0))
        y = float(tag.attrib.get("y", 0))
        myob.x, myob.y = cls.deweirdify_coordinates(x, y, givenlayer)
        myob.gid = int(tag.attrib.get("gid"))
        myob.visible = int(tag.attrib.get("visible",1))
        return myob

    @classmethod
    def fromjson(cls, jdict, objectgroup, givenlayer):
        myob = cls()
        myob.name = jdict.get("name")
        myob.type = jdict.get("type")
        # Convert the x,y pixel coordinates to x,y map coordinates.
        x = jdict.get("x", 0)
        y = jdict.get("y", 0)
        myob.x, myob.y = cls.deweirdify_coordinates(x, y, givenlayer)
        myob.gid = jdict.get("gid")
        myob.visible = jdict.get("visible")
        return myob


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
    def __init__(self, name, visible, map, offsetx=0, offsety=0):
        self.name = name
        self.visible = visible

        self.tile_width = map.tile_width
        self.tile_height = map.tile_height

        self.width = map.width
        self.height = map.height

        self.offsetx = offsetx
        self.offsety = offsety

        self.properties = {}
        self.cells = list()

    def __repr__(self):
        return '<Layer "%s" at 0x%x>' % (self.name, id(self))

    @classmethod
    def emptylayer(cls, name, givenmap):
        layer = cls(
            name, 0, givenmap, 0, 0
        )

        layer.cells = [0,] * givenmap.height * givenmap.width

        return layer

    @classmethod
    def fromxml(cls, tag, givenmap):
        layer = cls(
            tag.attrib['name'], int(tag.attrib.get('visible', 1)), givenmap,
            int(tag.attrib.get('offsetx', 0)), int(tag.attrib.get('offsety', 0))
        )

        data = tag.find('data')
        if data is None:
            raise ValueError('layer %s does not contain <data>' % layer.name)

        data = data.text.strip()
        data = data.encode()  # Convert to bytes
        # Decode from base 64 and decompress via zlib
        data = decompress(b64decode(data))

        # I ran a test today and there's a slight speed advantage in leaving the cells as a list. It's not a big
        # advantage, but it's just as easy for now to leave the data as it is.
        #
        # I'm changing to a list from a tuple in case destructible terrain or modifiable terrain (such as doors) are
        # wanted in the future.
        layer.cells = list(struct.unpack('<%di' % (len(data) / 4,), data))
        assert len(layer.cells) == layer.width * layer.height

        return layer

    @classmethod
    def fromjson(cls, jdict, givenmap):
        layer = cls(
            jdict['name'], jdict.get('visible', True), givenmap,
            jdict.get('offsetx', 0), jdict.get('offsety', 0)
        )

        data = jdict.get('data')
        if data is None:
            raise ValueError('layer %s does not contain <data>' % layer.name)

        data = data.strip()
        data = data.encode()  # Convert to bytes
        # Decode from base 64 and decompress via zlib
        data = decompress(b64decode(data))

        # I ran a test today and there's a slight speed advantage in leaving the cells as a list. It's not a big
        # advantage, but it's just as easy for now to leave the data as it is.
        #
        # I'm changing to a list from a tuple in case destructible terrain or modifiable terrain (such as doors) are
        # wanted in the future.
        layer.cells = list(struct.unpack('<%di' % (len(data) / 4,), data))
        assert len(layer.cells) == layer.width * layer.height

        return layer

    def __len__(self):
        return self.height * self.width

    def _pos_to_index(self, x, y):
        return y * self.width + x

    def __getitem__(self, key):
        x, y = key
        i = self._pos_to_index(x, y)
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.cells[i]

    def __setitem__(self, pos, value):
        x, y = pos
        i = self._pos_to_index(x, y)
        if 0 <= x < self.width and 0 <= y < self.height:
            self.cells[i] = value


class ObjectGroup():
    def __init__(self, name, visible, offsetx, offsety):
        self.name = name
        self.visible = visible
        self.offsetx = offsetx
        self.offsety = offsety

        self.contents = list()

    @classmethod
    def fromxml(cls, tag, givenlayer, object_fun=None):
        mygroup = cls(
            tag.attrib['name'], int(tag.attrib.get('visible', 1)),
            int(tag.attrib.get('offsetx', 0)), int(tag.attrib.get('offsety', 0))
        )

        for t in tag:
            if t.tag == "object":
                if object_fun:
                    mygroup.contents.append(IsometricMapObject.fromxml(t))
                elif "gid" in t.attrib:
                    mygroup.contents.append(IsometricMapObject.fromxml(
                        t, mygroup, givenlayer
                    ))

        return mygroup

    @classmethod
    def fromjson(cls, jdict, givenlayer, object_fun=None):
        mygroup = cls(
            jdict.get('name'), jdict.get('visible', True),
            jdict.get('offsetx', 0), jdict.get('offsety', 0)
        )

        if "objects" in jdict:
            for t in jdict["objects"]:
                if object_fun:
                    mygroup.contents.append(IsometricMapObject.fromxml(t))
                elif "gid" in t.attrib:
                    mygroup.contents.append(IsometricMapObject.fromjson(
                        t, mygroup, givenlayer
                    ))

        return mygroup


class IsometricMap():
    def __init__(self):
        self.tile_width = 0
        self.tile_height = 0
        self.width = 0
        self.height = 0
        self.properties = {}
        self.layers = list()
        self.tilesets = Tilesets()
        self.objectgroups = dict()

    @classmethod
    def load_tmx(cls, filename, object_fun=None):
        # object_fun is a function that can parse a dict describing an object.
        # If None, the only objects that can be loaded are terrain objects.
        with open(filename) as f:
            tminfo_tree = ElementTree.fromstring(f.read())

        # get most general map informations and create a surface
        tilemap = cls()

        tilemap.width = int(tminfo_tree.attrib['width'])
        tilemap.height = int(tminfo_tree.attrib['height'])
        tilemap.tile_width = int(tminfo_tree.attrib['tilewidth'])
        tilemap.tile_height = int(tminfo_tree.attrib['tileheight'])

        for tag in tminfo_tree.findall('tileset'):
            tilemap.tilesets.add(
                tileset.IsometricTileset.fromxml(tag)
                # hacks work only if no more than 1 ts
            )

        for tag in tminfo_tree:
            if tag.tag == 'layer':
                layer = IsometricLayer.fromxml(tag, tilemap)
                tilemap.layers.append(layer)
            elif tag.tag == "objectgroup":
                if not tilemap.layers:
                    # If the first layer on the map is an objectgroup, this is gonna be a problem. Without
                    # a frame of reference, we won't be able to know what tile the object is in, and that is going
                    # to be important information. So, we add an empty layer with no offsets to act as this
                    # objectgroup's frame of reference.
                    tilemap.layers.append(IsometricLayer.emptylayer("The Mysterious Empty Layer", tilemap))
                tilemap.objectgroups[tilemap.layers[-1]] = ObjectGroup.fromxml(tag, tilemap.layers[-1], object_fun)

        return tilemap

    @classmethod
    def load_json(cls, filename, object_fun=None):
        # object_fun is a function that can parse a dict describing an object.
        # If None, the only objects that can be loaded are terrain objects.

        with open(filename) as f:
            jdict = json.load(f)

        # get most general map informations and create a surface
        tilemap = cls()

        tilemap.width = jdict['width']
        tilemap.height = jdict['height']
        tilemap.tile_width = jdict['tilewidth']
        tilemap.tile_height = jdict['tileheight']

        for tag in jdict['tilesets']:
            tilemap.tilesets.add(
                tileset.IsometricTileset.fromjson(tag)
            )

        for tag in jdict["layers"]:
            if tag["type"] == 'tilelayer':
                layer = IsometricLayer.fromjson(tag, tilemap)
                tilemap.layers.append(layer)
            elif tag["type"] == "objectgroup":
                if not tilemap.layers:
                    # See above comment for why I'm adding an empty layer. TLDR: the objects need a reference frame.
                    tilemap.layers.append(IsometricLayer.emptylayer("The Mysterious Empty Layer", tilemap))
                tilemap.objectgroups[tilemap.layers[-1]] = ObjectGroup.fromjson(tag, tilemap.layers[-1], object_fun)

        return tilemap

    @classmethod
    def load(cls, filename, object_fun=None):
        if filename.endswith(("tmx", "xml")):
            return cls.load_tmx(filename, object_fun)
        elif filename.endswith(("tmj", "json")):
            return cls.load_json(filename, object_fun)

    def on_the_map(self, x, y):
        # Returns true if (x,y) is on the map, false otherwise
        return (x >= 0) and (x < self.width) and (y >= 0) and (y < self.height)


class OldSceneClass(object):
    # Just gonna keep this here for a bit while I see what methods need to be taken from it.
    DELTA8 = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
    ANGDIR = ((-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0))

    def __init__(self, width=128, height=128, name="", player_team=None, exit_scene_wp=None):
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

    def tile_blocks_vision(self, x, y):
        if self.on_the_map(x, y):
            return self._map[x][y].blocks_vision()
        else:
            return True

    def tile_blocks_walking(self, x, y):
        if self.on_the_map(x, y):
            return self._map[x][y].blocks_walking()
        else:
            return True

    def tile_blocks_movement(self, x, y, mmode):
        if self.on_the_map(x, y):
            return self._map[x][y].blocks_movement(mmode)
        else:
            return True

    def distance(self, pos1, pos2):
        return round(math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2))

    def __str__(self):
        if self.name:
            return self.name
        else:
            return repr(self)

    def wall_wont_block(self, x, y):
        """Return True if a wall placed here won't block movement."""
        if self.tile_blocks_walking(x, y):
            # This is a wall now. Changing it from a wall to a wall really won't
            # change anything, as should be self-evident.
            return True
        else:
            # Adding a wall will block a passage if there are two or more spaces
            # in the eight surrounding tiles which are separated by walls.
            was_a_space = not self.tile_blocks_walking(x - 1, y)
            n = 0
            for a in self.ANGDIR:
                is_a_space = not self.tile_blocks_walking(x + a[0], y + a[1])
                if is_a_space != was_a_space:
                    # We've gone from wall to space or vice versa.
                    was_a_space = is_a_space
                    n += 1
            return n <= 2

    def fill(self, dest, floor=-1, wall=-1, decor=-1):
        # Fill the provided area with the provided terrain.
        for x in range(dest.x, dest.x + dest.width):
            for y in range(dest.y, dest.y + dest.height):
                if self.on_the_map(x, y):
                    if floor != -1:
                        self._map[x][y].floor = floor
                    if wall != -1:
                        self._map[x][y].wall = wall
                    if decor != -1:
                        self._map[x][y].decor = decor

    def fill_blob(self, dest, floor=-1, wall=-1, decor=-1):
        # Fill the provided area with the provided terrain.
        midpoint = dest.center
        for x in range(dest.x, dest.x + dest.width):
            for y in range(dest.y, dest.y + dest.height):
                if self.on_the_map(x, y) and self.distance((x, y), midpoint) <= dest.width // 2:
                    if floor != -1:
                        self._map[x][y].floor = floor
                    if wall != -1:
                        self._map[x][y].wall = wall
                    if decor != -1:
                        self._map[x][y].decor = decor

    def get_move_cost(self, a, b, movemode):
        # a and b should be adjacent tiles.
        if self.on_the_map(b[0], b[1]) and self.on_the_map(a[0], a[1]):
            base_cost = 5 * (abs(a[0] - b[0]) + abs(a[1] - b[1]) + 1)
            # Modify by terrain.
            base_cost *= self._map[b[0]][b[1]].get_movement_multiplier(movemode)
            # Modify for climbing.
            if (movemode.climb_penalty > 1.0) and movemode.altitude is not None and (
                    max(self._map[b[0]][b[1]].altitude(), movemode.altitude) > max(self._map[a[0]][a[1]].altitude(),
                                                                                   movemode.altitude)):
                base_cost *= movemode.climb_penalty
            return int(base_cost)
        else:
            return 100

    def tile_altitude(self, x, y):
        if self.on_the_map(x, y):
            return self._map[int(x)][int(y)].altitude()
        else:
            return 0

    def model_altitude(self, m, x, y):
        if not hasattr(m, "mmode") or not m.mmode or m.mmode.altitude is None:
            return self.tile_altitude(x, y)
        else:
            return max(self._map[x][y].altitude(), m.mmode.altitude)

    def get_cover(self, x1, y1, x2, y2, vmode=movement.Vision):
        # x1,y1 is the viewer, x2,y2 is the target
        my_line = animobs.get_line(x1, y1, x2, y2)
        it = 0
        for p in my_line[1:]:
            if self.on_the_map(*p):
                it += self._map[p[0]][p[1]].get_cover(vmode)
        return it

    def get_waypoint(self, pos):
        # Return the first waypoint found at this position. If more than one
        # waypoint is there, tough cookies.
        for a in self.contents:
            if a.pos == pos and isinstance(a, waypoints.Waypoint):
                return a

    def get_waypoints(self, pos):
        # Return all of the waypoints found at this position.
        return [a for a in self.contents if isinstance(a, waypoints.Waypoint) and a.pos == pos]

    def get_bumpable(self, pos):
        # Return the first bumpable found at this position. If more than one
        # bumpable is there, tough cookies.
        for a in self.contents:
            if hasattr(a, "pos") and a.pos == pos and hasattr(a, 'bump'):
                return a

    def get_bumpables(self, pos):
        # Return all of the bumpables found at this position.
        return [a for a in self.contents if hasattr(a, "pos") and a.pos == pos and hasattr(a, 'bump')]

    def get_root_scene(self):
        if hasattr(self, "container") and self.container and hasattr(self.container.owner, "get_root_scene"):
            return self.container.owner.get_root_scene()
        else:
            return self
