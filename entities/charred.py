# entities/charred.py
import pygame
from resources import Resources
from settings import CHARRED_FRAMES, CHARRED_ANIMATION_SPEED

class ZombieCharred(pygame.sprite.Sprite):
    _frames_cache = None

    def __init__(self, x, y, row, start_time=0):
        super().__init__()
        if ZombieCharred._frames_cache is None:
            ZombieCharred._frames_cache = Resources.load_animation(
                folder="zombie_charred",
                prefix="Zombie_charred",
                count=CHARRED_FRAMES,
                start_index=1,
                digits=1,
                extension="png",
                size=None
            )
        self.frames = ZombieCharred._frames_cache
        self.anim_index = 0
        self.anim_speed = CHARRED_ANIMATION_SPEED
        self.last_update = start_time
        self.image = self.frames[0]
        self.world_x = x
        self.world_y = y
        self.row = row                     # 新增 row 属性
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self, now, *args):
        if now - self.last_update > self.anim_speed * 1000:
            if self.anim_index < len(self.frames) - 1:
                self.anim_index += 1
                self.image = self.frames[self.anim_index]
                self.last_update = now
            else:
                self.kill()