import katagames_engine as kengi
kengi.init('hd')  # instead of pygame.init(), and pygame.display.set_mode(...)

pygame = kengi.pygame  # alias to keep on using pygame, easily
screen = kengi.core.get_screen()  # new way to retrieve the surface used for display

import pbge
pbge.init()

#tilemap = kengi.tmx.data.TileMap.load('assets/test_map.tmx', hack_tsxfile="assets/sync-tileset.tsx")  # -> Tilemap instance
#tileset = kengi.tmx.data.load_tmx('assets/sync-tileset.tsx')  # -> Tilemap instance

tilemap = pbge.scenes.IsometricMap.load('assets/test_map.tmx')

keep_going = True

while keep_going:
    gdi = pbge.wait_event()

    if gdi.type == pbge.TIMEREVENT:
        pass
        #for l in tilemap.layers:
        #    l.draw(screen)
        #    kengi.flip()
    elif gdi.type == pygame.KEYDOWN:
        keep_going = False


kengi.quit()  # instead of pygame.quit()
