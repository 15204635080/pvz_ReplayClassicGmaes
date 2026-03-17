# entities/plant.py
import pygame
from resources import Resources
from settings import *

class Plant(pygame.sprite.Sprite):
    def __init__(self, x, y, row, anim_frames, anim_speed=0.1, health=100,start_time=0):
        super().__init__()
        self.row = row  # 新增：保存植物所在行
        self.frames = anim_frames
        self.anim_index = 0
        self.anim_speed = anim_speed
        self.last_update = start_time
        self.image = self.frames[0]
        # 世界坐标
        self.world_x = x
        self.world_y = y
        # 屏幕坐标矩形（每帧由 Game 更新）
        self.rect = self.image.get_rect(topleft=(x, y))
        self.health = health
        self.max_health = health
        self.shoot_timer = 0
        self.shoot_interval = 2000
        self.spawn_time = pygame.time.get_ticks()

        # 新增：出生保护时间（毫秒）
        self.spawn_protection = 1000
        self.shovel_hover = False  # 铲子悬停标志



    def update(self, now, *args):
        # 动画更新
        if now - self.last_update > self.anim_speed * 1000:
            self.anim_index = (self.anim_index + 1) % len(self.frames)
            self.image = self.frames[self.anim_index]
            self.last_update = now

    def take_damage(self, damage):
        now = pygame.time.get_ticks()

        # 出生保护期
        if now - self.spawn_time < self.spawn_protection:
            return
        self.health -= damage
        if self.health <= 0:
            self.kill()

    def can_shoot(self, now):
        return False

    def shoot(self):
        pass


class Peashooter(Plant):
    def __init__(self, x, y, row,start_time=0):  # 新增 row 参数
        frames = Resources.load_animation(
            folder="peashooter",
            prefix="Peashooter_",
            count=PEASHOOTER_FRAMES,
            start_index=0,
            digits=2,
            extension="png",
            size=(CELL_WIDTH, CELL_HEIGHT)
        )
        super().__init__(x, y, row, frames, anim_speed=0.1, health=100, start_time=start_time)
        self.shoot_interval =2000
        self.shoot_timer = start_time

    def can_shoot(self, now):
        if now - self.shoot_timer > self.shoot_interval:
            self.shoot_timer = now
            return True
        return False

    def shoot(self):
        from entities.bullet import PeaBullet
        #对准豌豆射手的口
        MOUTH_OFFSET_X = int(self.rect.width * 0.91)  # 假设口部靠右
        MOUTH_OFFSET_Y = int(self.rect.height * 0.15)  # 假设口部偏上

        bullet_x = self.world_x + MOUTH_OFFSET_X
        bullet_y = self.world_y + MOUTH_OFFSET_Y

        return PeaBullet(bullet_x, bullet_y, self.row)

import random  # 在文件顶部添加

