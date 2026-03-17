# entities/zombie.py
import pygame
import random
from resources import Resources
from settings import CELL_WIDTH, CELL_HEIGHT, ZOMBIE_BASE_SPEED
import math
class Zombie(pygame.sprite.Sprite):
    STATE_WALK = 0
    STATE_ATTACK = 1
    STATE_DIE = 2
    STATE_SQUASHED = 3          # 新增：被碾压状态

    def __init__(self, x, y, row, animations, anim_speed=0.1, health=270, speed=ZOMBIE_BASE_SPEED, chomp_sounds=None, start_time=0):
        super().__init__()
        self.row = row
        self.animations = animations
        self.state = self.STATE_WALK

        self.anim_frames = animations['walk']
        self.anim_index = 0
        self.last_update = start_time
        self.anim_speed = anim_speed
        if self.anim_frames:
            self.anim_index = random.randint(0, len(self.anim_frames) - 1)
            self.image = self.anim_frames[self.anim_index]
            offset = random.randint(0, int(self.anim_speed * 1000))
            self.last_update -= offset
            if self.last_update < 0:
                self.last_update = 0

        self.world_x = x
        self.world_y = y
        self.rect = self.image.get_rect(topleft=(x, y))
        self.health = health
        self.max_health = health
        self.speed = speed
        self.attack_damage = 20
        self.attack_cooldown = 500
        self.last_attack = 0
        self.target_plant = None
        self.die_finished = False
        self.original_speed = speed

        # 特殊死亡动画属性
        self.die_special = False
        self.die_loop_target = 0
        self.die_loop_current = 0
        self.die_start_health = 0
        self.die_total_frames = 0
        self.die_frame_count = 0
        self.collision_left_ratio = 0.43
        self.collision_width_ratio = 0.4
        self.collision_rect = self.rect.copy()
        self.die_loop_frames = []

        # 草坪进入阈值
        lawn_enter_thresholds = [983, 993, 998, 993, 1001]
        self.speedup_threshold = lawn_enter_thresholds[row]

        # 啃咬音效相关
        self.chomp_sounds = chomp_sounds if chomp_sounds else []
        self.last_chomp_time = 0
        self.chomp_interval = 300

        # 新增：碾压相关属性
        self.squash_start_time = 0      # 进入碾压状态的时间戳
        self.squash_angle = 0.0         # 当前旋转角度
        self.squash_finished = False    # 旋转是否完成
        self.head = None                 # 关联的僵尸头
        self.death_callback = None       # 死亡回调（由 Game 设置）
        self.death_counted = False       # 防止重复计数
        self.squash_image = None  # 碾压时固定的图像
        # 旋转锚点（脚底）
        self.foot_anchor = (self.rect.width * 0.45, self.rect.height)

        self.squash_image = None
        self.foot_anchor = None
        self.anchor_world = (0, 0)
        # 新增：下沉偏移（向右下角）
        self.sink_x = 0
        self.sink_y = 0
    def _update_collision_rect(self):
        img_width = self.rect.width
        img_height = self.rect.height
        coll_left = self.rect.left + img_width * self.collision_left_ratio
        coll_width = img_width * self.collision_width_ratio
        self.collision_rect = pygame.Rect(coll_left, self.rect.top, coll_width, img_height)

    def update(self, now, *args):
        # 先更新动画（普通动画或碾压动画）
        self._update_animation(now)

        if self.state == self.STATE_WALK:
            if self.world_x > self.speedup_threshold:
                self.speed = self.original_speed * 3
            else:
                self.speed = self.original_speed
            self.world_x -= self.speed
        elif self.state == self.STATE_ATTACK:
            if self.target_plant and self.target_plant.alive():
                if now - self.last_attack > self.attack_cooldown:
                    self.target_plant.take_damage(self.attack_damage)
                    self.last_attack = now
                    new_speed = self.randomize_speed()
                    self.original_speed = new_speed
                    self.speed = new_speed
                if self.chomp_sounds and now - self.last_chomp_time > self.chomp_interval:
                    sound = random.choice(self.chomp_sounds)
                    sound.play()
                    self.last_chomp_time = now
            else:
                self.set_state(self.STATE_WALK)
        elif self.state == self.STATE_DIE:
            if self._should_die_end():
                self.kill()
        elif self.state == self.STATE_SQUASHED:
            if not self.squash_finished:
                elapsed = now - self.squash_start_time
                ROTATION_TIME = 500
                if elapsed >= ROTATION_TIME:
                    self.squash_angle = -90
                    self.squash_finished = True
                    self.sink_x = 180  # 最终向右偏移量
                    self.sink_y = 0  # 最终向下偏移量
                else:
                    self.squash_angle = -90 * (elapsed / ROTATION_TIME)
                    progress = elapsed / ROTATION_TIME
                    self.sink_x = 180 * progress
                    self.sink_y = 0 * progress

                orig_image = self.squash_image
                rotated = pygame.transform.rotate(orig_image, self.squash_angle)

                orig_w, orig_h = orig_image.get_size()
                cx = orig_w / 2.0
                cy = orig_h / 2.0
                dx = self.foot_anchor[0] - cx
                dy = self.foot_anchor[1] - cy

                angle_rad = math.radians(self.squash_angle)
                rdx = dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
                rdy = dx * math.sin(angle_rad) + dy * math.cos(angle_rad)

                new_center_x = self.anchor_world[0] - rdx + self.sink_x
                new_center_y = self.anchor_world[1] - rdy + self.sink_y

                # 计算旋转后图像左上角的世界坐标
                new_world_x = new_center_x - rotated.get_width() / 2
                new_world_y = new_center_y - rotated.get_height() / 2

                self.image = rotated
                self.world_x = new_world_x
                self.world_y = new_world_y
                # 注意：这里不再设置 self.rect，让 update_screen_positions 去更新
            else:
                if self.head is None or not self.head.alive():
                    self.kill()
    def _should_die_end(self):
        return not self.die_special and self.anim_index == len(self.anim_frames) - 1

    def update_animation(self, now):
        if now - self.last_update > self.anim_speed * 1000:
            self.anim_index = (self.anim_index + 1) % len(self.anim_frames)
            self.image = self.anim_frames[self.anim_index]
            self.last_update = now

    def set_state(self, new_state):
        if new_state == self.state:
            return
        self.state = new_state
        if new_state == self.STATE_WALK:
            self.anim_frames = self.animations['walk']
        elif new_state == self.STATE_ATTACK:
            self.anim_frames = self.animations['attack']
        elif new_state == self.STATE_DIE:
            self.anim_frames = self.animations['die']
            self.die_start_health = self.health
            if random.random() < 0.05:
                self.die_special = True
                self.die_loop_target = 5
                self.die_loop_current = 0
                self.die_loop_frames = [9, 8, 7, 6]
                self.die_total_frames = self.die_loop_target * len(self.die_loop_frames) + len(self.anim_frames)
            else:
                self.die_special = False
                self.die_total_frames = len(self.anim_frames)
            self.die_frame_count = 0
        self.anim_index = 0
        self.image = self.anim_frames[0]
        self.rect.size = self.image.get_size()

    def take_damage(self, damage):
        if self.state == self.STATE_DIE:
            return
        self.health -= damage
        if self.health <= 70 and self.state != self.STATE_DIE:
            self.set_state(self.STATE_DIE)

    def _update_animation(self, now):
        if self.state == self.STATE_SQUASHED:
            return  # 碾压时不更新动画
        if now - self.last_update <= self.anim_speed * 1000:
            return
        self.last_update = now

        if self.state == self.STATE_DIE:
            if self.die_special:
                if self.die_loop_current < self.die_loop_target:
                    current_loop_frame_index = self.die_loop_frames[self.anim_index]
                    self.anim_index += 1
                    if self.anim_index >= len(self.die_loop_frames):
                        self.die_loop_current += 1
                        self.anim_index = 0
                    frame_idx = self.die_loop_frames[self.anim_index] if self.anim_index < len(
                        self.die_loop_frames) else 0
                    self.image = self.anim_frames[frame_idx]
                else:
                    self.die_special = False
                    self.anim_index = 0
                    self.image = self.anim_frames[0]
            else:
                if self.anim_index < len(self.anim_frames) - 1:
                    self.anim_index += 1
                self.image = self.anim_frames[self.anim_index]

            self.die_frame_count += 1
            if self.die_total_frames > 0:
                progress = self.die_frame_count / self.die_total_frames
                self.health = max(0, self.die_start_health * (1 - progress))
        elif self.state == self.STATE_SQUASHED:
            # 碾压状态下，让动画正常播放，但图像会在 update 的旋转部分被覆盖
            self.anim_index = (self.anim_index + 1) % len(self.anim_frames)
        else:
            self.anim_index = (self.anim_index + 1) % len(self.anim_frames)
            self.image = self.anim_frames[self.anim_index]

    def attack(self, plant):
        if self.state == self.STATE_DIE:
            return
        self.target_plant = plant
        self.set_state(self.STATE_ATTACK)

    def stop_attack(self):
        if self.state == self.STATE_DIE:
            return
        self.target_plant = None
        if self.state != self.STATE_DIE:
            self.set_state(self.STATE_WALK)

    def randomize_speed(self):
        """生成一个新的随机速度，子类可覆盖"""
        return self.speed

    def squash(self, now):
        if self.state in (self.STATE_DIE, self.STATE_SQUASHED):
            return
        self.state = self.STATE_SQUASHED
        self.squash_start_time = now
        self.squash_angle = 0.0
        self.squash_finished = False
        # 固定当前帧图像
        self.squash_image = self.image.copy()
        img_w, img_h = self.squash_image.get_size()
        # 锚点：水平居中，脚底附近（可根据实际微调）
        self.foot_anchor = (img_w * 0.5, img_h * 0.95)
        self.anchor_world = (
            self.world_x + self.foot_anchor[0],
            self.world_y + self.foot_anchor[1]
        )
        # 初始化下沉偏移量
        self.sink_x = 0
        self.sink_y = 0
        ground_y = self.world_y + self.rect.height
        self.head = ZombieHead(self.world_x, self.world_y, self.row, ground_y=ground_y)
        if self.death_callback and not self.death_counted:
            self.death_callback(self)
            self.death_counted = True

    def kill(self):
        """重写 kill，确保死亡回调只调用一次（如果还没调用）"""
        if self.death_callback and not self.death_counted:
            self.death_callback(self)
            self.death_counted = True
        super().kill()


