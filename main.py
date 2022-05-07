import katagames_engine as kengi
kengi.init('hd')  # instead of pygame.init(), and pygame.display.set_mode(...)

pygame = kengi.pygame  # alias to keep on using pygame, easily
screen = kengi.core.get_screen()  # new way to retrieve the surface used for display

import pbge
pbge.init()


#tilemap = kengi.tmx.data.TileMap.load('assets/test_map.tmx', hack_tsxfile="assets/sync-tileset.tsx")  # -> Tilemap instance
#tileset = kengi.tmx.data.load_tmx('assets/sync-tileset.tsx')  # -> Tilemap instance

tilemap = pbge.scenes.IsometricMap.load('assets/test_map.tmx')
viewer = pbge.scenes.viewer.SceneView(tilemap, screen)

keep_going = True

while keep_going:
    gdi = pbge.wait_event()

    if gdi.type == pbge.TIMEREVENT:
        viewer()
        kengi.flip()
    elif gdi.type == pygame.KEYDOWN and gdi.key == pygame.K_ESCAPE:
        keep_going = False


kengi.quit()  # instead of pygame.quit()
