import pbge
import pygame
from pbge import my_state,draw_text,default_border,anim_delay

class ConvoVisualizer(object):
    # The visualizer is a class used by the conversation when conversing.
    # It has a "text" property and "render", "get_menu" methods.
    TEXT_AREA = pbge.frects.Frect(0,-125,300,100)
    MENU_AREA = pbge.frects.Frect(0,0,300,80)
    PORTRAIT_AREA = pbge.frects.Frect(-370,-300,400,600)
    
    def __init__(self,npc):
        self.npc = npc
        self.npc_sprite = pbge.image.Image(npc.portrait,400,600,npc.colors)
        self.bottom_sprite = pbge.image.Image('sys_wintermocha_convoborder.png',32,200)
        self.text = ''
    def render(self):
        if my_state.view:
            my_state.view()

        self.bottom_sprite.tile(pygame.Rect(0,my_state.screen.get_height()//2+100,my_state.screen.get_width(),200))
        self.npc_sprite.render(self.PORTRAIT_AREA.get_rect())

        text_rect = self.TEXT_AREA.get_rect()
        default_border.render(text_rect)
        draw_text(my_state.medium_font,self.text,text_rect)
        default_border.render(self.MENU_AREA.get_rect())

    def rollout(self):
        bx = my_state.screen.get_width()
        t = 0
        myrect = self.PORTRAIT_AREA.get_rect()
        myrect.x = -400
        while (myrect.x < self.PORTRAIT_AREA.get_rect().x):
            if my_state.view:
                my_state.view()
            self.bottom_sprite.tile(pygame.Rect(max(0,bx-t*75),my_state.screen.get_height()//2+100,my_state.screen.get_width(),200))
            self.npc_sprite.render(myrect)

            my_state.do_flip()
            myrect.x += 25
            anim_delay()
            t += 1

    def get_menu(self):
        return pbge.rpgmenu.Menu(self.MENU_AREA.dx,self.MENU_AREA.dy,self.MENU_AREA.w,self.MENU_AREA.h,border=None,predraw=self.render,font=my_state.medium_font)