class Sunflower(Plant):
    def __init__(self, x, y, row, start_time=0):
        frames = Resources.load_animation(
            folder=SUNFLOWER_ANIMATION_FOLDER,
            prefix=SUNFLOWER_ANIMATION_PREFIX,
            count=SUNFLOWER_ANIMATION_COUNT,
            start_index=SUNFLOWER_ANIMATION_START_INDEX,
            digits=SUNFLOWER_ANIMATION_DIGITS,
            extension="png",
            size=(CELL_WIDTH, CELL_HEIGHT)
        )
        super().__init__(x, y, row, frames, anim_speed=SUNFLOWER_ANIMATION_SPEED, health=100, start_time=start_time)
        self.produce_interval = SUNFLOWER_PRODUCE_INTERVAL
        self.first_produce_delay = random.randint(7000, 9000)
        self.last_produce = start_time
        self.has_produced = False
        self.produce_value = SUNFLOWER_PRODUCE_VALUE

        # ---------- 生成高亮帧：仅对非透明像素且在上方70%区域增加亮度 ----------
        self.glow_frames = []
        BRIGHTNESS_ADD = 100  # 亮度增量，可调
        HEIGHT_RATIO = 0.7  # 仅变亮图像上方 70% 区域
        for frame in frames:
            # 创建副本（保证不修改原帧）
            highlighted = frame.copy()
            try:
                pa = pygame.PixelArray(highlighted)
                h = highlighted.get_height()
                threshold_y = int(h * HEIGHT_RATIO)  # 纵坐标阈值，小于此值才变亮
                for x in range(pa.shape[0]):
                    for y in range(pa.shape[1]):
                        if y >= threshold_y:
                            continue  # 跳过下方区域
                        color = pa[x][y]
                        r, g, b, a = highlighted.unmap_rgb(color)
                        if a > 0:  # 只处理非透明像素
                            r = min(255, r + BRIGHTNESS_ADD)
                            g = min(255, g + BRIGHTNESS_ADD)
                            b = min(255, b + BRIGHTNESS_ADD)
                            pa[x][y] = (r, g, b, a)
                pa.close()
            except Exception as e:
                print(f"生成高亮帧时出错: {e}，将使用原始帧")
                highlighted = frame
            self.glow_frames.append(highlighted)
        # -----------------------------------------------------

        self.glow_threshold = 1500  # 生产前 2 秒开始变亮

    def can_produce(self, now):
        if not self.has_produced:
            if now - self.last_produce >= self.first_produce_delay:
                self.has_produced = True
                return True
            return False
        else:
            return now - self.last_produce >= self.produce_interval

    # plant.py 中的 Sunflower 类的 produce 方法

    def produce(self, now):
        self.last_produce = now
        min_x = int(self.world_x - self.rect.width * 0.8)
        max_x = int(self.world_x + self.rect.width * 0.8)
        if min_x > max_x:
            min_x, max_x = max_x, min_x  # 防止范围颠倒
        sun_x = random.randint(min_x, max_x)
        sun_y = self.world_y - 20  # 从向日葵脸部位置生成
        from entities.sun import Sun
        ground_y = self.world_y - 20 + random.randint(-25, 25)
        sun = Sun(
            sun_x,
            sun_y,
            value=self.produce_value,
            velocity_y=-random.randint(150,200),  # 向上初速度（像素/秒）
            lifetime=30000,
            start_time=now,
            gravity=random.randint(250,300),  # 重力加速度，使阳光先上升后下降
            land_y = ground_y
        )

        return sun

    def update(self, now, *args):
        # 计算下一次生产时间点
        if not self.has_produced:
            next_produce = self.last_produce + self.first_produce_delay
        else:
            next_produce = self.last_produce + self.produce_interval

        remaining = next_produce - now

        # 先调用父类更新动画（更新 anim_index 和 last_update，设置 self.image 为当前原始帧）
        super().update(now, *args)

        # 如果处于生产前阈值内，则替换为对应的高亮帧
        if 0 < remaining <= self.glow_threshold:
            self.image = self.glow_frames[self.anim_index]
        # 否则保留父类设置的原始帧

class Wallnut(Plant):
    def __init__(self, x, y, row, start_time=0):
        # 加载正常动画帧
        frames = Resources.load_animation(
            folder="wall_nut",
            prefix="WallNut_",
            count=WALLNUT_FRAMES,
            start_index=0,
            digits=2,
            extension="png",
            size=(CELL_WIDTH, CELL_HEIGHT)
        )
        super().__init__(x, y, row, frames, anim_speed=0.1, health=4000, start_time=start_time)

        # 加载裂纹图片
        try:
            self.cracked1_img = Resources.load_image("wall_nut/Wallnut_cracked1.png", size=(CELL_WIDTH, CELL_HEIGHT))
            self.cracked2_img = Resources.load_image("wall_nut/Wallnut_cracked2.png", size=(CELL_WIDTH, CELL_HEIGHT))
        except Exception as e:
            print(f"无法加载坚果裂纹图片: {e}")
            # 备用：创建裂纹图片（简单变色）
            self.cracked1_img = pygame.Surface((CELL_WIDTH, CELL_HEIGHT))
            self.cracked1_img.fill((150, 75, 0))  # 棕色
            self.cracked2_img = pygame.Surface((CELL_WIDTH, CELL_HEIGHT))
            self.cracked2_img.fill((100, 50, 0))  # 更深的棕色

        # 保存原始动画帧（用于健康状态）
        self.normal_frames = frames
        self.current_state = 'normal'  # 'normal', 'cracked1', 'cracked2'

    def update(self, now, *args):
        health_ratio = self.health / self.max_health

        if health_ratio <= 0.25:
            if self.current_state != 'cracked2':
                self.current_state = 'cracked2'
                self.image = self.cracked2_img
            # 静态图片，不播放动画，只更新时间戳防止警告
            self.last_update = now
        elif health_ratio <= 0.5:
            if self.current_state != 'cracked1':
                self.current_state = 'cracked1'
                self.image = self.cracked1_img
            self.last_update = now
        else:
            if self.current_state != 'normal':
                self.current_state = 'normal'
                # 恢复动画帧，并确保索引有效
                self.frames = self.normal_frames
                self.anim_index = self.anim_index % len(self.frames)
                self.image = self.frames[self.anim_index]
            # 调用父类更新动画
            super().update(now, *args)