class OpeningZombie(Zombie):
    """开场动画僵尸：根据类型展示不同的僵尸外观。"""
    def __init__(self, x, y, row, scale=1.0, zombie_type='normal'):
        from resources import Resources
        from settings import CELL_WIDTH, CELL_HEIGHT
        target_width = max(1, int(CELL_WIDTH * scale))
        target_height = max(1, int(CELL_HEIGHT * scale))
        size = (target_width, target_height)

        # 加载普通僵尸动画（所有类型都基于普通僵尸动画）
        full_animations = Resources.load_zombie_animations(size=size)

        super().__init__(x, y, row, full_animations,
                         anim_speed=0.1,
                         health=999999,
                         speed=0,
                         chomp_sounds=[])

        # 自定义动画序列（用于展示）
        walk_frames = full_animations['walk']
        selected_indices = [0, 1, 2, 3, 20, 21, 20, 3, 2, 1]
        self.anim_frames = [walk_frames[i] for i in selected_indices]
        self.anim_index = 0
        self.image = self.anim_frames[0]
        self.state = self.STATE_WALK

        self.zombie_type = zombie_type
        self.equipment_image = None  # 装备图片（帽子、铁桶等）
        self.equipment_offset = (0, 0)

        if zombie_type == 'conehead':
            # 加载路障帽子图片（使用完好帽子 Zombie_cone1.png）
            try:
                raw_cone = Resources.load_image("zombie_cone/Zombie_cone1.png")
                # 缩放到合适大小（与原僵尸帧比例一致）
                cone_scaled = pygame.transform.scale(raw_cone,
                    (int(raw_cone.get_width() * scale*0.6), int(raw_cone.get_height() * scale*0.6)))
                self.equipment_image = cone_scaled
                self.equipment_offset=(50,-5)
            except Exception as e:
                print(f"加载路障帽子图片失败: {e}")

        elif zombie_type == 'bucket':
            try:
                raw_bucket = Resources.load_image("zombie_bucket/Zombie_bucket1.png")
                # 缩放到合适大小（与原僵尸帧比例一致）
                bucket_scaled = pygame.transform.scale(raw_bucket,
                    (int(raw_bucket.get_width() * scale*0.6), int(raw_bucket.get_height() * scale*0.6)))
                self.equipment_image = bucket_scaled
                self.equipment_offset = (40, 0)
            except Exception as e:
                print(f"加载铁通帽子图片失败: {e}")

    def update(self, now, *args):
        self._update_animation(now)
        # 如果是路障僵尸，叠加帽子
        if self.equipment_image:
            combined = self.image.copy()
            combined.blit(self.equipment_image, self.equipment_offset)
            self.image = combined


