# Polar Bear Game Engine

# This package contains some low-level graphics stuff needed to
# create an isometric RPG style rules in Python. The idea is to
# isolate the graphics handling from the code as much as possible,
# so that if PyGame is replaced the interface shouldn't change
# too much. Also, so that creating a new rules should be as simple
# as importing this package.

# Word wrapper taken from the PyGame wiki plus
# the list-printer from Anne Archibald's GearHead Prime demo.

import katagames_engine as kengi

pygame = kengi.pygame  # alias to keep on using pygame, easily
screen = kengi.core.get_screen()  # new way to retrieve the surface used for display

from itertools import chain
import random
import weakref
import sys


class KeyObject(object):
    """A catcher for multiple inheritence. Subclass this instead of object if
       you're going to use multiple inheritence, so that erroneous keywords
       will get caught and identified."""

    def __init__(self, **keywords):
        for k, i in keywords.items():
            print("WARNING: KeyObject got parameters {}={}".format(k, i))


class SingletonMeta(type):
    def __str__(cls):
        return cls.name

class Singleton(object, metaclass=SingletonMeta):
    """For rules constants that don't need to be instanced."""
    name = "Singleton"
    def __init__(self):
        raise NotImplementedError("Singleton can't be instantiated.")


class Border(object):
    def __init__(self, border_width=16, tex_width=32, border_name="", tex_name="", padding=16, tl=0, tr=0, bl=0, br=0,
                 t=1, b=1, l=2, r=2, transparent=True):
        # tl,tr,bl,br are the top left, top right, bottom left, and bottom right frames
        # Bug: The border must be exactly half as wide as the texture.
        self.border_width = border_width
        self.tex_width = tex_width
        self.border_name = border_name
        self.tex_name = tex_name
        self.border = None
        self.tex = None
        self.padding = padding
        self.tl = tl
        self.tr = tr
        self.bl = bl
        self.br = br
        self.t = t
        self.b = b
        self.l = l
        self.r = r
        self.transparent = transparent

    def render(self, dest):
        """Draw this decorative border at dest on screen."""
        # We're gonna draw a decorative border to surround the provided area.
        if self.border == None:
            self.border = image.Image(self.border_name, self.border_width, self.border_width)
        if self.tex_name and not self.tex:
            self.tex = image.Image(self.tex_name, self.tex_width, self.tex_width)
            if self.transparent:
                self.tex.bitmap.set_alpha(224)

        # Draw the backdrop.
        if self.tex:
            self.tex.tile(dest.inflate(self.padding, self.padding))

        # Expand the dimensions to their complete size.
        # The method inflate_ip doesn't seem to be working... :(
        fdest = dest.inflate(self.padding, self.padding)

        self.border.render((fdest.x - self.border_width // 2, fdest.y - self.border_width // 2), self.tl)
        self.border.render((fdest.x - self.border_width // 2, fdest.y + fdest.height - self.border_width // 2), self.bl)
        self.border.render((fdest.x + fdest.width - self.border_width // 2, fdest.y - self.border_width // 2), self.tr)
        self.border.render(
            (fdest.x + fdest.width - self.border_width // 2, fdest.y + fdest.height - self.border_width // 2), self.br)

        fdest = dest.inflate(self.padding - self.border_width, self.padding + self.border_width)
        screen.set_clip(fdest)
        for x in range(0, fdest.w // self.border_width + 2):
            self.border.render((fdest.x + x * self.border_width, fdest.y), self.t)
            self.border.render((fdest.x + x * self.border_width, fdest.y + fdest.height - self.border_width), self.b)

        fdest = dest.inflate(self.padding + self.border_width, self.padding - self.border_width)
        screen.set_clip(fdest)
        for y in range(0, fdest.h // self.border_width + 2):
            self.border.render((fdest.x, fdest.y + y * self.border_width), self.l)
            self.border.render((fdest.x + fdest.width - self.border_width, fdest.y + y * self.border_width), self.r)
        screen.set_clip(None)


# Monkey Type these definitions to fit your game/assets.
default_border = Border(border_width=8, tex_width=16, border_name="assets/sys_defborder.png", tex_name="assets/sys_defbackground.png",
                        tl=0, tr=3, bl=4, br=5, t=1, b=1, l=2, r=2)
notex_border = Border(border_width=8, border_name="sys_defborder.png", padding=4, tl=0, tr=3, bl=4, br=5, t=1, b=1, l=2,
                      r=2)
# map_border = Border( border_name="sys_mapborder.png", tex_name="sys_maptexture.png", tl=0, tr=1, bl=2, br=3, t=4, b=6, l=7, r=5 )
# gold_border = Border( border_width=8, tex_width=16, border_name="sys_rixsborder.png", tex_name="sys_rixstexture.png", tl=0, tr=3, bl=4, br=5, t=1, b=1, l=2, r=2 )

TEXT_COLOR = (240, 240, 50)
WHITE = (255, 255, 255)
GREY = (160, 160, 160)

INFO_GREEN = (50, 200, 0)
INFO_HILIGHT = (100, 250, 0)
ENEMY_RED = (250, 50, 0)


class GameState(object):
    def __init__(self, screen=None):
        self.screen = screen
        self.physical_screen = None
        self.view = None
        self.got_quit = False
        self.widgets = list()
        self.widgets_active = True
        self.active_widget_hilight = False
        self._active_widget = None
        self.widget_clicked = False
        self.audio_enabled = True
        self.music = None
        self.music_name = None
        self.music_library = dict()
        self.anim_phase = 0
        self.standing_by = False
        self.notifications = list()

        self.mouse_pos = (0, 0)

    def render_widgets(self):
        if self.widgets:
            for w in self.widgets:
                w.super_render()
        elif self.active_widget_hilight:
            self.active_widget_hilight = False

    def render_notifications(self):
        for n in list(self.notifications):
            n.render()
            if n.is_done():
                self.notifications.remove(n)

    def do_flip(self, show_widgets=True, reset_standing_by=True):
        self.widget_tooltip = None
        if show_widgets:
            self.render_widgets()
        if self.notifications:
            self.render_notifications()
        if self.widget_tooltip:
            x, y = self.mouse_pos
            x += 16
            y += 16
            if x + 200 > self.screen.get_width():
                x -= 200
            myimage = render_text(self.small_font, self.widget_tooltip, 200)
            myrect = myimage.get_rect(topleft=(x, y))
            default_border.render(myrect)
            self.screen.blit(myimage, myrect)
        self.anim_phase = (self.anim_phase + 1) % 6000
        if reset_standing_by:
            self.standing_by = False
        pygame.display.flip()


    def _set_active_widget(self, widj):
        if widj:
            self._active_widget = weakref.ref(widj)
        else:
            self._active_widget = None

    def _get_active_widget(self):
        if self._active_widget:
            return self._active_widget()

    def _del_active_widget(self):
        self._active_widget = None

    active_widget = property(_get_active_widget, _set_active_widget, _del_active_widget)

    def _get_all_kb_selectable_widgets(self, wlist):
        mylist = list()
        for w in wlist:
            if w.active:
                if w.is_kb_selectable():
                    mylist.append(w)
                if w.children:
                    mylist += self._get_all_kb_selectable_widgets(w.children)
        return mylist

    def activate_next_widget(self, backwards=False):
        wlist = self._get_all_kb_selectable_widgets(self.widgets)
        awid = self.active_widget
        if awid and awid in wlist:
            if backwards:
                n = wlist.index(awid) - 1
            else:
                n = wlist.index(awid) + 1
                if n >= len(wlist):
                    n = 0
            self.active_widget = wlist[n]
        elif wlist:
            self.active_widget = wlist[0]

    def resize(self):
        w, h = self.physical_screen.get_size()
        self.screen = pygame.Surface((max(800, 600 * w // h), 600))



INPUT_CURSOR = None
SMALLFONT = None
TINYFONT = None
ITALICFONT = None
BIGFONT = None
ANIMFONT = None
MEDIUMFONT = None
ALTTEXTFONT = None  # Use this instead of MEDIUMFONT when you want to shake things up a bit.
POSTERS = list()

# The FPS the rules runs at.
FPS = 30

# Use a timer to control FPS.
TIMEREVENT = pygame.USEREVENT

# Remember whether or not this unit has been initialized, since we don't need
# to initialize it more than once.
INIT_DONE = False


def truncline(text, font, maxwidth):
    real = len(text)
    stext = text
    l = font.size(text)[0]
    cut = 0
    a = 0
    done = 1
    old = None
    while l > maxwidth:
        a = a + 1
        n = text.rsplit(None, a)[0]
        if stext == n:
            cut += 1
            stext = n[:-cut]
        else:
            stext = n
        l = font.size(stext)[0]
        real = len(stext)
        done = 0
    return real, done, stext


def wrapline(text, font, maxwidth):
    done = 0
    wrapped = []

    while not done:
        nl, done, stext = truncline(text, font, maxwidth)
        wrapped.append(stext.strip())
        text = text[nl:]
    return wrapped


def wrap_with_records(fulltext, font, maxwidth):
    # Do a word wrap, but also return the length of each line including whitespace and newlines.
    done = 0
    wrapped = list()
    line_lengths = list()

    for text in fulltext.splitlines(True):
        done = 0
        while not done:
            nl, done, stext = truncline(text, font, maxwidth)
            wrapped.append(stext.lstrip())
            # wrapped.append(stext)
            line_lengths.append(nl + 1)
            text = text[nl:]
    return wrapped, line_lengths


def wrap_multi_line(text, font, maxwidth):
    """ returns text taking new lines into account.
    """
    lines = chain(*(wrapline(line, font, maxwidth) for line in text.splitlines()))
    return list(lines)


def render_text(font, text, width, color=TEXT_COLOR, justify=-1, antialias=True):
    # Return an image with prettyprinted text.
    lines = wrap_multi_line(text, font, width)

    imgs = [font.render(l, antialias, color) for l in lines]
    h = sum(i.get_height() for i in imgs)
    s = pygame.surface.Surface((width, h))
    s.fill((0, 0, 0))
    o = 0
    for i in imgs:
        if justify == 0:
            x = width // 2 - i.get_width() // 2
        elif justify > 0:
            x = width - i.get_width()
        else:
            x = 0
        s.blit(i, (x, o))
        o += i.get_height()
    s.set_colorkey((0, 0, 0), pygame.RLEACCEL)
    return s


def draw_text(font, text, rect, color=TEXT_COLOR, justify=-1, antialias=True, dest_surface=None):
    # Draw some text to the screen with the provided options.
    dest_surface = dest_surface or screen
    myimage = render_text(font, text, rect.width, color, justify, antialias)
    if justify == 0:
        myrect = myimage.get_rect(midtop=rect.midtop)
    elif justify > 0:
        myrect = myimage.get_rect(topleft=rect.topleft)
    else:
        myrect = rect
    dest_surface.set_clip(rect)
    dest_surface.blit(myimage, myrect)
    dest_surface.set_clip(None)


def wait_event():
    # Wait for input, then return it when it comes.
    ev = pygame.event.wait()

    # Record if a quit event took place
    if ev.type == TIMEREVENT:
        pygame.event.clear(TIMEREVENT)

    return ev






from . import frects
from . import image




# PG2 Change
# FULLSCREEN_FLAGS = pygame.FULLSCREEN | pygame.SCALED
# WINDOWED_FLAGS = pygame.RESIZABLE | pygame.SCALED
# FULLSCREEN_RES = (800,600)
FULLSCREEN_FLAGS = pygame.FULLSCREEN
WINDOWED_FLAGS = pygame.RESIZABLE
if sys.platform.startswith("linux"):
    FULLSCREEN_RES = (800, 600)
else:
    FULLSCREEN_RES = (0, 0)


def init():
    global INIT_DONE
    if not INIT_DONE:
        pygame.init()

        global FPS
        FPS = 30
        pygame.time.set_timer(TIMEREVENT, int(1000 / FPS))

        # Set key repeat.
        pygame.key.set_repeat(200, 75)

        INIT_DONE = True


