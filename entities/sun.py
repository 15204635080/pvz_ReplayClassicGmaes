# sun.py
import pygame
import random
from settings import *
from resources import Resources

class Sun(pygame.sprite.Sprite):
    def __init__(self, x, y, value=SUN_DEFAULT_VALUE, velocity_y=SUN_FALL_SPEED,
                 lifetime=None,start_time=0,gravity=0,land_y=None):
        super().__init__()
        # 加载原始帧并缩放
        raw_frames = Resources.load_animation(
            folder=SUN_ANIMATION_FOLDER,
            prefix=SUN_ANIMATION_PREFIX,
            count=SUN_ANIMATION_COUNT,
            start_index=SUN_ANIMATION_START_INDEX,
            digits=SUN_ANIMATION_DIGITS,
            extension="png"
        )
        self.frames = [pygame.transform.scale_by(frame, SUN_SCALE) for frame in raw_frames]
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.world_x = x
        self.world_y = y
        # 初始屏幕坐标（暂时设置，每帧 update 会重新计算）
        self.rect.topleft = (x, y)

        # 生命周期
        self.lifetime = lifetime if lifetime is not None else SUN_LIFETIME
        self.spawn_time = start_time
        self.fade_start = self.spawn_time + self.lifetime - SUN_FADE_DURATION
        self.fade_duration = SUN_FADE_DURATION
        self.alpha = 255
        self.fading = False

        # 根据速度决定初始状态
        self.velocity_y = velocity_y
        if velocity_y == 0:
            self.state = 'landed'
            self.land_time = self.spawn_time
            self.land_y = None
        else:
            self.state = 'falling'
            self.land_y = None
            self.land_time = None

        # 动画参数
        self.frame_index = 0
        self.animation_speed = SUN_ANIMATION_SPEED
        self.last_update = start_time
        self.value = value

        # 收集动画参数
        self.collect_start_time = None
        self.collect_finished = False
        self.collect_speed = 400  # 像素/秒
        self.velocity_x = 0
        self.collect_target_world = None   # 目标世界坐标

        #阳光自动收集的参数
        # 自动收集延迟（2~5秒）
        self.auto_collect_delay = random.randint(2000, 10000)  # 毫秒
        self.auto_collect_time = self.spawn_time + self.auto_collect_delay
        self.gravity = gravity
        self.land_y = land_y
    def update(self, now, dt, viewport_x):
        # 根据不同状态更新世界坐标
        if self.state == 'falling':
            if self.land_y is None:
                self.land_y = random.randint(SUN_LAND_Y_MIN, SUN_LAND_Y_MAX)
            self.velocity_y += self.gravity * dt
            self.world_y += self.velocity_y * dt
            # 只有当速度向下且到达或超过落地线时，转为 landed
            if self.velocity_y > 0 and self.world_y >= self.land_y:
                self.world_y = self.land_y
                self.state = 'landed'
                self.land_time = now

        elif self.state == 'landed':
            if self.land_time is None:
                self.land_time = now
            elapsed = now - self.land_time
            if not self.fading and elapsed > self.lifetime - self.fade_duration:
                self.fading = True
                self.fade_start = now
            if self.fading:
                fade_elapsed = now - self.fade_start
                self.alpha = max(0, 255 - int(255 * fade_elapsed / self.fade_duration))
            if elapsed > self.lifetime:
                self.kill()

        elif self.state == 'collecting':
            # 首次进入收集状态：计算目标世界坐标和初始速度
            if self.collect_start_time is None:
                self.collect_start_time = now
                target_screen_x, target_screen_y = SUN_UI_POS
                self.collect_target_world = (viewport_x + target_screen_x, target_screen_y)
                dx = self.collect_target_world[0] - self.world_x
                dy = self.collect_target_world[1] - self.world_y
                distance = (dx ** 2 + dy ** 2) ** 0.5
                if distance > 0:
                    self.velocity_x = dx / distance * self.collect_speed
                    self.velocity_y = dy / distance * self.collect_speed
                else:
                    self.velocity_x = self.velocity_y = 0

            # 移动世界坐标
            self.world_x += self.velocity_x * dt
            self.world_y += self.velocity_y * dt

            # 到达判定（世界坐标距离）
            dx = self.collect_target_world[0] - self.world_x
            dy = self.collect_target_world[1] - self.world_y
            if dx * dx + dy * dy < 25:   # 5像素阈值
                self.collect_finished = True

        # 动画更新（所有状态共用）
        if now - self.last_update > 1000 / self.animation_speed:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.last_update = now

        # 根据当前帧动画图像更新 self.image（考虑淡出）
        if self.fading:
            self.image = self.frames[self.frame_index].copy()
            self.image.set_alpha(self.alpha)
        else:
            self.image = self.frames[self.frame_index]

        # 更新屏幕坐标（至关重要！否则动画不可见）
        self.rect.x = self.world_x - viewport_x
        self.rect.y = self.world_y

    def start_collect(self, now, viewport_x):
        """开始收集动画，需传入当前视口偏移"""
        if self.state in ('falling', 'landed'):
            self.state = 'collecting'
            self.collect_start_time = None   # 下一帧 update 会重新计算目标
            # 可提前预计算目标（非必须）
            target_screen_x, target_screen_y = SUN_UI_POS
            self.collect_target_world = (viewport_x + target_screen_x, target_screen_y)