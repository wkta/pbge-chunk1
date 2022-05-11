import katagames_engine as kengi
kengi.init('old_school')  # instead of pygame.init(), and pygame.display.set_mode(...)

pygame = kengi.pygame  # alias to keep on using pygame, easily
screen = kengi.core.get_screen()  # new way to retrieve the surface used for display

import pbge
pbge.init()


#tilemap = kengi.tmx.data.TileMap.load('assets/test_map.tmx', hack_tsxfile="assets/sync-tileset.tsx")  # -> Tilemap instance
#tileset = kengi.tmx.data.load_tmx('assets/sync-tileset.tsx')  # -> Tilemap instance

tilemap = pbge.scenes.IsometricMap.load('assets/test_map.tmx')
viewer = pbge.scenes.viewer.IsometricMapViewer(tilemap, screen)
cursor_image = pygame.image.load("assets/half-floor-tile.png").convert_alpha()
cursor_image.set_colorkey((255,0,255))
viewer.cursor = pbge.scenes.mapcursor.QuarterCursor(0,0,cursor_image,tilemap.layers[1])

keep_going = True

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
            print(viewer.relative_x(0,0), viewer.relative_y(0,0))
            print(viewer.relative_x(0,19), viewer.relative_y(0,19))

    elif gdi.type == pygame.QUIT:
        keep_going = False


kengi.quit()  # instead of pygame.quit()