class NormalZombie(Zombie):
    SPEED_MEAN = ZOMBIE_BASE_SPEED
    SPEED_STD = 0.05

    def __init__(self, x, y, row, scale=1.0, speed=None, chomp_sounds=None, start_time=0):
        target_width = max(1, int(CELL_WIDTH * scale))
        target_height = max(1, int(CELL_HEIGHT * scale))
        size = (target_width, target_height)

        anims = Resources.load_zombie_animations(size=size)

        first_frame = anims['walk'][0]
        img_height = first_frame.get_height()
        ground_y = y + CELL_HEIGHT
        adjusted_y = ground_y - img_height

        if speed is None:
            speed = random.gauss(self.SPEED_MEAN, self.SPEED_STD)
            speed = max(0.1, min(0.5, speed))

        super().__init__(x, adjusted_y, row, anims, anim_speed=0.1, health=270, speed=speed, chomp_sounds=chomp_sounds, start_time=start_time)

    def randomize_speed(self):
        speed = random.gauss(self.SPEED_MEAN, self.SPEED_STD)
        return max(0.1, min(0.5, speed))


class FlagZombie(Zombie):
    SPEED_MEAN = ZOMBIE_BASE_SPEED
    SPEED_STD = 0.05

    def __init__(self, x, y, row, scale=1.0, speed=None, chomp_sounds=None, start_time=0):
        target_width = max(1, int(CELL_WIDTH * scale))
        target_height = max(1, int(CELL_HEIGHT * scale))
        size = (target_width, target_height)

        anims = Resources.load_flagzombie_animations(size=size)

        first_frame = anims['walk'][0]
        img_height = first_frame.get_height()
        ground_y = y + CELL_HEIGHT
        adjusted_y = ground_y - img_height

        if speed is None:
            speed = random.gauss(self.SPEED_MEAN, self.SPEED_STD)
            speed = max(0.1, min(0.5, speed))

        super().__init__(x, adjusted_y, row, anims,
                         anim_speed=0.1,
                         health=350,
                         speed=speed,
                         chomp_sounds=chomp_sounds, start_time=start_time)

    def randomize_speed(self):
        speed = random.gauss(self.SPEED_MEAN, self.SPEED_STD)
        return max(0.1, min(0.5, speed))


