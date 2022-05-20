import katagames_engine as kengi

pygame = kengi.pygame  # alias to keep on using pygame, easily
screen = kengi.core.get_screen()  # new way to retrieve the surface used for display

ANCHOR_UPPERLEFT = (0, 0)
ANCHOR_UPPERRIGHT = (2, 0)
ANCHOR_CENTER = (1, 1)
ANCHOR_LOWERLEFT = (0, 2)
ANCHOR_LOWERRIGHT = (2, 2)
ANCHOR_TOP = (1, 0)
ANCHOR_LEFT = (0, 1)
ANCHOR_RIGHT = (2, 1)


class Frect(object):
    """Floating rect- changes position depending on the screen dimensions."""

    def __init__(self, dx, dy, w, h, anchor=ANCHOR_CENTER, parent=None):
        self.dx = dx
        self.dy = dy
        self.w = w
        self.h = h
        self.anchor = anchor
        self.parent = parent

    def get_rect(self):
        if self.parent:
            prect = self.parent.get_rect()
            x0 = prect.left + (prect.w // 2) * self.anchor[0]
            y0 = prect.top + (prect.h // 2) * self.anchor[1]
        else:
            x0 = (screen.get_width() // 2) * self.anchor[0]
            y0 = (screen.get_height() // 2) * self.anchor[1]
        return pygame.Rect(self.dx + x0, self.dy + y0, self.w, self.h)
