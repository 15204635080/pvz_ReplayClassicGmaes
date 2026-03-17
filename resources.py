# resources.py
import os
import sys
import pygame
from settings import IMAGE_DIR, SOUND_DIR

class Resources:
    _images = {}
    _animations = {}  # 缓存已加载的动画帧列表
    _sounds = {}      # 缓存音效对象

    @classmethod
    def get_base_path(cls):
        """获取资源基础路径：开发时返回当前目录，打包后返回 exe 所在目录"""
        if getattr(sys, 'frozen', False):
            # 打包后，sys.executable 是 exe 的完整路径
            return os.path.dirname(sys.executable)
        else:
            # 开发环境，返回当前工作目录
            return os.path.abspath(".")

    @classmethod
    def resource_path(cls, relative_path):
        """返回资源的绝对路径（相对于基础路径）"""
        return os.path.join(cls.get_base_path(), relative_path)

    @classmethod
    def load_sound(cls, filename):
        """
        加载音效文件（相对 SOUND_DIR 路径），返回 pygame.mixer.Sound 对象。
        如果加载失败，返回 None 并打印警告。
        """
        full_path = cls.resource_path(os.path.join(SOUND_DIR, filename))
        if full_path not in cls._sounds:
            try:
                sound = pygame.mixer.Sound(full_path)
            except pygame.error as e:
                print(f"无法加载音效: {full_path}, 错误: {e}")
                sound = None
            cls._sounds[full_path] = sound
        return cls._sounds[full_path]

    @classmethod
    def load_image(cls, path, size=None, alpha=True):
        """
        加载单张图片，path 是相对于 IMAGE_DIR 的路径。
        例如 "peashooter/Peashooter_00.png"
        """
        full_path = cls.resource_path(os.path.join(IMAGE_DIR, path))
        if full_path not in cls._images:
            try:
                if alpha:
                    image = pygame.image.load(full_path).convert_alpha()
                else:
                    image = pygame.image.load(full_path).convert()
            except pygame.error as e:
                print(f"无法加载图片: {full_path}")
                raise e
            cls._images[full_path] = image
        else:
            image = cls._images[full_path]

        if size:
            return pygame.transform.scale(image, size)
        return image

    @classmethod
    def load_animation(cls, folder, prefix, count, start_index=0, digits=2, extension="png", size=None):
        """
        加载一个动画序列帧。
        folder: 相对于 IMAGE_DIR 的文件夹，如 "peashooter"
        prefix: 文件名前缀，如 "Peashooter_"
        count: 帧数
        start_index: 起始编号，默认为0
        digits: 编号位数，如2表示两位数字（00,01...）
        extension: 文件扩展名，默认png
        size: 缩放尺寸
        返回帧列表（pygame.Surface）
        """
        key = (folder, prefix, count, start_index, digits, size)  # 缓存键
        if key in cls._animations:
            return cls._animations[key]

        frames = []
        for i in range(start_index, start_index + count):
            filename = f"{prefix}{i:0{digits}d}.{extension}"
            path = os.path.join(folder, filename)
            frame = cls.load_image(path, size)
            frames.append(frame)

        cls._animations[key] = frames
        return frames

    @classmethod
    def load_zombie_animations(cls, size=None):
        """加载普通僵尸的所有动画状态，返回字典"""
        walk_frames = cls.load_animation("zombie", "Zombie_", 22, start_index=0, digits=1, extension="png", size=size)
        attack_frames = cls.load_animation("zombie", "ZombieAttack_", 21, start_index=0, digits=1, extension="png", size=size)
        die_frames = cls.load_animation("zombie", "ZombieDie_", 10, start_index=0, digits=1, extension="png", size=size)
        return {
            "walk": walk_frames,
            "attack": attack_frames,
            "die": die_frames
        }

    @classmethod
    def load_flagzombie_animations(cls, size=None):
        """加载旗帜僵尸动画，返回字典包含 walk, attack, die（die 复用普通僵尸死亡动画）"""
        walk_frames = cls.load_animation("flag_zombie", "FlagZombie_", 12, start_index=0, digits=1, extension="png", size=size)
        attack_frames = cls.load_animation("flag_zombie", "FlagZombieAttack_", 11, start_index=0, digits=1, extension="png", size=size)
        die_frames = cls.load_animation("zombie", "ZombieDie_", 10, start_index=0, digits=1, extension="png", size=size)
        return {
            "walk": walk_frames,
            "attack": attack_frames,
            "die": die_frames
        }