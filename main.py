import katagames_engine as kengi
kengi.init('hd')  # instead of pygame.init(), and pygame.display.set_mode(...)

pygame = kengi.pygame  # alias to keep on using pygame, easily
screen = kengi.core.get_screen()  # new way to retrieve the surface used for display

import pbge




kengi.quit()  # instead of pygame.quit()
