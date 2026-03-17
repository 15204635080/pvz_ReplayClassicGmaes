import pygame
import os
from resources import Resources
from settings import IMAGE_DIR, SCREEN_WIDTH, SCREEN_HEIGHT

# 核心修复：明确戴夫的固定屏幕坐标（替代混淆的视口偏移）
DAVE_SCREEN_X =  0 # 戴夫对话时的固定屏幕左侧坐标（目标86）
DAVE_MOVE_SPEED = 100  # 移动速度（像素/秒），可调整


class DaveSequence:
    """
    戴夫对话管理器（帧序列版）
    修复：1. 固定屏幕坐标86；2. 移动时无中间闪烁；3. 帧顺序正常
    """

    def __init__(self, frame_dir, sound_files, frame_ext=".png", frame_digits=3):
        """
        frame_dir: 帧图片所在目录（相对于 IMAGE_DIR），如 "crazydave"
        sound_files: 音频文件名列表，顺序为 [extralong1, extralong2, extralong3, crazy]
        """
        self.frame_dir = frame_dir
        self.frames = []  # 所有帧（索引0~12）
        self.load_all_frames()
        self.sounds = []
        for fname in sound_files:
            snd = Resources.load_sound(fname)
            self.sounds.append(snd)

        # 定义每次点击对应的帧索引序列
        self.phase_frames = [
            [0, 1, 7, 6, 8, 9, 10, 11, 12],  # 第1次点击（9帧）
            [0, 1, 7, 6, 8, 9, 10, 11, 12],  # 第2次点击
            [0, 1, 7, 6, 8, 9, 10, 11, 12],  # 第3次点击
            list(range(13))  # 第4次点击（0~12，13帧）
        ]

        # 状态管理
        self.state = 'idle'  # idle, animating, moving
        self.current_phase = 0  # 0~3
        self.current_frame = 0  # 当前显示的帧索引（0~12）
        self.anim_start_time = 0
        self.anim_duration = 0  # 当前动画总时长（毫秒）
        self.frame_duration = 0  # 当前动画每帧时长（毫秒）
        self.anim_frame_indices = []  # 当前动画的帧索引序列
        self.current_frame_index_in_anim = 0  # 动画内的帧索引
        self.last_update_time = 0  # 上一次切帧的时间戳

        # 移动相关（核心修复：基于固定屏幕坐标）
        self.move_x = DAVE_SCREEN_X  # 移动时的实时x坐标（初始为固定86）
        self.move_start_time = 0
        self.finished_moving = False

        # 字体（用于提示）
        try:
            self.font = pygame.font.SysFont("simhei", 40)
        except:
            self.font = pygame.font.Font(None, 40)

    def load_all_frames(self):
        """加载所有13帧图片（frame_000.png 到 frame_012.png）"""
        for i in range(13):
            filename = f"frame_{i:03d}.png"
            path = os.path.join(self.frame_dir, filename)
            try:
                img = Resources.load_image(path, alpha=True)
                self.frames.append(img)
            except Exception as e:
                print(f"无法加载帧图片: {path}, 错误: {e}")
                # 创建占位表面（便于调试）
                surf = pygame.Surface((400, 200))
                surf.fill((255, 0, 255))  # 品红占位，提示缺失图片
                self.frames.append(surf)

    def handle_click(self):
        """处理鼠标点击，根据状态执行动作"""
        now = pygame.time.get_ticks()
        if self.state == 'idle':
            if self.current_phase < 4:
                # 开始新动画
                self.start_animation(self.current_phase)
                return False
            else:
                # 四次对话完成，启动移动（核心修复：直接基于固定x初始化）
                self.state = 'moving'
                self.move_start_time = now

                # 移动目标：x = -当前帧宽度（完全移出屏幕左侧）
                self.move_x = DAVE_SCREEN_X
                # 使用闭嘴帧的宽度计算目标位置
                self.move_target_x = -self.frames[0].get_width()
                self.finished_moving = False
                return False
        elif self.state in ('animating', 'moving'):
            # 动画/移动期间点击无效
            return False
        return False

    def start_animation(self, phase):
        """开始指定阶段的动画"""
        now = pygame.time.get_ticks()
        self.state = 'animating'
        self.current_phase = phase
        self.anim_frame_indices = self.phase_frames[phase]
        self.current_frame_index_in_anim = 0  # 强制从第0帧开始
        self.current_frame = self.anim_frame_indices[self.current_frame_index_in_anim]

        # 音频与帧时长配置
        sound = self.sounds[phase]
        audio_len = sound.get_length()  # 秒
        self.anim_duration = audio_len * 1000  # 毫秒
        self.frame_duration = self.anim_duration / len(self.anim_frame_indices)

        # 重置时间戳，避免跳帧
        self.anim_start_time = now
        self.last_update_time = now

        # 播放音频
        sound.play()

    def update(self, now):
        """更新动画/移动状态（核心：仅修改需要变化的参数）"""
        now = pygame.time.get_ticks()
        if self.state == 'animating':
            total_elapsed = now - self.anim_start_time

            # 动画结束判断
            if total_elapsed >= self.anim_duration:
                self.state = 'idle'
                self.current_frame = 0  # 切回闭嘴帧
                self.current_phase = self.current_phase + 1 if self.current_phase < 3 else 4
                return

            # 增量式切帧（避免跳帧）
            frame_elapsed = now - self.last_update_time
            if frame_elapsed >= self.frame_duration:
                self.current_frame_index_in_anim += 1
                self.current_frame_index_in_anim = min(self.current_frame_index_in_anim,
                                                       len(self.anim_frame_indices) - 1)
                self.current_frame = self.anim_frame_indices[self.current_frame_index_in_anim]
                self.last_update_time += self.frame_duration

        elif self.state == 'moving':
            # 核心修复：从固定86坐标平滑左移，无中间闪烁
            elapsed = now - self.move_start_time  # 毫秒
            elapsed_seconds = elapsed / 1000.0  # 秒

            # 计算实时x坐标：从86向左侧目标移动
            distance_moved = DAVE_MOVE_SPEED * elapsed_seconds
            self.move_x = DAVE_SCREEN_X - distance_moved

            # 移动完成判断（完全移出屏幕）
            if self.move_x <= self.move_target_x:
                self.move_x = self.move_target_x  # 固定最终位置
                self.finished_moving = True
                self.state = 'idle'

    def draw(self, screen):
        """绘制戴夫（核心：固定初始x=86，移动时仅修改move_x）"""
        # 确定最终显示的x坐标：动画时固定86，移动时用实时move_x
        if self.state == 'moving' and not self.finished_moving:
            draw_x = self.move_x
        else:
            draw_x = DAVE_SCREEN_X  # 始终固定在86，无中间闪烁

        # 垂直居中（保持原有逻辑）
        frame = self.frames[self.current_frame]
        draw_y = (SCREEN_HEIGHT - frame.get_height()) // 2

        # 绘制帧（坐标完全基于屏幕像素，无混淆）
        screen.blit(frame, (draw_x, draw_y))
        # print(f"state={self.state}, draw_x={draw_x}, move_x={self.move_x}")
        # 绘制提示文字（仅idle/moving时显示）
        if self.state == 'idle' or (self.state == 'moving' and not self.finished_moving):
            text = self.font.render("press any key to continue", True, (0, 0, 0))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
            screen.blit(text, text_rect)

    def reset(self):
        """重置所有状态（重新开始游戏时调用）"""
        self.state = 'idle'
        self.current_phase = 0
        self.current_frame = 0
        self.current_frame_index_in_anim = 0
        self.last_update_time = 0
        self.move_x =DAVE_SCREEN_X  # 重置移动坐标到86
        self.finished_moving = False