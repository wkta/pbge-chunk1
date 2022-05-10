import katagames_engine as kengi
pygame = kengi.pygame

from pbge import image

from xml.etree import ElementTree
import json

import os

FLIPPED_HORIZONTALLY_FLAG  = 0x80000000
FLIPPED_VERTICALLY_FLAG    = 0x40000000
FLIPPED_DIAGONALLY_FLAG    = 0x20000000
ROTATED_HEXAGONAL_120_FLAG = 0x10000000

NOT_ALL_FLAGS = 0x0FFFFFFF


class IsometricTile():
    def __init__(self, id, tile_surface, hflip, vflip):
        self.id = id
        self.tile_surface = tile_surface
        if hflip:
            self.hflip_surface = pygame.transform.flip(tile_surface, True, False).convert_alpha()
            self.hflip_surface.set_colorkey(tile_surface.get_colorkey(), tile_surface.get_flags())
        else:
            self.hflip_surface = None

        if vflip:
            self.vflip_surface = pygame.transform.flip(tile_surface, False, True).convert_alpha()
            self.vflip_surface.set_colorkey(tile_surface.get_colorkey(), tile_surface.get_flags())
        else:
            self.vflip_surface = None

        if hflip and vflip:
            self.hvflip_surface = pygame.transform.flip(tile_surface, True, True).convert_alpha()
            self.hvflip_surface.set_colorkey(tile_surface.get_colorkey(), tile_surface.get_flags())
        else:
            self.hvflip_surface = None

    def __call__(self, dest_surface, x, y, hflip=False, vflip=False):
        if hflip and vflip:
            surf = self.hvflip_surface
        elif hflip:
            surf = self.hflip_surface
        elif vflip:
            surf = self.vflip_surface
        else:
            surf = self.tile_surface
        mydest = surf.get_rect(midbottom=(x,y))
        dest_surface.blit(surf, mydest)

    def __repr__(self):
        return '<Tile {}>'.format(self.id)


class IsometricTileset:
    """
    Based on the Tileset class from katagames_engine/_sm_shelf/tmx/data.py, but modified for the needs of isometric
    maps. Or at least the needs of this particular isometric map.
    """

    def __init__(self, name, tile_width, tile_height, firstgid):
        self.name = name
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.firstgid = firstgid

        self.hflip = False
        self.vflip = False

        self.tiles = []
        self.properties = {}

    def get_tile(self, gid):
        return self.tiles[gid - self.firstgid]

    def add_image(self, source, num_tiles):
        # TODO: Make this bit compatible with Kenji.
        myimage = image.Image(os.path.join("assets", source), self.tile_width, self.tile_height)
        for t in range(num_tiles):
            self.tiles.append(IsometricTile(t+1, myimage.get_subsurface(t), self.hflip, self.vflip ))

    @classmethod
    def fromxml(cls, tag, firstgid=None):
        print('fromxml (isometrically)')
        if 'source' in tag.attrib:
            # Instead of a tileset proper, we have been handed an external tileset tag from inside a map file.
            # Load the external tileset and continue on as if nothing had happened.
            firstgid = int(tag.attrib['firstgid'])
            srcc = tag.attrib['source']

            #TODO: Another direct disk access here.
            if srcc.endswith(("tsx","xml")):
                with open(os.path.join("assets", srcc)) as f:
                    print('opened ', srcc)
                    tag = ElementTree.fromstring(f.read())
            elif srcc.endswith(("tsj","json")):
                with open(os.path.join("assets", srcc)) as f:
                    jdict = json.load(f)
                return cls.fromjson(jdict, firstgid)

        name = tag.attrib['name']
        if firstgid is None:
            firstgid = int(tag.attrib['firstgid'])
        tile_width = int(tag.attrib['tilewidth'])
        tile_height = int(tag.attrib['tileheight'])
        num_tiles = int(tag.attrib['tilecount'])

        tileset = cls(name, tile_width, tile_height, firstgid)

        # TODO: The transformations must be registered before any of the tiles. Is there a better way to do this
        # than iterating through the list twice? I know this is a minor thing but it bothers me.
        for c in tag:  # .getchildren():
            if c.tag == "transformations":
                tileset.vflip = int(c.attrib.get("vflip", 0)) == 1
                tileset.hflip = int(c.attrib.get("hflip", 0)) == 1
                print("Flip values: v={} h={}".format(tileset.vflip, tileset.hflip))


        for c in tag:  # .getchildren():
            #TODO: The tileset can only contain an "image" tag or multiple "tile" tags; it can't combine the two.
            # This should be enforced. For now, I'm just gonna support spritesheet tiles.
            if c.tag == "image":
                # create a tileset
                arg_sheet = c.attrib['source']
                tileset.add_image(arg_sheet, num_tiles)

        return tileset

    @classmethod
    def fromjson(cls, jdict, firstgid=None):
        print('fromjson (isometrically)')
        if 'source' in jdict:
            firstgid = int(jdict['firstgid'])
            srcc = jdict['source']

            #TODO: Another direct disk access here.
            if srcc.endswith(("tsx","xml")):
                with open(os.path.join("assets", srcc)) as f:
                    print('opened ', srcc)
                    tag = ElementTree.fromstring(f.read())
                    return cls.fromxml(tag, firstgid)
            elif srcc.endswith(("tsj","json")):
                with open(os.path.join("assets", srcc)) as f:
                    jdict = json.load(f)

        name = jdict['name']
        if firstgid is None:
            firstgid = int(jdict.get('firstgid', 1))
        tile_width = int(jdict['tilewidth'])
        tile_height = int(jdict['tileheight'])
        num_tiles = int(jdict['tilecount'])

        tileset = cls(name, tile_width, tile_height, firstgid)

        if "transformations" in jdict:
            c = jdict["transformations"]
            tileset.vflip = int(c.get("vflip", 0)) == 1
            tileset.hflip = int(c.get("hflip", 0)) == 1

        #TODO: The tileset can only contain an "image" tag or multiple "tile" tags; it can't combine the two.
        # This should be enforced. For now, I'm just gonna support spritesheet tiles.

        # create a tileset
        arg_sheet = jdict['image']
        tileset.add_image(arg_sheet, num_tiles)

        return tileset