class CherryBomb(Plant):
    def __init__(self, x, y, row, start_time=0):
        frames = Resources.load_animation(
            folder="cherrybomb",
            prefix="cherrybomb_",
            count=CHERRYBOMB_FRAMES,
            start_index=0,
            digits=3,
            extension="png",
            size=(CELL_WIDTH, CELL_HEIGHT)
        )
        super().__init__(x, y, row, frames,
                         anim_speed=CHERRYBOMB_ANIMATION_SPEED,
                         health=9999,
                         start_time=start_time)
        self.exploded = False
        self.explode_frame = CHERRYBOMB_EXPLODE_FRAME
        self.explode_scale = 3.0
        # 记录原始中心世界坐标（不变）
        self.center_x = self.world_x + CELL_WIDTH / 2
        self.center_y = self.world_y + CELL_HEIGHT / 2
        # 新增：是否跳过自动位置更新
        self.override_position = False
        self.explode_sound = Resources.load_sound("cherrybomb.mp3")

    def update(self, now, viewport_x=None):
        # 动画推进
        if now - self.last_update > self.anim_speed * 1000:
            if self.anim_index < len(self.frames) - 1:
                self.anim_index += 1
                self.last_update = now

        # 到达爆炸帧时标记爆炸
        if not self.exploded and self.anim_index >= self.explode_frame:
            self.exploded = True
            if self.explode_sound:
                self.explode_sound.play()  # 播放一次
        frame_img = self.frames[self.anim_index]

        # 爆炸放大（从爆炸帧的下一帧开始）
        if self.exploded and self.anim_index >= self.explode_frame + 1:
            # 缩放图像


            new_w = int(frame_img.get_width() * self.explode_scale)
            new_h = int(frame_img.get_height() * self.explode_scale)
            scaled_img = pygame.transform.scale(frame_img, (new_w, new_h))
            self.image = scaled_img

            # 启用自定义位置管理
            self.override_position = True

            # 计算屏幕坐标（基于视口）
            if viewport_x is not None:
                # 屏幕中心点 = 世界中心点 - 视口偏移
                screen_center_x = self.center_x - viewport_x
                screen_center_y = self.center_y
                # 你可以在这里添加手动偏移（例如-200, -200）
                # self.rect = scaled_img.get_rect(center=(screen_center_x - 200, screen_center_y - 200))
                # 正常以中心锚点放大（不偏移）：
                self.rect = scaled_img.get_rect(center=(screen_center_x, screen_center_y))
            else:
                # 降级处理（没有视口信息时使用世界坐标中心，但屏幕坐标会错位）
                self.rect = scaled_img.get_rect(center=(self.center_x, self.center_y))
        else:
            # 正常状态：使用原始图像，位置由 game 自动更新
            self.image = frame_img
            self.override_position = False
            # 让 game 的 update_screen_positions 负责设置 rect 位置
            self.rect.size = frame_img.get_size()   # 只更新尺寸，不设置位置

        # 动画结束移除
        if self.anim_index >= len(self.frames) - 1:
            self.kill()