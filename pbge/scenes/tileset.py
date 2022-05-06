import katagames_engine as kengi
pygame = kengi.pygame
from zlib import decompress
from base64 import b64decode

from pbge import image

from xml.etree import ElementTree

import os


class IsometricTile():
    def __init__(self, id, tile_image, tile_frame):
        print("Creating Tile {}".format(id))
        self.id = id
        self.tile_image = tile_image
        self.tile_frame = tile_frame

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
        self.tiles = []
        self.properties = {}

    def get_tile(self, gid):
        return self.tiles[gid - self.firstgid]

    def add_image(self, source, num_tiles):
        # TODO: Make this bit compatible with Kenji.
        myimage = image.Image(os.path.join("assets", source), self.tile_width, self.tile_height)
        for t in range(num_tiles):
            self.tiles.append(IsometricTile(t+1, myimage, t))

    @classmethod
    def fromxml(cls, tag, firstgid=None, hacksource=None, hacktileset=None):
        print('fromxml (isometrically)')
        if 'source' in tag.attrib:
            firstgid = int(tag.attrib['firstgid'])
            if hacksource:
                srcc = hacksource
            else:
                srcc = tag.attrib['source']

            #TODO: Another direct disk access here.
            with open(os.path.join("assets", srcc)) as f:
                print('opened ', srcc)
                tileset = ElementTree.fromstring(f.read())

            return cls.fromxml(tileset, firstgid, hacktileset=hacktileset)

        name = tag.attrib['name']
        if firstgid is None:
            firstgid = int(tag.attrib['firstgid'])
        tile_width = int(tag.attrib['tilewidth'])
        tile_height = int(tag.attrib['tileheight'])
        num_tiles = int(tag.attrib['tilecount'])

        tileset = cls(name, tile_width, tile_height, firstgid)

        for c in tag:  # .getchildren():
            #TODO: The tileset can only contain an "image" tag or multiple "tile" tags; it can't combine the two.
            # This should be enforced. For now, I'm just gonna support spritesheet tiles.
            if c.tag == "image":
                # create a tileset
                arg_sheet = c.attrib['source'] if (hacktileset is None) else hacktileset
                tileset.add_image(arg_sheet, num_tiles)

        return tileset


