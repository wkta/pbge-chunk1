import sys

import katagames_engine as kengi

kengi.init('old_school')  # instead of pygame.init(), and pygame.display.set_mode(...)

pygame = kengi.pygame  # alias to keep on using pygame, easily
screen = kengi.core.get_screen()  # new way to retrieve the surface used for display

import pbge

pbge.init()

tilemap = pbge.scenes.IsometricMap.load('assets/test_map.tmx')
tilemap2 = pbge.scenes.IsometricMap.load('assets/test_map2.tmx')

maps = (tilemap, tilemap2)

viewer = pbge.scenes.viewer.IsometricMapViewer(tilemap, screen, up_scroll_key=pygame.K_UP,
                                               down_scroll_key=pygame.K_DOWN, left_scroll_key=pygame.K_LEFT,
                                               right_scroll_key=pygame.K_RIGHT)
cursor_image = pygame.image.load("assets/half-floor-tile.png").convert_alpha()
cursor_image.set_colorkey((255, 0, 255))
viewer.cursor = pbge.scenes.mapcursor.QuarterCursor(0, 0, cursor_image, tilemap.layers[1])


class Character(pbge.scenes.IsometricMapObject):
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.surf = pygame.image.load("assets/sys_icon.png").convert_alpha()
        # self.surf.set_colorkey((0,0,255))

    def __call__(self, dest_surface, sx, sy, mymap):
        mydest = self.surf.get_rect(midbottom=(sx, sy))
        dest_surface.blit(self.surf, mydest)


mypc = Character(10.5, 10.5)
list(tilemap.objectgroups.values())[0].contents.append(mypc)
list(tilemap2.objectgroups.values())[0].contents.append(mypc)

viewer.set_focused_object(mypc)

keep_going = True
current_tilemap = 0

while keep_going:
    gdi = pbge.wait_event()

    viewer.check_event(gdi)

    if gdi.type == pbge.TIMEREVENT:
        viewer()
        kengi.flip()
    elif gdi.type == pygame.KEYDOWN:
        if gdi.key == pygame.K_ESCAPE:
            keep_going = False
        elif gdi.key == pygame.K_m:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            print(viewer.map_x(mouse_x, mouse_y, return_int=False), viewer.map_y(mouse_x, mouse_y, return_int=False))
            print(viewer.relative_x(0, 0), viewer.relative_y(0, 0))
            print(viewer.relative_x(0, 19), viewer.relative_y(0, 19))
        elif gdi.key == pygame.K_d and mypc.x < tilemap.width - 1.5:
            mypc.x += 0.1
        elif gdi.key == pygame.K_a and mypc.x > -1:
            mypc.x -= 0.1
        elif gdi.key == pygame.K_w and mypc.y > -1:
            mypc.y -= 0.1
        elif gdi.key == pygame.K_s and mypc.y < tilemap.height - 1.5:
            mypc.y += 0.1
        elif gdi.key == pygame.K_TAB:
            current_tilemap = 1 - current_tilemap
            viewer.switch_map(maps[current_tilemap])

    elif gdi.type == pygame.QUIT:
        keep_going = False

kengi.quit()  # instead of pygame.quit()
sys.exit()