class ZombieHead(pygame.sprite.Sprite):
    """僵尸被碾压后飞出的头"""
    def __init__(self, x, y, row,ground_y):
        super().__init__()
        # 加载头图片
        try:
            raw_image = Resources.load_image("zombie/ZombieHead.png")
            self.image = raw_image
        except Exception as e:
            # 备用：创建一个圆形
            self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (150, 75, 0), (15, 15), 15)
        scale = 0.7
        new_size = (int(raw_image.get_width() * scale), int(raw_image.get_height() * scale))
        self.original_image = pygame.transform.scale(raw_image, new_size)
        self.image = self.original_image

        self.rect = self.image.get_rect()
        # 初始世界坐标（从身体位置偏移一点）
        self.world_x = x + 30
        self.world_y = y - 20
        self.row = row
        self.ground_y = ground_y
        # 物理参数
        self.vx = random.uniform(-50, 50)      # 像素/秒
        self.vy = random.uniform(-200, -150)
        self.gravity = 400
        # self.life = 2.0                         # 存活时间（秒）
        self.angle = 0.0
        self.angular_velocity = random.uniform(-180, 180)  # 度/秒

        self.landed = False
        self.land_time = None
        self.linger_duration = 2000  # 停留2秒

        self.last_update = None                # 用于计算 dt

    def update(self, now, *args):
        # 计算时间差（使用 now 计算 dt）
        if self.last_update is None:
            self.last_update = now
            dt = 0
        else:
            dt = (now - self.last_update) / 1000.0  # 转换为秒
            self.last_update = now

        if not self.landed:
            # 飞行状态：更新物理
            self.world_x += self.vx * dt
            self.world_y += self.vy * dt
            self.vy += self.gravity * dt
            self.angle += self.angular_velocity * dt

            # 检测落地：头的底部接触到地面
            head_bottom = self.world_y + self.original_image.get_height()
            if head_bottom >= self.ground_y and self.vy > 0:
                # 落地
                self.landed = True
                self.land_time = now
                # 停止运动
                self.vx = 0
                self.vy = 0
                self.gravity = 0
                self.angular_velocity = 0
                # 调整位置使头刚好接触地面
                self.world_y = self.ground_y - self.original_image.get_height()
        else:
            # 落地停留状态：检查是否超过停留时间
            if now - self.land_time >= self.linger_duration:
                self.kill()
                return

            # 更新图像旋转
        if self.angular_velocity != 0 or self.angle != 0:
            # 旋转图像
            rotated = pygame.transform.rotate(self.original_image, self.angle)
            # 保持中心位置不变（旋转后rect会变化）
            center = (self.world_x + self.original_image.get_width() // 2,
                      self.world_y + self.original_image.get_height() // 2)
            self.image = rotated
            self.rect = rotated.get_rect(center=center)
        else:
            # 无旋转时直接使用原始图像，位置保持
            self.image = self.original_image
            self.rect.topleft = (self.world_x, self.world_y)


# ---------- 新增：掉落防具类 ----------
class DroppedHat(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, end_x, end_y, image, start_time,
                 fall_duration=500, linger_duration=2000, row=0):
        super().__init__()
        self.image = image
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.start_time = start_time
        self.fall_duration = fall_duration
        self.linger_duration = linger_duration
        self.total_duration = fall_duration + linger_duration
        self.row = row
        self.world_x = start_x
        self.world_y = start_y
        self.rect = self.image.get_rect(topleft=(start_x, start_y))

    def update(self, now, *args):
        elapsed = now - self.start_time
        if elapsed >= self.total_duration:
            self.kill()
            return

        if elapsed < self.fall_duration:
            # 下落阶段：线性插值
            t = elapsed / self.fall_duration
            self.world_x = self.start_x + (self.end_x - self.start_x) * t
            self.world_y = self.start_y + (self.end_y - self.start_y) * t
        else:
            # 停留阶段：固定在终点
            self.world_x = self.end_x
            self.world_y = self.end_y

class ConeheadZombie(NormalZombie):
    """路障僵尸：继承普通僵尸，叠加路障图片，血量更高，帽子随血量变化，并增加掉落动画"""
    def __init__(self, x, y, row, scale=1.0, speed=None, chomp_sounds=None, start_time=0, cone_scale=1, group=None):
        super().__init__(x, y, row, scale, speed, chomp_sounds, start_time)
        self.hat_dropped = False
        # 提高总血量
        self.max_health = 670
        self.health = self.max_health

        # 加载三张路障图片，使用独立缩放比例 cone_scale
        self.cone_images = []
        for i in range(1, 4):
            try:
                raw_img = Resources.load_image(f"zombie_cone/Zombie_cone{i}.png")
                # 根据 cone_scale 缩放（相对于原始尺寸）
                new_size = (int(raw_img.get_width() * cone_scale), int(raw_img.get_height() * cone_scale))
                scaled_img = pygame.transform.scale(raw_img, new_size)
                self.cone_images.append(scaled_img)
            except Exception as e:
                print(f"加载路障图片 {i} 失败: {e}")
                # 如果加载失败，创建一个透明占位图
                placeholder = pygame.Surface((1,1), pygame.SRCALPHA)
                self.cone_images.append(placeholder)

        self.cone_index = 0
        # 帽子相对于僵尸图像左上角的偏移量（需根据实际图片微调）
        self.hat_offset = (55, -5)  # 示例值，请根据视觉效果调整

        # 掉落动画相关
        self.dropped_hat = None      # 当前掉落的帽子精灵
        self.group = group           # 用于添加掉落物的精灵组

    def update(self, now, *args):
        super().update(now, *args)

        # 检查是否触发掉落动画（生命值≤270 且尚未触发且不是死亡/碾压状态）
        if self.health <= 270 and self.dropped_hat is None and self.state not in (self.STATE_DIE, self.STATE_SQUASHED) and not self.hat_dropped:
            self._start_hat_drop(now)
            self.hat_dropped=True
        # 如果掉落物已死亡，清空引用
        if self.dropped_hat and not self.dropped_hat.alive():
            self.dropped_hat = None

        # 死亡或碾压时不叠加帽子
        if self.state in (self.STATE_DIE, self.STATE_SQUASHED):
            return

        # 如果已经触发了掉落，不再绘制帽子
        if self.dropped_hat is not None:
            return

        # 血量低于 270 时无帽子（理论上此时应有掉落物，但以防万一）
        if self.health <= 270:
            return

        # 根据剩余血量选择帽子状态
        if self.health > 470:
            cone_idx = 0          # 完好
        elif self.health > 370:
            cone_idx = 1          # 破损一点
        else:
            cone_idx = 2          # 破损很多

        # 如果索引改变，重新合成图像（也可以每次都合成）
        if cone_idx != self.cone_index:
            self.cone_index = cone_idx

        # 合成：将当前僵尸帧复制，然后在指定偏移位置绘制帽子
        combined = self.image.copy()
        combined.blit(self.cone_images[self.cone_index], self.hat_offset)
        self.image = combined

    def _start_hat_drop(self, now):
        hat_img = self.cone_images[2]
        # 旋转90度（让帽子平躺）
        rotated_hat = pygame.transform.rotate(hat_img, 90)

        # 起始位置（从僵尸头上帽子位置开始）
        start_x = self.world_x + self.hat_offset[0]
        start_y = self.world_y + self.hat_offset[1]

        # 计算僵尸身体水平中心，用于终点定位
        raw_center_x = self.world_x + self.rect.width // 2
        # 随机偏移量（水平 ±15 像素，垂直 ±5 像素）
        rand_x = random.randint(-15, 15)
        rand_y = random.randint(-5, 5)

        # 终点：旋转后图像底部对齐地面，水平居中附近加随机偏移
        end_x = raw_center_x - rotated_hat.get_width() // 2 + rand_x
        end_y = self.world_y + self.rect.height - rotated_hat.get_height() + rand_y+15

        self.dropped_hat = DroppedHat(
            start_x, start_y, end_x, end_y, rotated_hat, now,
            fall_duration=500, linger_duration=2000, row=self.row
        )
        if self.group:
            self.group.add(self.dropped_hat)
        self.hat_dropped = True
    def kill(self):
        """确保掉落物一同消失"""
        if self.dropped_hat and self.dropped_hat.alive():
            self.dropped_hat.kill()
        super().kill()


class BucketZombie(NormalZombie):
    """铁桶僵尸：继承普通僵尸，叠加铁桶图片，血量更高，帽子随血量变化，并增加掉落动画"""
    def __init__(self, x, y, row, scale=1.0, speed=None, chomp_sounds=None, start_time=0, cone_scale=1, group=None):
        super().__init__(x, y, row, scale, speed, chomp_sounds, start_time)
        self.hat_dropped = False
        # 提高总血量
        self.max_health = 1370
        self.health = self.max_health

        # 加载三张铁桶图片，使用独立缩放比例 cone_scale
        self.bucket_images = []
        for i in range(1, 4):
            try:
                raw_img = Resources.load_image(f"zombie_bucket/Zombie_bucket{i}.png")
                # 根据 cone_scale 缩放（相对于原始尺寸）
                new_size = (int(raw_img.get_width() * cone_scale), int(raw_img.get_height() * cone_scale))
                scaled_img = pygame.transform.scale(raw_img, new_size)
                self.bucket_images.append(scaled_img)
            except Exception as e:
                print(f"加载铁桶图片 {i} 失败: {e}")
                # 如果加载失败，创建一个透明占位图
                placeholder = pygame.Surface((1,1), pygame.SRCALPHA)
                self.bucket_images.append(placeholder)

        self.cone_index = 0
        # 帽子相对于僵尸图像左上角的偏移量（需根据实际图片微调）
        self.hat_offset = (40, 5)  # 示例值，请根据视觉效果调整

        # 掉落动画相关
        self.dropped_hat = None
        self.group = group

    def update(self, now, *args):
        super().update(now, *args)

        # 检查是否触发掉落动画（生命值≤270 且尚未触发且不是死亡/碾压状态）
        if self.health <= 270 and self.dropped_hat is None and self.state not in (self.STATE_DIE, self.STATE_SQUASHED) and not self.hat_dropped:
            self._start_hat_drop(now)
            self.hat_dropped=True

        if self.dropped_hat and not self.dropped_hat.alive():
            self.dropped_hat = None

        if self.state in (self.STATE_DIE, self.STATE_SQUASHED):
            return

        if self.dropped_hat is not None:
            return

        if self.health <= 270:
            return

        # 根据剩余血量选择帽子状态
        if self.health > 870:
            cone_idx = 0          # 完好
        elif self.health > 570:
            cone_idx = 1          # 破损一点
        else:
            cone_idx = 2          # 破损很多

        if cone_idx != self.cone_index:
            self.cone_index = cone_idx

        combined = self.image.copy()
        combined.blit(self.bucket_images[self.cone_index], self.hat_offset)
        self.image = combined

    def _start_hat_drop(self, now):
        hat_img = self.bucket_images[2]
        rotated_hat = pygame.transform.rotate(hat_img, 90)

        start_x = self.world_x + self.hat_offset[0]
        start_y = self.world_y + self.hat_offset[1]

        raw_center_x = self.world_x + self.rect.width // 2
        rand_x = random.randint(-15, 15)
        rand_y = random.randint(-5, 5)

        end_x = raw_center_x - rotated_hat.get_width() // 2 + rand_x
        end_y = self.world_y + self.rect.height - rotated_hat.get_height() + rand_y+15

        self.dropped_hat = DroppedHat(
            start_x, start_y, end_x, end_y, rotated_hat, now,
            fall_duration=500, linger_duration=2000, row=self.row
        )
        if self.group:
            self.group.add(self.dropped_hat)
        self.hat_dropped = True

    def kill(self):
        if self.dropped_hat and self.dropped_hat.alive():
            self.dropped_hat.kill()
        super().kill()