import random
import timeit
import array

map_width = 5000
map_height = 5000

class LinearMap():
    def __init__(self):
        self.tiles = [random.randint(1,100) for t in range(map_width * map_height)]

    def __getitem__(self, key):
        x,y = key
        i = y*map_width + x
        if x >= 0 and y >= 0 and x < map_width and y < map_height:
            return self.tiles[i]


class ArrayMap():
    def __init__(self):
        tiles = [random.randint(1,100) for t in range(map_width * map_height)]
        self.tiles = array.array("L", tiles)

    def __getitem__(self, key):
        x,y = key
        i = y*map_width + x
        if x >= 0 and y >= 0 and x < map_width and y < map_height:
            return self.tiles[i]
            

class DictMap():
    def __init__(self):
        self.tiles = dict()
        for x in range(map_width):
            for y in range(map_height):
                self.tiles[x,y] = random.randint(1,100)

    def __getitem__(self, key):
        return self.tiles.get(key)

class ListOfListsMap():
    def __init__(self):
        self.tiles = [[random.randint(1,100) for t in range(map_width)] for t in range(map_height)]

    def __getitem__(self, key):
        x,y = key
        if x >= 0 and y >= 0 and x < map_width and y < map_height:
            return self.tiles[x][y]


if __name__ == '__main__':
    print(timeit.timeit("i = a[random.randint(0,{}),random.randint(0,{})]".format(map_width-1,map_height-1), setup="from __main__ import random, LinearMap\na = LinearMap()", number=100000))
    print(timeit.timeit("i = a[random.randint(0,{}),random.randint(0,{})]".format(map_width-1,map_height-1), setup="from __main__ import random, ArrayMap\na = ArrayMap()", number=100000))
    print(timeit.timeit("i = a[random.randint(0,{}),random.randint(0,{})]".format(map_width-1,map_height-1), setup="from __main__ import random, DictMap\na = DictMap()", number=100000))
    print(timeit.timeit("i = a[random.randint(0,{}),random.randint(0,{})]".format(map_width-1,map_height-1), setup="from __main__ import random, ListOfListsMap\na = ListOfListsMap()", number=100000))
