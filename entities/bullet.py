# entities/bullet.py
import pygame
from resources import Resources

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, row, image, speed=5, damage=10):
        super().__init__()
        self.row = row  # 新增：子弹所在行
        self.image = image
        self.world_x = x
        self.world_y = y
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.damage = damage

    def update(self, now, *args):
        self.world_x += self.speed
        # 移除逻辑可交给 Game 处理，或在此处根据视口判断
        # 但为了方便，建议在 Game 中移除超出屏幕的子弹

    def update_animation(self, now):
        pass


class PeaBullet(Bullet):
    def __init__(self, x, y, row):  # 新增 row 参数
        image = Resources.load_image("bullet/Bullet_1.png", size=(28, 28))
        super().__init__(x, y, row, image, speed=8, damage=20)