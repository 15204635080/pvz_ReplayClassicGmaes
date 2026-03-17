# entities/mower.py
import pygame
from settings import LAWNMOWER_START_X, LAWNMOWER_SPEED, LAWN_TOP_LEFT_Y, CELL_HEIGHT, BACKGROUND_WIDTH, MOWER_SCALE
from resources import Resources

class Mower(pygame.sprite.Sprite):
    def __init__(self, row):
        super().__init__()
        self.row = row
        try:
            raw_image = Resources.load_image("screen/car.png")
            scale = CELL_HEIGHT * MOWER_SCALE / raw_image.get_height()
            new_size = (int(raw_image.get_width() * scale), int(raw_image.get_height() * scale))
            self.image = pygame.transform.scale(raw_image, new_size)
        except Exception as e:
            print(f"无法加载小推车图片: {e}")
            self.image = pygame.Surface((60, 60))
            self.image.fill((255, 255, 255))
            pygame.draw.rect(self.image, (0, 0, 0), self.image.get_rect(), 2)

        self.rect = self.image.get_rect()
        self.ENTER_START_X = 0
        self.target_x = LAWNMOWER_START_X
        self.world_x = self.ENTER_START_X
        self.world_y = LAWN_TOP_LEFT_Y + row * CELL_HEIGHT + (CELL_HEIGHT - self.rect.height) // 2
        self.rect.topleft = (self.world_x, self.world_y)

        self.state = 'idle'           # 初始状态，由外部触发进入 entering
        self.enter_speed = 0           # 入场速度（像素/秒）
        self.speed = LAWNMOWER_SPEED   # 触发后的移动速度

    def start_enter(self, duration):
        """开始入场动画，duration为期望的移动时间（秒）"""
        self.state = 'entering'
        self.world_x = self.ENTER_START_X
        if duration > 0:
            self.enter_speed = (self.target_x - self.ENTER_START_X) / duration
        else:
            # 后备：1秒
            self.enter_speed = (self.target_x - self.ENTER_START_X) / 1.0

    def trigger(self):
        if self.state == 'idle':
            self.state = 'moving'

    def update(self, dt, viewport_x):
        if self.state == 'entering':
            self.world_x += self.enter_speed * dt
            if self.world_x >= self.target_x:
                self.world_x = self.target_x
                self.state = 'idle'
        elif self.state == 'moving':
            self.world_x += self.speed * dt

        # 更新屏幕坐标
        self.rect.x = self.world_x - viewport_x
        self.rect.y = self.world_y

        # 移出屏幕后销毁（仅 moving 状态可能）
        if self.state == 'moving' and self.world_x > BACKGROUND_WIDTH:
            self.kill()