#game.py
import random
import math
import json
import os
from settings import *
from resources import *
from entities.plant import *
from entities.zombie import *
from entities.bullet import *
from entities.lawn import *
from entities.dave_sequence import *
from entities.sun import *        # 新增：导入阳光类
from entities.wave_manager import *
from entities.mower import *
from entities.charred import *
import sys


def get_base_path():
    """sys.frozen是打包工具pyinstaller添加的属性，
    如果这里有frozen属性说明目前处于exe环境，返回true
    如果没有该属性，说明还处于Python开发环境，返回false"""
    if getattr(sys, 'frozen', False):
        # 打包后，返回 exe 所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发环境，返回 game.py 所在目录（即项目根目录）
        return os.path.dirname(os.path.abspath(__file__))



# 关卡配置（索引 0,1,2 分别对应三关）
LEVELS = [
    { # 关卡1
        'waves': [
            ({"normal": 5}, False),  # 第一波：5个普通
            ({"normal": 4}, False),
            ({"normal": 3}, False),
            ({"normal": 5}, True),
        ],
        'first_spawn_interval': 20.0,
        'last_spawn_interval': 5.0,
        'first_spawn_time': 30000,
        'emergency_multiplier': 1.5,
        'flag_followers_min': 5,
        'flag_followers_max': 10
    },
    { # 关卡2
        'waves': [
            ({"normal": 5}, False),
            ({"normal": 7, "conehead": 4}, False),
            ({"normal": 3}, False),
            ({"normal": 7, "conehead": 4}, True),
            ({"normal": 7, "conehead": 5}, True),
        ],
        'first_spawn_interval': 20.0,
        'last_spawn_interval': 1.0,
        'first_spawn_time': 30000,
        'emergency_multiplier': 1.5,
        'flag_followers_min': 5,
        'flag_followers_max': 10
    },
    { # 关卡3
        'waves': [
            ({"normal": 5, "bucket": 2}, False),
            ({"normal": 3, "conehead": 13}, False),
            ({"normal": 10, "bucket": 2}, False),
            ({"normal": 7, "conehead": 13, "bucket": 20}, False),
            ({"normal": 7, "conehead": 4}, True),
            ({"normal": 7, "conehead": 5}, True),
            ({"normal": 7, "conehead": 6}, True),
            ({"normal": 7, "conehead": 7}, True),
            ({"normal": 7, "conehead": 8}, True),
            ({"normal": 7, "conehead": 9}, True),
            ({"normal": 6, "conehead": 10}, True),
            ({"normal": 5, "conehead": 11}, True),
            ({"normal": 4, "conehead": 12}, True),
            ({"normal": 3, "conehead": 13}, True),
            ({"normal": 2, "conehead": 14}, True),
            ({"normal": 1, "conehead": 15}, True),
            ({"normal": 0, "conehead": 16}, True),
            ({"normal": 0, "conehead": 18}, True),
            ({"normal": 0, "conehead": 20}, True),
            ({"normal": 0, "conehead": 22}, True),
            ({"normal": 0, "conehead": 24}, True),
            ({"normal": 0, "conehead": 26}, True),
            ({"normal": 0, "conehead": 28}, True),
            ({"normal": 0, "conehead": 30}, True),
        ],
        'first_spawn_interval': 20.0,
        'last_spawn_interval': 1.0,
        'first_spawn_time': 30000,
        'emergency_multiplier': 1.5,
        'flag_followers_min': 20,
        'flag_followers_max': 30
    }
]







class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)#创建一个 Pygame 的时钟对象，用于控制游戏的帧率（FPS）
        self.clock = pygame.time.Clock()
        self.running = True
        #是否保留图片的透明通道（Alpha 通道）。False 表示不保留（背景图一般是不透明的，不需要透明通道）；如果是精灵、特效等图片，会设为 True 来保留透明效果。
        self.full_background = Resources.load_image("screen/background.jpg",
                                                    (BACKGROUND_WIDTH, BACKGROUND_HEIGHT),
                                                    alpha=False)
        #JPG 格式本身就没有 Alpha 通道，所以给背景图设 alpha=False 是合理的，即使设为 True 也不会有透明效果。
        #游戏角色、道具、特效、按钮等需要抠图的图片（通常是 PNG 格式，因为 PNG 支持 Alpha 通道）
        self.gameover_raw_image = Resources.load_image("screen/GameOver.png", alpha=True)
        self.gameover_delay_start = None
        self.GAMEOVER_DELAY = 2500  # 延迟一坤秒展示screen/GameOver.png
        self.gameover_visible = False
        self.gameover_image = None
        self.gameover_scale = 0.3  #最开始展示screen/GameOver.png图片是原始的0.3倍
        self.gameover_scale_speed = 0.005 #以0.005每帧扩大
        self.gameover_anim_finished = False
        self.show_health_bars = True#僵尸血量显示，按2切换

        self.font_chinese = None
        # 尝试加载内置字体文件
        font_path = os.path.join(get_base_path(), "fonts", "simhei.ttf")  # 如果使用 simhei.ttf
        # 如果你用的是 NotoSansSC-Regular.ttf，就改成对应的文件名
        # font_path = os.path.join(get_base_path(), "fonts", "NotoSansSC-Regular.ttf")

        if os.path.exists(font_path):
            try:
                self.font_chinese = pygame.font.Font(font_path, 30)
                # 测试渲染，确保字体有效
                test_surf = self.font_chinese.render("测试", True, (255, 255, 255))
                if test_surf.get_width() == 0:
                    raise ValueError("字体渲染宽度为0")
            except Exception as e:
                print(f"内置字体加载失败，将尝试系统字体: {e}")
                self.font_chinese = None
        else:
            print(f"内置字体文件未找到: {font_path}，尝试系统字体")


        if self.font_chinese is None:
            # 尝试加载中文字体，按优先级尝试
            font_names = ["simhei", "Microsoft YaHei", "SimHei", "Arial Unicode MS", "Noto Sans CJK SC"]
            self.font_chinese = None
            for name in font_names:
                try:
                    font = pygame.font.SysFont(name, 30)
                    # 测试渲染一个中文字符，如果渲染出来的字符宽度为0或没有正确渲染，则失败
                    test_surf = font.render("测试", True, (255, 255, 255))
                    if test_surf.get_width() > 0:
                        self.font_chinese = font
                        break
                except:
                    continue
            if self.font_chinese is None:
                # 最后尝试使用默认字体（可能无法显示中文，但至少不崩溃）
                self.font_chinese = pygame.font.Font(None, 30)
                print("警告：未找到合适的中文字体，将使用默认字体，中文可能显示为方块")

        self.state = 'intro' #introduction 开场，序幕
        self.viewport_x = VIEWPORT_RIGHT_OFFSET#开场移动之后最左侧位于BACKGROUND_WIDTH位置

        self.all_sprites = pygame.sprite.Group()
        self.plants = pygame.sprite.Group()
        self.zombies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.sun_sprites = pygame.sprite.Group()
        self.opening_zombies = pygame.sprite.Group()#开场之前晃悠的僵尸
        self.opening_zombies_created = False
        self.lawn = LawnGrid()
        self.mowers = pygame.sprite.Group()  # 新增：小推车组


        # 阳光系统属性
        self.sun_amount = 100                                # 初始阳光数量
        self.last_sun_drop = 0                              # 上次自然掉落时间
        self.sun_font = pygame.font.Font(None, 30)          # 用于显示阳光数量的字体
        # 阳光UI背景图
        try:
            self.seed_bank_img = Resources.load_image(SEED_BANK_IMAGE)
            # 缩放至合适大小（例如宽度150，高度自动）
            self.seed_bank_img = pygame.transform.scale(self.seed_bank_img, (seedbank_x, seedbank_y+5))
        except Exception as e:
            print(f"无法加载 SeedBank.png: {e}")
            self.seed_bank_img = None

        # 卡片图标
        try:
            self.peashooter_card_img = Resources.load_image(CARD_PEASHOOTER_ICON, size=(CARD_WIDTH, CARD_HEIGHT))
            self.sunflower_card_img = Resources.load_image(CARD_SUNFLOWER_ICON, size=(CARD_WIDTH, CARD_HEIGHT))
            self.cherrybomb_card_img=Resources.load_image(CARD_CHERRYBOMB_ICON,size=(CARD_WIDTH,CARD_HEIGHT))
            self.wallnut_card_img=Resources.load_image(CARD_WALLNUT_ICON, size=(CARD_WIDTH, CARD_HEIGHT))
        except Exception as e:
            print(f"无法加载卡片图标: {e}")
            # 备用：创建彩色方块
            self.peashooter_card_img = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            self.peashooter_card_img.fill((0, 255, 0))  # 绿色
            self.sunflower_card_img = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            self.sunflower_card_img.fill((255, 255, 0))  # 黄色
            self.wallnut_card_img = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            self.wallnut_card_img.fill((255, 255, 255))  #
            self.cherrybomb_card_img = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            self.cherrybomb_card_img.fill((255, 0, 0))  # 红色方块备用

        #rect是矩形对象，传入左上角xy坐标以及卡片宽，高
        self.card_rects = [#代表两张卡片
            pygame.Rect(CARD_START_X-10, CARD_START_Y, CARD_WIDTH, CARD_HEIGHT),
            pygame.Rect(CARD_START_X-10 + CARD_WIDTH + CARD_SPACING, CARD_START_Y, CARD_WIDTH, CARD_HEIGHT),
            pygame.Rect(CARD_START_X-10 + CARD_WIDTH*2 + CARD_SPACING*2, CARD_START_Y, CARD_WIDTH, CARD_HEIGHT),
            pygame.Rect(CARD_START_X-10 + CARD_WIDTH * 3 + CARD_SPACING * 3, CARD_START_Y, CARD_WIDTH, CARD_HEIGHT)
        ]

        # 当前选中的卡片索引：0=豌豆射手，1=向日葵，2=坚果 None=未选中
        self.selected_card = None
#这个还没有处理
        self.start_button_rect = pygame.Rect(SCREEN_WIDTH//2 - 100,
                                             SCREEN_HEIGHT//2 - 40,
                                             200, 80)
        self.fail_anim_start = 0
        self.fail_anim_duration = 2500#视角向左移动这个动画一坤秒
        self.leftmost_zombie = None#用于检测谁先进家

        self.paused = False
        self.show_health_bars = True
        self.health_font = pygame.font.Font(None, 18)

        # 旗帜僵尸以及后续所有僵尸生成逻辑
        # self.flag_zombie_spawned = False
        # （已解决）本关所有僵尸生成逻辑，需要改进，这个waves所有数量加一起大于total_zombie，游戏正常运行，但是进度显示错误

        self.load_user_data()  # 新增
        self.current_level = None  # 新增：当前正在进行的关卡索引

        # 界面按钮（用于 intro 状态）
        self.new_game_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 60, 200, 50)
        self.continue_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 10, 200, 50)





        self.game_start_time = 0  # 记录游戏开始时间

        # 背景音乐
        # 背景音乐文件列表（索引 0~3）
        self.BGM_FILES = [
            "game_running_0.mp3",
            "game_running_1.mp3",
            "game_running_2.mp3",
            "game_running_3.mp3"
        ]
        self.current_bgm_index = None  # 当前正在播放的音乐索引
        self.bgm_phase = None  # 当前阶段：'intro', 'battle_part1', 'battle_part2', 'stopped'
        self.bgm_part2_choice = None  # 后半段随机选择的索引（2 或 3）

        # 失败音效
        self.lose_sound = None
        self.lose_played = False
        try:
            self.lose_sound = Resources.load_sound("lose.mp3")
        except Exception as e:
            print(f"失败音效无法加载: {e}")

        # 啃咬音效
        self.chomp_sound = []
        try:
            s1 = Resources.load_sound("chomp.mp3")
            s2 = Resources.load_sound("chomp2.mp3")
            if s1:
                self.chomp_sound.append(s1)
            if s2:
                self.chomp_sound.append(s2)
        except Exception as e:
            print(f"啃咬音频加载失败 {e}")

        # 呻吟音效
        self.groan_sounds = []
        try:
            for i in range(1, 7):
                filename = f"groan{i}.mp3" if i > 1 else "groan.mp3"
                s = Resources.load_sound(filename)
                if s:
                    self.groan_sounds.append(s)
        except Exception as e:
            print(f"无法加载呻吟音效: {e}")
        self.last_groan_time = 0
        self.groan_interval = 8000

        # 击打音效
        self.splat_sounds = []
        try:
            for i in range(1, 4):
                filename = f"splat{i}.mp3" if i > 1 else "splat.mp3"
                s = Resources.load_sound(filename)
                if s:
                    self.splat_sounds.append(s)
        except Exception as e:
            print(f"无法加载 击打 音效: {e}")

        # self.dave_seen_file = DAVE_SEEN_FILE
        # self.dave_seen = os.path.exists(self.dave_seen_file)
        self.dave = DaveSequence(
            frame_dir="crazydave",
            sound_files=[
                "crazydaveextralong1.mp3",
                "crazydaveextralong2.mp3",
                "crazydaveextralong3.mp3",
                "crazydavecrazy.mp3",
            ]
        )



        self.plant_sound = None
        try:
            self.plant_sound = Resources.load_sound("plant.mp3")
        except Exception as e:
            print(f"无法加载种植音效: {e}")

        # 植物冷却记录
        self.last_plant_time = {
            'peashooter': 0,
            'sunflower': 0,
            "wallnut":0,
            "cherrybomb":0
        }
        self.card_plants = [
            {'name': 'peashooter', 'class': Peashooter},
            {'name': 'sunflower', 'class': Sunflower},
            {'name':'cherrybomb','class':CherryBomb},
            {'name': 'wallnut', 'class': Wallnut}
        ]
        # 在 __init__ 中，卡片图标加载之后添加
        try:
            # 加载植物第一帧作为预览阴影（缩放到与植物实际大小一致）
            plant_size = (CELL_WIDTH, CELL_HEIGHT)  # 假设植物与格子同大，或者使用实际植物大小
            self.peashooter_preview = Resources.load_image("peashooter/Peashooter_00.png", size=plant_size)
            self.sunflower_preview = Resources.load_image("sunflower/Sunflower_00.png", size=plant_size)
            self.cherrybomb_preview=Resources.load_image("cherrybomb/cherrybomb_000.png",size=(CELL_WIDTH*1.1, CELL_HEIGHT*1.1) )
            self.wallnut_preview = Resources.load_image("wall_nut/WallNut_00.png", size=plant_size)
            # 设置透明度（使用 convert_alpha 后设置 alpha 值）
            self.peashooter_preview.set_alpha(180)#这个范围是0~255，0表示完全透明，255为图片本身
            self.sunflower_preview.set_alpha(180)
            self.cherrybomb_preview.set_alpha(180)
            self.wallnut_preview.set_alpha(180)
        except Exception as e:
            print(f"无法加载植物预览图像: {e}")
            # 备用：创建彩色半透明方块
            self.peashooter_preview = pygame.Surface((CELL_WIDTH, CELL_HEIGHT), pygame.SRCALPHA)
            self.peashooter_preview.fill((0, 255, 0, 180))
            self.sunflower_preview = pygame.Surface((CELL_WIDTH, CELL_HEIGHT), pygame.SRCALPHA)
            self.sunflower_preview.fill((255, 255, 0, 180))
            self.cherryomb_preview = pygame.Surface((CELL_WIDTH, CELL_HEIGHT), pygame.SRCALPHA)
            self.cherrybomb_preview.fill((255, 0, 0, 180))
            self.wallnut_preview = pygame.Surface((CELL_WIDTH, CELL_HEIGHT), pygame.SRCALPHA)
            self.wallnut_preview.fill((255, 255, 255, 180))


        # 阳光不足提示音
        self.not_enough_sound = None
        try:
            self.not_enough_sound = Resources.load_sound("not_enough.mp3")
        except Exception as e:
            print(f"无法加载 not_enough 音效: {e}")

        #开场动画
        # 加载 Ready Set Plant 图片（缩放0.5倍，居中显示）
        # 加载 Ready Set Plant 图片，不同缩放比例
        try:
            raw_ready = Resources.load_image("screen/StartReady.png")
            raw_set = Resources.load_image("screen/StartSet.png")
            raw_plant = Resources.load_image("screen/StartPlant.png")

            READY_SCALE = 1.2
            SET_SCALE = 1.0
            PLANT_SCALE = 1.4

            self.ready_img = pygame.transform.scale(raw_ready,
                                                    (int(raw_ready.get_width() * READY_SCALE),
                                                     int(raw_ready.get_height() * READY_SCALE)))
            self.set_img = pygame.transform.scale(raw_set,
                                                  (int(raw_set.get_width() * SET_SCALE),
                                                   int(raw_set.get_height() * SET_SCALE)))
            self.plant_img = pygame.transform.scale(raw_plant,
                                                    (int(raw_plant.get_width() * PLANT_SCALE),
                                                     int(raw_plant.get_height() * PLANT_SCALE)))
            #包裹图片的矩形中心为SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            self.ready_rect = self.ready_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.set_rect = self.set_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.plant_rect = self.plant_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        except Exception as e:
            print(f"无法加载 Ready、Set、Plant 图片: {e}")
            # 备用纯色图片
            self.ready_img = pygame.Surface((int(SCREEN_WIDTH * 0.5), int(SCREEN_HEIGHT * 0.5)))
            self.ready_img.fill((255, 0, 0))
            self.set_img = pygame.Surface((int(SCREEN_WIDTH * 0.4), int(SCREEN_HEIGHT * 0.4)))
            self.set_img.fill((0, 255, 0))
            self.plant_img = pygame.Surface((int(SCREEN_WIDTH * 0.6), int(SCREEN_HEIGHT * 0.6)))
            self.plant_img.fill((0, 0, 255))
            self.ready_rect = self.ready_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.set_rect = self.set_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.plant_rect = self.plant_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.ready_set_plant_sound = None
        try:
            self.ready_set_plant_sound = Resources.load_sound("readysetplant.mp3")
        except Exception as e:
            print(f"无法加载 readysetplant.mp3: {e}")

        #初始化小推车


        for row in range(LAWN_ROWS):
            mower = Mower(row)
            self.mowers.add(mower)
        # 加载小推车出场音效
        self.move_car_sound = None
        try:
            self.move_car_sound = Resources.load_sound("move_the_car.mp3")
        except Exception as e:
            print(f"无法加载 move_the_car.mp3: {e}")
        self.move_car_start = 0
        self.move_car_duration = 0
        #小推车保护机制
        # 记录每行小推车上次触发时间（毫秒），初始为 -30000 表示可以立即生成僵尸
        # self.row_last_mower_trigger = [-MOWER_COOLDOWN] * LAWN_ROWS

        # 铲子相关
        self.shovel_mode = False
        self.shovel_img = None
        self.shovel_bank_img = None
        try:
            self.shovel_img = Resources.load_image(SHOVEL_ICON, size=(CARD_WIDTH, CARD_HEIGHT))
            self.shovel_bank_img = Resources.load_image(SHOVEL_BANK_IMAGE, size=(CARD_WIDTH, CARD_HEIGHT))
        except Exception as e:
            print(f"无法加载铲子图片: {e}")
            # 备用：创建灰色方块
            self.shovel_img = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            self.shovel_img.fill((128, 128, 128))
            self.shovel_bank_img = pygame.Surface(SHOVEL_BANK_SIZE)#其实就是size=(CARD_WIDTH, CARD_HEIGHT)
            self.shovel_bank_img.fill((200, 200, 200))
        self.shovel_rect = pygame.Rect(SHOVEL_BANK_POS[0], SHOVEL_BANK_POS[1], SHOVEL_BANK_SIZE[0], SHOVEL_BANK_SIZE[1])
        self.shovel_sound = None
        try:
            self.shovel_sound = Resources.load_sound("shovel.mp3")
        except Exception as e:
            print(f"无法加载铲子音效: {e}")

        # 旗帜进度条
        self.flag_progress = 0.0
        self.flag_empty = None
        self.flag_full = None
        self.flag_rect = None
        self.battle_start_time = 0
        try:
            raw_flagmeter = Resources.load_image("screen/FlagMeter.png")
            meter_width, meter_height = raw_flagmeter.get_size()
            # 切割上下两部分
            #surface.subsurface((x, y, width, height))
            # x,y：裁剪区域的左上角坐标（相对于原图）；
            # width,height：裁剪区域的宽和高。
            self.flag_empty = raw_flagmeter.subsurface((0, 0, meter_width, meter_height//2))
            self.flag_full = raw_flagmeter.subsurface((0, meter_height//2, meter_width, meter_height//2))
            # 缩放到目标大小
            self.flag_empty = pygame.transform.scale(self.flag_empty, FLAGMETER_SIZE)
            self.flag_full = pygame.transform.scale(self.flag_full, FLAGMETER_SIZE)
        except Exception as e:
            print(f"无法加载 FlagMeter.png: {e}")
            # 备用：创建纯色
            self.flag_empty = pygame.Surface(FLAGMETER_SIZE)
            self.flag_empty.fill((100, 100, 100))
            self.flag_full = pygame.Surface(FLAGMETER_SIZE)
            self.flag_full.fill((0, 255, 0))
        self.flag_rect = pygame.Rect(FLAGMETER_POS[0], FLAGMETER_POS[1], FLAGMETER_SIZE[0], FLAGMETER_SIZE[1])

        # 胜利音乐
        self.win_sound = None
        try:
            self.win_sound = Resources.load_sound("winmusic.mp3")
        except Exception as e:
            print(f"无法加载 winmusic.mp3: {e}")
        self.win_played = False
        self.win_displayed = False
        self.win_delay_start = 0
        # 奖杯相关
        self.trophy_img = None
        try:
            raw_trophy = Resources.load_image("screen/trophy.png")
            trophy_size = (150, 150)
            self.trophy_img = pygame.transform.scale(raw_trophy, trophy_size)
        except Exception as e:
            print(f"无法加载 trophy.png: {e}")
            # 备用：创建金色圆形
            self.trophy_img = pygame.Surface((150, 150), pygame.SRCALPHA)
            pygame.draw.circle(self.trophy_img, (255, 215, 0), (75, 75), 70)
            pygame.draw.circle(self.trophy_img, (255, 255, 255), (75, 75), 60, 5)

        # # 光芒相关
        self.shine_angle = 0.0
        self.shine_alpha = 0
        self.shine_max_alpha = 255
        self.shine_fade_speed = 1.5      # 每帧透明度增量
        self.shine_rotation_speed = 0.3  # 每帧角度增量
        self.shine_img = None
        self.light_mask = None  # 8扇形光影遮罩

        #外挂接口
        self.cheat_config = self.load_cheat_config()
        self.last_cheat_check = 0
        self.cheat_check_interval = 1000  # 每1秒检查一次配置文件更新


        self.play_bgm(0)
        self.bgm_phase = 'intro'



        self.more_zombies_sound = None
        try:
            self.more_zombies_sound = Resources.load_sound("more_zombies.mp3")
        except Exception as e:
            print(f"无法加载 more_zombies.mp3: {e}")

        self.ui_on_top = False  # 控制UI绘制顺序：False=UI在下，True=UI在上
        #为了实现真正的暂停（包括植物冷却、向日葵产阳光、自然阳光掉落等）引入游戏时间
        self.paused = False
        self.game_time = 0
        # 加载暂停图片（支持拖动）
        try:
            # raw_suspend = Resources.load_image("screen/suspend.jpg")
            # 缩放到屏幕宽度的60%（保持比例）
            # max_width = int(SCREEN_WIDTH * 0.6)
            # scale = max_width / raw_suspend.get_width()
            # new_size = (max_width, int(raw_suspend.get_height() * scale))
            self.suspend_image = Resources.load_image("screen/suspend.jpg")
        except Exception as e:
            print(f"无法加载暂停图片: {e}")
            # 备用：创建半透明灰色方块
            self.suspend_image = pygame.Surface((400, 300), pygame.SRCALPHA)
            self.suspend_image.fill((128, 128, 128, 200))
        self.suspend_rect = self.suspend_image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.suspend_dragging = False
        self.drag_offset = (0, 0)
        self.preview_follow_img = None  # 跟随鼠标的植物预览图像

        try:
            # 加载植物第一帧（用于鼠标跟随），不预先设置透明度
            self.peashooter_follow = Resources.load_image("peashooter/Peashooter_00.png", size=(CELL_WIDTH, CELL_HEIGHT))
            self.sunflower_follow = Resources.load_image("sunflower/Sunflower_00.png", size=(CELL_WIDTH, CELL_HEIGHT))
            self.cherrybomb_follow = Resources.load_image("cherrybomb/cherrybomb_000.png", size=(CELL_WIDTH*1.1, CELL_HEIGHT*1.1))
            self.wallnut_follow = Resources.load_image("wall_nut/WallNut_00.png", size=(CELL_WIDTH, CELL_HEIGHT))
        except Exception as e:
            print(f"无法加载植物跟随图像: {e}")
            # 备用：使用预览图（已设置透明度）
            self.peashooter_follow = self.peashooter_preview
            self.sunflower_follow = self.sunflower_preview
            self.cherrybomb_follow = self.cherrybomb_preview
            self.wallnut_follow = self.wallnut_preview

    def load_user_data(self):
        """加载用户进度（已通关关卡数）"""
        self.user_data_file = os.path.join(get_base_path(), "user_data.json")
        try:
            with open(self.user_data_file, 'r') as f:
                data = json.load(f)
                self.unlocked_level = data.get("unlocked_level", 0)
        except FileNotFoundError:
            self.unlocked_level = 0  # 未通关任何关卡
        except Exception as e:
            print(f"加载用户数据失败: {e}")
            self.unlocked_level = 0

    def save_user_data(self):
        """保存用户进度"""
        try:
            with open(self.user_data_file, 'w') as f:
                json.dump({"unlocked_level": self.unlocked_level}, f)
        except Exception as e:
            print(f"保存用户数据失败: {e}")

    def go_to_title(self):
        """返回标题界面，不清除存档"""
        self.all_sprites.empty()
        self.plants.empty()
        self.zombies.empty()
        self.bullets.empty()
        self.sun_sprites.empty()
        self.lawn = LawnGrid()
        self.mowers.empty()
        self.opening_zombies.empty()
        self.opening_zombies_created = False
        self.viewport_x = VIEWPORT_RIGHT_OFFSET
        self.gameover_scale = 0.3
        self.gameover_anim_finished = False
        self.leftmost_zombie = None
        self.lose_played = False
        self.gameover_delay_start = None
        self.gameover_visible = False
        self.gameover_image = None
        self.last_groan_time = 0
        self.dave.reset()
        self.sun_amount = 100
        self.last_sun_drop = 0
        self.last_plant_time = {
            'peashooter': 0,
            'sunflower': 0,
            'cherrybomb': 0,
            "wallnut": 0,
        }
        self.selected_card = None
        self.preview_follow_img = None
        self.ready_set_plant_start = 0
        self.ready_set_plant_index = 0
        self.ready_set_plant_last_switch = 0
        self.mowers.empty()
        for row in range(LAWN_ROWS):
            mower = Mower(row)
            self.mowers.add(mower)
        self.start_mower_enter()
        self.move_car_start = 0
        self.move_car_duration = 0
        self.shovel_mode = False
        self.flag_progress = 0.0
        self.battle_start_time = 0
        self.win_played = False
        self.win_displayed = False
        self.win_delay_start = 0
        if self.win_sound:
            self.win_sound.stop()
        self.win_start = 0
        self.light_mask = None
        self.shine_angle = 0.0
        self.shine_alpha = 0
        self.game_time = 0

        # 清空波次管理器（开始关卡时重新创建）
        self.wave_manager = None
        self.current_level = None

        self.stop_bgm()
        self.play_bgm(0)
        self.bgm_phase = 'intro'
        self.state = 'intro'

    def start_level(self, level_index, now):
        """开始指定关卡（索引从0开始），需要传入当前真实时间 now"""
        if level_index < 0 or level_index >= len(LEVELS):
            print(f"无效关卡索引: {level_index}")
            return

        # 先调用 go_to_title 重置所有状态（但会清空存档？不，go_to_title 不清除存档）
        # 为了复用重置代码，可以直接复制 go_to_title 中重置状态的代码，或者让 go_to_title 接受一个 keep_archive 参数。
        # 这里为了清晰，我们直接写一个独立的重置（与 go_to_title 类似，但保留存档并创建 wave_manager）
        self.all_sprites.empty()
        self.plants.empty()
        self.zombies.empty()
        self.bullets.empty()
        self.sun_sprites.empty()
        self.lawn = LawnGrid()
        self.mowers.empty()
        self.opening_zombies.empty()
        self.opening_zombies_created = False
        self.viewport_x = VIEWPORT_RIGHT_OFFSET
        self.gameover_scale = 0.3
        self.gameover_anim_finished = False
        self.leftmost_zombie = None
        self.lose_played = False
        self.gameover_delay_start = None
        self.gameover_visible = False
        self.gameover_image = None
        self.last_groan_time = 0
        self.dave.reset()
        self.sun_amount = 100
        self.last_sun_drop = 0
        self.last_plant_time = {
            'peashooter': 0,
            'sunflower': 0,
            'cherrybomb': 0,
            "wallnut": 0,
        }
        self.selected_card = None
        self.preview_follow_img = None
        self.ready_set_plant_start = 0
        self.ready_set_plant_index = 0
        self.ready_set_plant_last_switch = 0
        self.mowers.empty()
        for row in range(LAWN_ROWS):
            mower = Mower(row)
            self.mowers.add(mower)
        self.start_mower_enter()
        self.move_car_start = 0
        self.move_car_duration = 0
        self.shovel_mode = False
        self.flag_progress = 0.0
        self.battle_start_time = 0
        self.win_played = False
        self.win_displayed = False
        self.win_delay_start = 0
        if self.win_sound:
            self.win_sound.stop()
        self.win_start = 0
        self.light_mask = None
        self.shine_angle = 0.0
        self.shine_alpha = 0
        self.game_time = 0

        # 根据关卡配置创建 WaveManager
        level_cfg = LEVELS[level_index]
        self.wave_manager = WaveManager(
            waves=level_cfg['waves'],
            first_spawn_interval=level_cfg['first_spawn_interval'],
            last_spawn_interval=level_cfg['last_spawn_interval'],
            first_spawn_time=level_cfg['first_spawn_time'],
            rows=LAWN_ROWS,
            emergency_multiplier=level_cfg['emergency_multiplier'],
            flag_followers_min=level_cfg['flag_followers_min'],
            flag_followers_max=level_cfg['flag_followers_max']
        )
        self.wave_manager.reset(now)

        self.current_level = level_index
        # self.stop_bgm()
        # self.play_bgm(0)
        self.bgm_phase = 'intro'
        self.state = 'transition_to_battle'


    def play_bgm(self, index):
        """播放指定索引的背景音乐（循环），若已播放相同音乐则跳过"""
        if self.current_bgm_index == index:
            return
        try:
            pygame.mixer.music.load(os.path.join("music", self.BGM_FILES[index]))
            pygame.mixer.music.play(loops=-1)#循环播放
            self.current_bgm_index = index
        except Exception as e:
            print(f"无法播放背景音乐 {self.BGM_FILES[index]}: {e}")

    def stop_bgm(self):
        """停止所有背景音乐"""
        pygame.mixer.music.stop()
        self.current_bgm_index = None
        self.bgm_phase = None
        self.bgm_part2_choice = None


    def load_cheat_config(self):
        """加载作弊配置文件 cheat.json"""
        config_path = os.path.join(get_base_path(), "cheat.json")
        default_config = {
            "sun_infinite": False,
            "sun_never_decrease": False,
            "sun_unlimited": False,#取消阳光上限
            "overlap_plant": False,
            "restore_mowers": False,
            "auto_collect_sun": False,
            "no_cooldown": False,  # 新增：取消植物冷却
            "pause_spawn": False,  # 新增：暂停出怪
            "kill_all_zombies": False,  # 新增：清除草坪内僵尸（触发型）
            "set_sun_amount": False,  # 新增：是否触发设置阳光
            "custom_sun": 100  # 新增：自定义阳光数值（默认值）
        }
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 确保所有键都存在
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        except FileNotFoundError:
            return default_config #玩家第一次打开游戏，没有作弊，直接返回上面那个全是false的
        except Exception as e:
            print(f"加载作弊配置失败: {e}")
            return default_config

    #目前专门用于处理小推车启动问题的
    def save_cheat_config(self, config):
        """保存作弊配置到文件"""
        config_path = os.path.join(get_base_path(), "cheat.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"保存作弊配置失败: {e}")

    def restore_all_mowers(self):
        #先删除所有的小推车，然后复原所有

        self.mowers.empty()
        # 重新为每行创建小推车，并直接放置在正确位置
        for row in range(LAWN_ROWS):
            mower = Mower(row)
            mower.world_x = LAWNMOWER_START_X  # 直接定位到目标位置
            mower.state = 'idle'#idle空闲的，无所事事的
            self.mowers.add(mower)
        # 重置触发记录
        self.row_last_mower_trigger = [-MOWER_COOLDOWN] * LAWN_ROWS
        #当前时间 - 最后一次触发时间 > 冷却时间 → 可以触发
        #专门为了配合作弊文件的，作弊文件中回复小推车别引发意外

    #专门处理作弊文件中杀死僵尸的
    def kill_zombies_in_lawn(self):
        """杀死所有位于草坪世界坐标范围内的僵尸"""
        for zombie in list(self.zombies):
            if zombie.state == Zombie.STATE_DIE:
                continue
            # 检查是否在草坪世界坐标范围内
            if  zombie.world_x <= LAWN_BOTTOM_RIGHT_X :
                zombie.kill()
                self.wave_manager.zombie_killed()
            #杀死僵尸之后通知波次管理逻辑

    def on_zombie_death(self, zombie):
        """僵尸死亡回调（动画开始时调用）"""
        self.wave_manager.zombie_killed()

    def create_opening_zombies(self):
        """创建开场僵尸，根据下一关的僵尸类型生成代表，每行一个，x坐标随机"""
        self.opening_zombies.empty()

        # 确定要展示哪一关的僵尸类型
        if self.unlocked_level < len(LEVELS):
            target_level = self.unlocked_level  # 下一关
        else:
            target_level = len(LEVELS) - 1  # 已通关所有关，展示最后一关

        waves = LEVELS[target_level]['waves']  # 获取该关的波次配置

        # 从波次配置中提取所有出现的僵尸类型（排除 'flag'）
        zombie_types = set()
        for type_dict, _ in waves:
            for ztype in type_dict.keys():
                if ztype != 'flag':
                    zombie_types.add(ztype)
        if not zombie_types:
            zombie_types = {'normal'}  # 保底

        zombie_types = list(zombie_types)

        # 以下代码保持不变：分配每种类型的数量、生成每行的僵尸
        rows = LAWN_ROWS
        num_zombies = rows

        if len(zombie_types) == 1:
            counts = {zombie_types[0]: num_zombies}
        else:
            base = num_zombies // len(zombie_types)
            remainder = num_zombies % len(zombie_types)
            shuffled = zombie_types[:]
            random.shuffle(shuffled)
            counts = {}
            for i, ztype in enumerate(shuffled):
                counts[ztype] = base + (1 if i < remainder else 0)

        type_pool = []
        for ztype, cnt in counts.items():
            type_pool.extend([ztype] * cnt)
        random.shuffle(type_pool)

        # 定义每行的坐标范围（原开场僵尸坐标）
        left_coords = [983, 993, 998, 993, 1001]
        right_coords = [1400, 1400, 1400, 1400, 1400]
        scale = 1.7

        temp = OpeningZombie(0, 0, 0, scale=scale, zombie_type='normal')
        zombie_width = temp.rect.width

        for row in range(rows):
            ztype = type_pool[row]
            left = left_coords[row]
            right = right_coords[row]
            max_x = right - zombie_width
            if max_x < left:
                max_x = left
            x = random.randint(left, max_x)
            y = row * CELL_HEIGHT
            zombie = OpeningZombie(x, y, row, scale=scale, zombie_type=ztype)
            self.opening_zombies.add(zombie)

    def create_light_mask(self):#该函数的目的就是改变light_mask的值
        """创建8个扇形的光影遮罩（强弱交替）"""
        # 计算对角线长度并设计2冗余
        diag = int(math.hypot(SCREEN_WIDTH, SCREEN_HEIGHT)) + 2
        mask_surf = pygame.Surface((diag, diag), pygame.SRCALPHA)
        center = (diag // 2, diag // 2)
        radius = diag // 2

        # 绘制8个扇形（0°～360°，每个45°）
        for i in range(8):
            start_angle = i * 45
            end_angle = start_angle + 45
            # 扇形由中心点、起始角度边缘点、终止角度边缘点构成
            points = [center]
            for angle in (start_angle, end_angle):
                rad = math.radians(angle)#弧度转化为角度
                x = center[0] + radius * math.cos(rad)
                y = center[1] - radius * math.sin(rad)  # pygame y轴向下
                points.append((x, y))
            # 偶数索引为强光，奇数索引为弱光
            alpha = 200 if i % 2 == 0 else 80
            pygame.draw.polygon(mask_surf, (255, 255, 255, alpha), points)
        self.light_mask = mask_surf


    def run(self):
        #handle_event 处理玩家输入，鼠标点击等操作
        #update 更新游戏状态，用于自动更新FPS
        #draw 绘制游戏画面
        #reset_game将游戏从 “运行中 / 结束态” 恢复到 “初始态”，让玩家无需重启程序即可重新开始一局游戏。
        while self.running:
            #强制一秒钟执行60次，并且返回上一帧用的时间（毫秒），1000/60 ≈ 16.67 毫秒
            dt = self.clock.tick(FPS) / 1000.0
            real_now = pygame.time.get_ticks()#游戏从开始到现在的真实时间，不受作弊，暂停的影响，用于音频播放
            if not self.paused:
                self.game_time += dt * 1000 #游戏内的逻辑时间，控制其他的update
            for event in pygame.event.get():
                self.handle_event(event, real_now)
            if not self.paused:
                self.update(self.game_time ,dt)   # 传递 dt
            self.draw()
            # 游戏退出时删除作弊配置文件
        cheat_path = os.path.join(get_base_path(), "cheat.json")
        try:
            if os.path.exists(cheat_path):
                os.remove(cheat_path)
                # print("作弊配置文件已删除")
        except Exception as e:
            print(f"删除作弊配置文件失败: {e}")


        pygame.quit()

    def handle_event(self, event, now):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_1:
                # 按1切换铲子模式
                self.shovel_mode = not self.shovel_mode
                if self.shovel_mode:
                    self.selected_card = None  # 进入铲子模式时取消卡片选中
                    if self.shovel_sound:
                        self.shovel_sound.play()
                # 可以播放音效（可选）
            elif event.key == pygame.K_2:
                # 按2切换僵尸血量显示
                self.show_health_bars = not self.show_health_bars
            elif event.key == pygame.K_3:
                # 按3切换图层顺序
                self.ui_on_top = not self.ui_on_top
                print(f"图层顺序切换: {'UI在上' if self.ui_on_top else '精灵在上'}")
            elif event.key == pygame.K_SPACE and self.state == 'battle':
                self.paused = not self.paused
                # 暂停时不停止音乐，仅停止游戏逻辑更新
            #整个过程：  elif event.type == pygame.KEYDOWN:
            #               elif event.key == pygame.K_SPACE and self.state == 'battle':
            #首先这个判断游戏进入暂停状态，具体来说这个时候update就停止更新了
            #然后进入    elif event.type == pygame.MOUSEBUTTONDOWN :
            #               if event.button == 1 and self.paused and self.state == 'battle':
            #                   mx, my = pygame.mouse.get_pos()
            #                   if self.suspend_rect.collidepoint(mx, my):
            #                       self.suspend_dragging = True
            #                       self.drag_offset = (mx - self.suspend_rect.x, my - self.suspend_rect.y)
            #                       return  # 优先处理拖动，不继续执行后续点击逻辑
            #如果在暂停状态下点击鼠标左键，记录点击位置，进入暂停图画"screen\suspend.jpg"拖拽状态
            #最后进入    elif event.type == pygame.MOUSEMOTION:#处理鼠标移动事件
            #               if self.suspend_dragging:
            #                   mx, my = pygame.mouse.get_pos()
            #                   self.suspend_rect.x = mx - self.drag_offset[0]
            #                   self.suspend_rect.y = my - self.drag_offset[1]
            #     # 限制在屏幕内
            #                   self.suspend_rect.clamp_ip(self.screen.get_rect())
            #最后调用draw 实现跟随鼠标走的效果

        elif event.type == pygame.MOUSEMOTION:#处理鼠标移动事件
            if self.suspend_dragging:
                mx, my = pygame.mouse.get_pos()
                self.suspend_rect.x = mx - self.drag_offset[0]
                self.suspend_rect.y = my - self.drag_offset[1]
                # 限制在屏幕内
                self.suspend_rect.clamp_ip(self.screen.get_rect())
        elif event.type == pygame.MOUSEBUTTONUP:       #检测鼠标按键松开
            if event.button == 1 and self.suspend_dragging:  #松开的是鼠标左键 button==3 是右键
                self.suspend_dragging = False

        elif event.type == pygame.MOUSEBUTTONDOWN :
            if event.button == 1 and self.paused and self.state == 'battle':
                mx, my = pygame.mouse.get_pos()
                if self.suspend_rect.collidepoint(mx, my):
                    self.suspend_dragging = True
                    # 计算鼠标相对于图片左上角的偏移
                    self.drag_offset = (mx - self.suspend_rect.x, my - self.suspend_rect.y)
                    return  # 优先处理拖动，不继续执行后续点击逻辑


            if event.button == 3 :
                #点击右键取消选中
                mx, my = pygame.mouse.get_pos()
                world_x = mx + self.viewport_x
                world_y = my
                col = int((world_x - LAWN_TOP_LEFT_X) / CELL_WIDTH)
                row = int((world_y - LAWN_TOP_LEFT_Y) / CELL_HEIGHT)
                if 0 <= row < LAWN_ROWS and 0 <= col < LAWN_COLS:
                    # 取消卡片选中，不影响铲子模式
                    self.selected_card = None
                    self.preview_follow_img = None
                if self.shovel_mode:
                    self.shovel_mode = False
                return

            if event.button == 1:
                # 这些代码看似没有用游戏后续逻辑（种植 / 铲植物 / 碰撞检测）需要用到world_x/world_y，
                # 但删掉了坐标转换的代码，导致后续逻辑读取不到这些变量
                # 触发了NameError（变量未定义）或AttributeError（属性不存在），最终闪退。
                mx, my = pygame.mouse.get_pos()
                world_x = mx + self.viewport_x
                world_y = my

                if self.state == 'intro':
                    if self.new_game_rect.collidepoint(mx, my):
                        self.start_level(0, now)
                        # 检测继续按钮（仅当有下一关时）
                    elif self.continue_rect.collidepoint(mx, my):
                        if self.unlocked_level < len(LEVELS):
                            self.start_level(self.unlocked_level, now)
                        else:
                            # 已通关所有关卡，进入最后一关
                            self.start_level(len(LEVELS) - 1, now)

                elif self.state == 'dave_dialogue':
                    self.dave.handle_click()

                elif self.state == 'ready_set_plant':
                    return

                elif self.state in ('battle',"win_delay"):
                    mx, my = pygame.mouse.get_pos()
                    world_x = mx + self.viewport_x
                    world_y = my
                    # ----- 0、阳光点击检测（优先，仅当非铲子模式且无选中卡片）-----
                    if not self.shovel_mode and self.selected_card is None:
                        clicked_sun = None
                        for sun in self.sun_sprites:
                            if sun.rect.collidepoint((mx, my)) and sun.state in ('falling', 'landed'):
                                clicked_sun = sun
                                break
                        if clicked_sun:
                            clicked_sun.start_collect(self.game_time, self.viewport_x)
                            return
                    # ----- 1. 卡片点击处理（豌豆、向日葵）-----
                    card_clicked = None
                    for i, rect in enumerate(self.card_rects):
                        if rect.collidepoint((mx, my)):
                            card_clicked = i
                            break

                    if card_clicked is not None:
                        plant_info = self.card_plants[card_clicked]
                        plant_name = plant_info['name']
                        price = PLANT_PRICES[plant_name]
                        last = self.last_plant_time[plant_name]
                        cooldown = PLANT_COOLDOWNS[plant_name]
                        # 阳光数量检查（受作弊影响）
                        if self.cheat_config.get("sun_infinite") :
                            enough = True
                        else:
                            enough = (self.sun_amount >= price)

                        if self.cheat_config.get("no_cooldown"):
                            cooled = True
                        else:
                            cooled = (last == 0 or self.game_time - last >= cooldown)

                        if not enough or not cooled:
                            if self.not_enough_sound:
                                self.not_enough_sound.play()
                            return
                        # 选中/取消选中
                        if self.selected_card == card_clicked:
                            self.selected_card = None
                            self.preview_follow_img = None
                        else:
                            self.selected_card = card_clicked
                            if card_clicked == 0:
                                self.preview_follow_img = self.peashooter_follow
                            elif card_clicked == 1:
                                self.preview_follow_img = self.sunflower_follow
                            elif card_clicked == 2:
                                self.preview_follow_img = self.cherrybomb_follow
                            elif card_clicked == 3:
                                self.preview_follow_img = self.wallnut_follow
                        self.shovel_mode = False#不管之前是什么样，立即变为取消铲子模式
                        return
                    # ----- 2. 铲子点击处理 -----
                    if self.shovel_rect.collidepoint((mx, my)):
                        if self.shovel_mode:
                            self.shovel_mode = False
                        else:
                            self.shovel_mode = True
                            self.selected_card = None
                            if self.shovel_sound:
                                self.shovel_sound.play()
                        return
                    # ----- 3. 草坪区域处理（铲除或种植）-----
                    if (LAWN_TOP_LEFT_X <= world_x <= LAWN_BOTTOM_RIGHT_X and
                            LAWN_TOP_LEFT_Y <= world_y <= LAWN_BOTTOM_RIGHT_Y):
                        col = int((world_x - LAWN_TOP_LEFT_X) / CELL_WIDTH)
                        row = int((world_y - LAWN_TOP_LEFT_Y) / CELL_HEIGHT)
                        if 0 <= row < LAWN_ROWS and 0 <= col < LAWN_COLS:
                            # 铲子模式：移除该格子最后种植的植物（列表末尾）
                            if self.shovel_mode:
                                plants = self.lawn.get_plants_at(row, col)
                                if plants:
                                    # 考虑到作弊可以重叠种植，移除最后一个（最新种植的）
                                    last_plant = plants[-1]
                                    last_plant.kill()
                                    self.lawn.remove_plant(last_plant)
                                    if self.shovel_sound:
                                        self.shovel_sound.play()
                                self.shovel_mode = False
                                return
                            # 种植事件（非铲子模式）
                            if self.selected_card is not None:
                                plant_info = self.card_plants[self.selected_card]
                                plant_name = plant_info['name']
                                plant_class = plant_info['class']
                                if plant_name == 'sunflower':
                                    self.wave_manager.add_sunflower_planted()

                                # 阳光和冷却检查（与原逻辑相同）
                                price = PLANT_PRICES[plant_name]
                                last = self.last_plant_time[plant_name]
                                cooldown = PLANT_COOLDOWNS[plant_name]

                                if self.cheat_config.get("sun_infinite"):
                                    enough = True
                                    pay = False
                                elif self.cheat_config.get("sun_never_decrease"):
                                    enough = (self.sun_amount >= price)
                                    pay = False
                                else:
                                    enough = (self.sun_amount >= price)
                                    pay = True

                                if self.cheat_config.get("no_cooldown"):
                                    cooled = True
                                else:
                                    cooled = (last == 0 or self.game_time - last >= cooldown)

                                if not enough or not cooled:
                                    if self.not_enough_sound:
                                        self.not_enough_sound.play()
                                    return

                                # 获取该格子已有的植物列表
                                plants_in_cell = self.lawn.get_plants_at(row, col)

                                # ========== 新逻辑：处理受损坚果替换 ==========
                                if not self.cheat_config.get("overlap_plant"):
                                    # 非重叠模式
                                    if plants_in_cell:
                                        # 格子有植物，检查是否为受损坚果
                                        if plant_name == 'wallnut':
                                            # 查找格子中的坚果（非重叠模式下最多一个）
                                            existing_nut = None
                                            for p in plants_in_cell:
                                                if isinstance(p, Wallnut):
                                                    existing_nut = p
                                                    break
                                            if existing_nut and existing_nut.current_state != 'normal':
                                                # 受损坚果：移除它，然后继续种植（格子变空）
                                                existing_nut.kill()  # 从精灵组移除
                                                self.lawn.remove_plant(existing_nut)  # 从草坪格子移除
                                                # 注意：此时 plants_in_cell 变为空列表，因为 remove_plant 已更新 grid
                                            else:
                                                # 没有受损坚果，种植失败
                                                if self.not_enough_sound:
                                                    self.not_enough_sound.play()
                                                return
                                        else:
                                            # 选中的不是坚果，格子被占，种植失败
                                            if self.not_enough_sound:
                                                self.not_enough_sound.play()
                                            return
                                    # 格子为空或已清空受损坚果，继续种植
                                # ==============================================

                                # 计算种植位置
                                plant_world_x = LAWN_TOP_LEFT_X + col * CELL_WIDTH
                                plant_world_y = LAWN_TOP_LEFT_Y + row * CELL_HEIGHT

                                # 根据 selected_card 创建植物实例（与原逻辑相同）
                                if self.selected_card == 0:
                                    plant_class = Peashooter
                                elif self.selected_card == 1:
                                    plant_class = Sunflower
                                elif self.selected_card == 2:
                                    plant_class = CherryBomb
                                elif self.selected_card == 3:
                                    plant_class = Wallnut

                                plant = plant_class(plant_world_x, plant_world_y, row, start_time=self.game_time)

                                # 将植物添加到草坪格子
                                if self.cheat_config.get("overlap_plant"):
                                    # 重叠模式：直接添加（不检查格子占用）
                                    self.lawn.add_plant_overlap(row, col, plant)
                                else:
                                    # 非重叠模式：此时格子应为空（已处理受损坚果情况），直接添加
                                    self.lawn.add_plant(row, col, plant)

                                # 添加到精灵组
                                self.plants.add(plant)
                                self.all_sprites.add(plant)

                                # 更新种植时间和阳光
                                self.last_plant_time[plant_name] = self.game_time
                                if pay:
                                    self.sun_amount -= price
                                if self.cheat_config.get("sun_infinite"):
                                    self.sun_amount = 9999

                                # 播放种植音效
                                if self.plant_sound:
                                    self.plant_sound.play()

                                # 取消选中卡片
                                self.selected_card = None
                                self.preview_follow_img = None
                                return

                    # ----- 4. 点击非草坪区域，取消选中卡片 -----
                    if self.selected_card is not None:
                        self.selected_card = None
                        self.preview_follow_img = None
                    return

                elif self.state == 'win':
                    self.go_to_title()

                elif self.state == 'gameover':
                    self.go_to_title()

    #将游戏从 “运行中 / 结束态” 恢复到 “初始态”，让玩家无需重启程序即可重新开始一局游戏。
    def reset_game(self):
        self.go_to_title()
        # self.all_sprites.empty()
        # self.plants.empty()
        # self.zombies.empty()
        # self.bullets.empty()
        # self.sun_sprites.empty()
        # self.lawn = LawnGrid()
        # self.mowers.empty()  # 清空小推车————统一清空然后重置
        # self.viewport_x = VIEWPORT_RIGHT_OFFSET
        # self.state = 'intro'
        # self.gameover_scale = 0.3
        # self.gameover_anim_finished = False
        # # self.last_zombie_spawn = 0
        # self.leftmost_zombie = None
        # self.lose_played = False
        # self.gameover_delay_start = None
        # self.gameover_visible = False
        # self.gameover_image = None
        # self.last_groan_time = 0
        # self.dave.reset()
        # self.opening_zombies.empty()
        # self.opening_zombies_created = False
        # # 重置阳光相关
        # self.sun_amount = 50
        # self.last_sun_drop = 0
        # # if not self.background_music_playing:
        # #     try:
        # #         pygame.mixer.music.load("music/game_running.mp3")
        # #         pygame.mixer.music.play(-1)
        # #         self.background_music_playing = True
        # #     except Exception as e:
        # #         print(f"无法加载背景音乐: {e}")
        #
        # self.last_plant_time = {
        #     'peashooter': 0,
        #     'sunflower': 0,
        #     'cherrybomb':0,
        #     "wallnut":0,
        # }
        # self.selected_card = None
        # self.preview_follow_img = None  # 新
        # self.ready_set_plant_start = 0
        # self.ready_set_plant_index = 0
        # self.ready_set_plant_last_switch = 0
        # # 生成小推车（每行一个）
        # self.mowers.empty()
        # for row in range(LAWN_ROWS):
        #     mower = Mower(row)
        #     self.mowers.add(mower)
        #     # 注意：不添加到 all_sprites，因为我们需要单独控制绘制顺序
        # self.start_mower_enter()  # 确保它们处于 entering 状态（新生成已是，但无害）
        # self.move_car_start = 0
        # self.move_car_duration = 0
        # # self.row_last_mower_trigger = [-MOWER_COOLDOWN] * LAWN_ROWS
        # self.shovel_mode = False
        # self.flag_progress = 0.0
        # self.battle_start_time = 0
        # self.win_played = False
        # self.win_displayed = False
        # self.win_delay_start = 0
        #
        # if self.win_sound:
        #     self.win_sound.stop()
        # self.win_start = 0
        # self.light_mask = None
        # self.shine_angle = 0.0
        # self.shine_alpha = 0
        # self.game_time = 0  # <-- 新增：重置游戏时间
        # self.all_sprites.empty()
        #
        # self.wave_manager.reset(self.game_time)
        # self.stop_bgm()
        # self.play_bgm(0)
        # self.bgm_phase = 'intro'


    def update_screen_positions(self):
        """更新所有精灵（植物、僵尸、子弹）的屏幕坐标（基于 self.viewport_x）"""
        for sprite in self.all_sprites:
            #hasattr()：检查对象是否有某个属性？有就返回 True，没有就返回 False
            #目标：给所有 “有世界坐标” 的精灵更新屏幕位置（植物、僵尸、子弹、小推车都属于这类）
            if hasattr(sprite, 'override_position') and sprite.override_position:
                continue
            if hasattr(sprite, 'world_x') and hasattr(sprite, 'world_y'):
                sprite.rect.x = sprite.world_x - self.viewport_x
                sprite.rect.y = sprite.world_y
            #isinstance()：检查对象是否是某个类（或子类）的实例？是就返回 True，不是就返回 False
            #只给僵尸更新碰撞矩形
            if isinstance(sprite, Zombie):
                sprite._update_collision_rect()
        # 阳光的屏幕坐标在 Sun.update 中已更新，此处不再处理

    #开启小推车入场动画
    def start_mower_enter(self,duration=3.0):
        for mower in self.mowers:
            mower.start_enter(duration)


    def update(self, now, dt):
        real_now = pygame.time.get_ticks()#为了适配音频播放
        # 如果处于 battle 且暂停，跳过所有游戏逻辑更新
        if self.state == 'battle' and self.paused:
            return


        #最先检查作弊文件是否更新
        if real_now - self.last_cheat_check > self.cheat_check_interval:
            self.last_cheat_check = real_now
            new_config = self.load_cheat_config()
            # 检测小推车恢复标志（仅当从 False 变为 True 时触发一次）
            if new_config.get("restore_mowers") and not self.cheat_config.get("restore_mowers"):
                self.restore_all_mowers()
                new_config["restore_mowers"] = False
            if new_config.get("kill_all_zombies") and not self.cheat_config.get("kill_all_zombies"):
                self.kill_zombies_in_lawn()
                new_config["kill_all_zombies"] = False

            # else:
            #     self.cheat_config = new_config

            # 处理自定义阳光设置（触发型）
            if new_config.get("set_sun_amount"):
                target = new_config.get("custom_sun", 100)
                if target > 50:
                    # 如果没有开启阳光上限，则限制不超过9999
                    if not self.cheat_config.get("sun_unlimited"):
                        target = min(target, 9999)
                    self.sun_amount = target
                    # print(f"[作弊] 阳光已设置为 {target}")
                # 清除标志，防止重复设置
                new_config["set_sun_amount"] = False
                # 可选：播放音效？暂无
            self.cheat_config = new_config
            self.save_cheat_config(new_config)

        # 先更新阳光（需要视口偏移）
        self.sun_sprites.update(now, dt, self.viewport_x)
#减少资源占用，不在为每一个阳光计算时间，而是统一一个时间收集所有阳光
        if self.cheat_config.get("auto_collect_sun"):
            for sun in list(self.sun_sprites):
                #不存在collect_finish状态，这个只是collecting的子状态
                if sun.state != 'collecting' and not getattr(sun, 'collect_finished',
                                                             False) and now >= sun.auto_collect_time:
                    sun.start_collect(now, self.viewport_x)
        # 检查收集完成的阳光（收集动画完成且未移除）
        for sun in list(self.sun_sprites):
            if hasattr(sun, 'collect_finished') and sun.collect_finished:
                self.sun_amount += sun.value
                if self.cheat_config.get("sun_infinite"):
                    self.sun_amount = 9999
                elif not self.cheat_config.get("sun_unlimited"):
                    if self.sun_amount > 9999:
                        self.sun_amount = 9999
                sun.kill()

        if self.state == 'intro':
            if not self.opening_zombies_created:
                self.create_opening_zombies()
                self.opening_zombies_created = True
            self.opening_zombies.update(now)


        elif self.state == 'transition_to_battle':
            if self.viewport_x > VIEWPORT_LEFT_OFFSET:
                self.viewport_x -= TRANSITION_SPEED * (1 / FPS)
                if self.viewport_x < VIEWPORT_LEFT_OFFSET:
                    self.viewport_x = VIEWPORT_LEFT_OFFSET
                    if self.current_level == 2:  # 第三关
                        self.state = 'dave_dialogue'
                    else:
                        self.state = 'ready_set_plant'
                        self.ready_set_plant_start = now
                        self.ready_set_plant_index = 0
                        self.ready_set_plant_last_switch = now
                        if self.ready_set_plant_sound:
                            self.ready_set_plant_sound.play()

            else:#视角移动逻辑的 “兜底保障”，避免卡死
                self.viewport_x = VIEWPORT_LEFT_OFFSET
                if self.current_level == 2:
                    self.state = 'dave_dialogue'
                else:
                    self.state = 'ready_set_plant'
                    self.ready_set_plant_start = now
                    self.ready_set_plant_index = 0
                    self.ready_set_plant_last_switch = now
                    if self.ready_set_plant_sound:
                        self.ready_set_plant_sound.play()

        elif self.state == 'dave_dialogue':
            self.dave.update(now)
            if self.dave.finished_moving:
                # try:
                #     with open(self.dave_seen_file, 'w') as f:
                #         f.write('1')
                #     self.dave_seen = True
                # except Exception as e:
                #     print(f"无法写入戴夫标志文件: {e}")
                # 戴夫结束 → 进入 Ready Set Plant
                self.state = 'ready_set_plant'
                self.ready_set_plant_start = now
                self.ready_set_plant_index = 0
                self.ready_set_plant_last_switch = now
                if self.ready_set_plant_sound:
                    self.ready_set_plant_sound.play()

        elif self.state == 'ready_set_plant':
            FIXED_DURATION = 2000 #三张图片总共存在时间
            # 三张图片各占 时间
            TIME_RATIOS = [0.3, 0.3, 0.4]
            total_display = FIXED_DURATION * sum(TIME_RATIOS)
            t1 = FIXED_DURATION * TIME_RATIOS[0]
            t2 = FIXED_DURATION * (TIME_RATIOS[0] + TIME_RATIOS[1])
            t3 = total_display
            elapsed = now - self.ready_set_plant_start

            # 图片切换逻辑（-1 表示不显示任何图片）
            if elapsed < t1:
                self.ready_set_plant_index = 0
            elif elapsed < t2:
                self.ready_set_plant_index = 1
            elif elapsed < t3:
                self.ready_set_plant_index = 2
            else:
                self.ready_set_plant_index = -1

            # 3秒后强制进入战斗，并停止音频
            if elapsed >= FIXED_DURATION:
                if self.ready_set_plant_sound:
                    self.ready_set_plant_sound.stop()  # 停止可能过长的音频
                #播放小推车入场动画
                if self.move_car_sound:
                    audio_length = self.move_car_sound.get_length()  # 秒
                    for mower in self.mowers:
                        mower.start_enter(audio_length)
                    self.move_car_sound.play()
                    self.move_car_start = now
                    self.move_car_duration = audio_length * 1000  # 毫秒
                else:
                    # 无音频时默认1秒
                    for mower in self.mowers:
                        mower.start_enter(1.0)
                self.battle_start_time = now   # 记录战斗开始时间
                self.state = 'battle'
                self.play_bgm(1)
                self.bgm_phase = 'battle_part1'
                self.last_zombie_spawn = now  # 重置僵尸生成计时
                self.wave_manager.reset(now)
                self.last_sun_drop = now

        elif self.state == 'battle':
            # 检查小推车入场音频是否结束
            if self.move_car_start > 0 and real_now - self.move_car_start >= self.move_car_duration:
                for mower in self.mowers:
                    if mower.state == 'entering':
                        mower.state = 'idle'
                        mower.world_x = LAWNMOWER_START_X  # 强制对齐
                self.move_car_start = 0





            # 更新旗帜进度（示例：基于时间，一轮60秒）
#现在更新旗帜进度——可以像原版一样改成一大波之后突然跳一节
            if self.battle_start_time > 0:
                elapsed = now - self.battle_start_time
                self.flag_progress = self.wave_manager.get_progress()
                # self.flag_progress = min(1.0, elapsed / 50000)  # 60秒 = 60000ms
                if self.wave_manager.is_all_spawned_and_dead(len(self.zombies)):
                    # if self.background_music_playing:
                    #     pygame.mixer.music.stop()
                    #     self.background_music_playing = False
                    # if self.win_sound and not self.win_played:
                    #     self.win_sound.play()
                    #     self.win_played = True
                    self.state = 'win_delay'
                    self.win_delay_start=now
                    # self.stop_bgm()
                    # self.win_start = now
                    # self.create_light_mask()

            else:
                self.flag_progress = 0.0


            #是否切换BGM
            # # 在 update 的 battle 分支中（大约在更新旗帜进度之后，僵尸生成之前）
            # if not self.bgm_switched and self.bgm2_sound and self.wave_manager.current_wave_index >= self.total_waves // 2:
            #     pygame.mixer.music.stop()  # 停止第一首背景音乐
            #     self.bgm2_sound.play(loops=-1)  # 循环播放第二首
            #     self.bgm_switched = True
            # 获取总波数的一半（向下取整）
            half_waves = len(self.wave_manager.waves) // 2

            # 如果当前处于前半段，但波次已经达到或超过一半，则切换到后半段
            if self.bgm_phase == 'battle_part1' and self.wave_manager.current_wave_index >= half_waves:
                # 随机选择 2 或 3
                choice = random.choice([2, 3])
                self.play_bgm(choice)
                self.bgm_phase = 'battle_part2'
                self.bgm_part2_choice = choice

            # 获取本帧需要生成的僵尸
            # 暂停出怪判断
            if not self.cheat_config.get("pause_spawn"):

                if self.wave_manager.next_wave_delay_until > now and self.wave_manager.next_wave_is_flag:
                    if self.more_zombies_sound:
                        self.more_zombies_sound.play()
                    self.wave_manager.next_wave_is_flag = False  # 避免重复播放
                alive_count = len(self.zombies)
                zombies_to_spawn = self.wave_manager.update(now,alive_count)
                for row, ztype in zombies_to_spawn:
                    x = int(BACKGROUND_WIDTH * 0.83)
                    y = LAWN_TOP_LEFT_Y + row * CELL_HEIGHT
                    scale = 1.7
                    # 在生成僵尸的代码处
                    if ztype == 'flag':
                        zombie = FlagZombie(x, y, row, scale=scale, chomp_sounds=self.chomp_sound, start_time=now)
                    elif ztype == 'conehead':
                        zombie = ConeheadZombie(x, y, row, scale=scale, chomp_sounds=self.chomp_sound, start_time=now,
                                                group=self.all_sprites)
                    elif ztype == 'bucket':
                        zombie = BucketZombie(x, y, row, scale=scale, chomp_sounds=self.chomp_sound, start_time=now,
                                              group=self.all_sprites)
                    else:  # 'normal'
                        zombie = NormalZombie(x, y, row, scale=scale, chomp_sounds=self.chomp_sound, start_time=now)
                    # 以下为原有生成逻辑
                    print(
                        f"[{now}] 生成 {ztype} 行{row}, 波次 {self.wave_manager.current_wave_index}, 当前保护行: {[r for r in range(LAWN_ROWS) if r in self.wave_manager.row_protected_until_wave and self.wave_manager.current_wave_index <= self.wave_manager.row_protected_until_wave[r]]}")
                    zombie.death_callback = self.on_zombie_death  # 添加这一行
                    self.zombies.add(zombie)
                    self.all_sprites.add(zombie)


            #判断是否使用小推车
            self.mowers.update(dt, self.viewport_x)

            # 检查触发条件：如果有僵尸到达房子（world_x <= 70）且该行有小推车未触发
            for zombie in self.zombies:
                if zombie.world_x <= LAWNMOWER_TRIGGER_X:
                    # 找到同一行的小推车
                    for mower in self.mowers:
                        if mower.row == zombie.row and mower.state == 'idle':
                            mower.trigger()
                            # ★ 记录该行触发时间
                            print(f"[{now}] 行{mower.row} 小推车触发，当前波次 {self.wave_manager.current_wave_index}")
                            self.wave_manager.protect_row(mower.row, self.wave_manager.current_wave_index)
                            break  # 每行只有一个，触发后退出循环

            # 小推车与僵尸碰撞检测（移动中的小推车杀死僵尸）
            for mower in self.mowers:
                if mower.state == 'moving':
                    # 检测与该行僵尸的碰撞
                    for zombie in list(self.zombies):
                        if zombie.row == mower.row and zombie.rect.colliderect(mower.rect):
                            # 从 zombies 组移除，避免后续碰撞
                            self.zombies.remove(zombie)
                            self.wave_manager.zombie_killed()
                            # 触发碾压动画
                            zombie.squash(now)
                            # 将头加入 all_sprites
                            if zombie.head:
                                self.all_sprites.add(zombie.head)

            # 向日葵生产阳光
            for plant in self.plants:
                if isinstance(plant, Sunflower):
                    if plant.can_produce(now):
                        sun = plant.produce(now)
                        self.sun_sprites.add(sun)

            # 自然掉落阳光
            if now - self.last_sun_drop > SUN_DROP_INTERVAL:
                self.last_sun_drop = now
                # 生成临时阳光以获取宽度（或者预先定义常量）
                temp_sun = Sun(0, 0)  # 临时创建，仅用于获取尺寸
                sun_width = temp_sun.rect.width
                temp_sun.kill()  # 立即销毁

                # 安全边界
                margin = 50
                min_screen_x = margin
                max_screen_x = SCREEN_WIDTH - sun_width - margin

                # 确保范围有效
                if max_screen_x < min_screen_x:
                    max_screen_x = min_screen_x  # 避免负数

                screen_x = random.randint(min_screen_x, max_screen_x)
                world_x = screen_x + self.viewport_x
                y = SUN_DROP_Y_START
                sun = Sun(world_x, y,start_time=now)
                self.sun_sprites.add(sun)


            #先进性植物射击，然后更新所有画面，之后在判断是否碰撞就可以了！！！
            # 植物射击
            effective_x_limit = BACKGROUND_WIDTH * 0.78
            for plant in self.plants:
                if isinstance(plant, Peashooter) and plant.can_shoot(now):
                    for zombie in self.zombies:
                        if zombie.state == Zombie.STATE_DIE:
                            continue
                        if (zombie.row == plant.row
                                and zombie.world_x > plant.world_x-60 #+ plant.rect.width
                                and zombie.world_x <= effective_x_limit):
                            bullet = plant.shoot()
                            self.bullets.add(bullet)
                            self.all_sprites.add(bullet)
                            break

            # pygame.sprite.Group 本身内置了 update() 方法
            for sprite in self.all_sprites:
                if isinstance(sprite, CherryBomb):
                    sprite.update(now, self.viewport_x)
                else:
                    sprite.update(now)

            # 更新屏幕坐标（为碰撞检测做准备）
            self.update_screen_positions()

            # 更新铲子悬停状态
            if self.shovel_mode:
                # 先重置所有植物的悬停标志
                for plant in self.plants:
                    plant.shovel_hover = False
                # 获取鼠标屏幕坐标
                mx, my = pygame.mouse.get_pos()
                # 遍历所有植物，检测碰撞
                for plant in self.plants:
                    # 使用植物的屏幕 rect 进行碰撞检测（注意：plant.rect 在 update_screen_positions 中已更新）
                    if plant.rect.collidepoint(mx, my):
                        plant.shovel_hover = True
                        break  # 只允许一个植物悬停
            else:
                # 铲子模式关闭，清除所有悬停标志
                for plant in self.plants:
                    plant.shovel_hover = False


            # 子弹与僵尸碰撞
            BULLET_EFFECTIVE_RATIO = 0.8
            BULLET_EFFECTIVE_X_LIMIT = BACKGROUND_WIDTH * BULLET_EFFECTIVE_RATIO
            for bullet in self.bullets:
                for zombie in self.zombies:
                    if zombie.state == Zombie.STATE_DIE:
                        continue
                    if zombie.row != bullet.row:
                        continue
                    if zombie.world_x > BULLET_EFFECTIVE_X_LIMIT:
                        continue
                    if zombie.collision_rect.colliderect(bullet.rect):
                        if self.splat_sounds:
                            random.choice(self.splat_sounds).play()
                        zombie.take_damage(bullet.damage)
                        if zombie.health <= 70:
                            self.wave_manager.zombie_killed()
                        bullet.kill()
                        break

            # 樱桃炸弹爆炸处理
            for plant in list(self.plants):
                if isinstance(plant, CherryBomb) and plant.exploded:
                    # 炸弹中心坐标（格子中心）
                    bomb_cx = plant.world_x + CELL_WIDTH / 2
                    bomb_cy = plant.world_y + CELL_HEIGHT / 2



                    for zombie in list(self.zombies):
                        if zombie.state == Zombie.STATE_DIE:
                            continue
                        # 僵尸中心坐标（使用碰撞盒中心）
                        z_cx = zombie.world_x + zombie.rect.width / 2+30
                        z_cy = zombie.world_y + zombie.rect.height / 2

                        dx = abs(z_cx - bomb_cx)
                        dy = abs(z_cy - bomb_cy)

                        # 3×3 格子的最大距离：半个格子到相邻格子最远点
                        if dx <= 1.55 * CELL_WIDTH and dy <= 1.5 * CELL_HEIGHT:
                            ash = ZombieCharred(
                                x=zombie.world_x+60   ,  # 根据实际图片微调
                                y=zombie.world_y+60 ,  # 脚部位置
                                row=zombie.row,  # 传入 row
                                start_time=self.game_time
                            )
                            self.all_sprites.add(ash)
                            zombie.kill()
                            self.wave_manager.zombie_killed()

                    plant.exploded = False  # 防止重复爆炸

            # 僵尸与植物碰撞
            for zombie in self.zombies:
                if zombie.state == Zombie.STATE_DIE:
                    continue
                same_row_plants = [p for p in self.plants if
                                   p.row == zombie.row and
                                   not isinstance(p, CherryBomb) and
                                   p.rect.colliderect(zombie.collision_rect)
                                   and p.world_x-100 < zombie.world_x ]

                if same_row_plants:
                    target = max(same_row_plants, key=lambda p: p.rect.right)
                    zombie.attack(target)
                else:
                    zombie.stop_attack()

            # 检查僵尸到达房子
            for zombie in self.zombies:
                if zombie.world_x <= 70:
                    if self.state != 'fail_animation':
                        self.state = 'fail_animation'
                        self.stop_bgm()  # 停止所有背景音乐
                        self.fail_anim_start = now
                        self.leftmost_zombie = zombie
                        # if self.background_music_playing:
                        #     pygame.mixer.music.stop()
                        #     self.background_music_playing = False
                        if self.lose_sound and not self.lose_played:
                            self.lose_sound.play()
                            self.lose_played = True
                    break

            # 清理死亡植物
            # 清理死亡植物
            for row in range(LAWN_ROWS):
                for col in range(LAWN_COLS):
                    plants = self.lawn.get_plants_at(row, col)
                    for plant in plants[:]:  # 使用副本遍历
                        if not plant.alive():
                            plant.kill()  # 从精灵组移除
                            self.lawn.remove_plant(plant)  # 从格子移除

        elif self.state == "win_delay":
            # self.sun_sprites.update(now, dt, self.viewport_x)
            # 自动收集阳光（如果开启）
            if self.cheat_config.get("auto_collect_sun"):
                for sun in list(self.sun_sprites):
                    if sun.state != 'collecting' and not getattr(sun, 'collect_finished',
                                                                 False) and now >= sun.auto_collect_time:
                        sun.start_collect(now, self.viewport_x)
            # 收集完成的阳光
            for sun in list(self.sun_sprites):
                if hasattr(sun, 'collect_finished') and sun.collect_finished:
                    self.sun_amount += sun.value
                    if self.cheat_config.get("sun_infinite"):
                        self.sun_amount = 9999
                    elif not self.cheat_config.get("sun_unlimited"):
                        if self.sun_amount > 9999:
                            self.sun_amount = 9999
                    sun.kill()
            for sprite in self.all_sprites:
                if isinstance(sprite, CherryBomb):
                    sprite.update(now, self.viewport_x)
                else:
                    sprite.update(now)

            self.mowers.update(dt, self.viewport_x)
            # 更新屏幕坐标（为碰撞检测和绘制准备）
            # self.update_screen_positions()
            # 2. 检查所有动画是否结束
            all_done = True
            # 检查是否还有活着的僵尸（包括死亡动画中的）
            if len(self.zombies) > 0:
                all_done = False
            # 检查是否还有灰烬（ZombieCharred）
            for sprite in self.all_sprites:
                if isinstance(sprite, ZombieCharred):
                    # 如果灰烬动画未结束（取决于其内部实现，通常会在动画完成后kill自己）
                    # 这里简单认为只要存在就未结束
                    all_done = False
                    break
            # 检查是否有移动中的小推车（未移出屏幕）
            for mower in self.mowers:
                if mower.state == 'moving':
                    all_done = False
                    break
            # 可选：增加超时保护，防止动画卡死（比如5秒后强制进入胜利）
            # if now - self.win_delay_start > 5000:
            #     all_done = True
            # 3. 如果所有动画结束，进入胜利状态
            if all_done and (now - self.win_delay_start >= 3000):
                if self.win_sound and not self.win_played:
                    self.win_sound.play()
                    self.win_played = True
                self.state = 'win'
                self.win_start = now
                self.create_light_mask()
                self.stop_bgm()
                if self.current_level is not None:
                    next_level = self.current_level + 1
                    if next_level > self.unlocked_level:
                        self.unlocked_level = next_level
                        self.save_user_data()

        elif self.state == 'win':
            # 更新光芒动画
#胜利的动画出现太早
#如果是小推车杀死全局最后一只僵尸就要等待小推车离开屏幕才模仿光芒动画，
# 如果是炸死的，就要等待charred动画结束，如果是正常打死的就要等待zombiedie动画结束
            if self.shine_alpha < self.shine_max_alpha: #遮罩程度逐渐变深
                self.shine_alpha += self.shine_fade_speed
                if self.shine_alpha > self.shine_max_alpha:
                    self.shine_alpha = self.shine_max_alpha
            self.shine_angle += self.shine_rotation_speed
            # if self.bgm2_sound:
            #     self.bgm2_sound.stop()

        elif self.state == 'fail_animation':

            total_distance = VIEWPORT_LEFT_OFFSET - VIEWPORT_FAIL_OFFSET
            #一帧FPS只运行一次代码，所以这里计算一帧需要移动多少
            delta = total_distance / (self.fail_anim_duration / 1000 * FPS)
            self.viewport_x = max(self.viewport_x - delta, 0)

            if self.leftmost_zombie and self.leftmost_zombie.alive():
                self.leftmost_zombie.update_animation(now)

            time_up = real_now - self.fail_anim_start >= self.fail_anim_duration
            if time_up or self.viewport_x <= 0:
                self.state = 'gameover'
                self.viewport_x = VIEWPORT_FAIL_OFFSET
                self.gameover_scale = 0.3
                self.gameover_anim_finished = False


        elif self.state == 'gameover':
            if self.gameover_delay_start is None:
                self.gameover_delay_start = now

            if not self.gameover_visible and real_now - self.gameover_delay_start >= self.GAMEOVER_DELAY:
                self.gameover_visible = True
                self.gameover_scale = 0.3
                self.gameover_anim_finished = False

            if self.gameover_visible:
                if self.gameover_scale < 1.0:
                    self.gameover_scale += self.gameover_scale_speed
                    if self.gameover_scale >= 1.0:
                        self.gameover_scale = 1.0
                        self.gameover_anim_finished = True

                orig_size = self.gameover_raw_image.get_size()
                new_size = (int(orig_size[0] * self.gameover_scale),
                            int(orig_size[1] * self.gameover_scale))
                self.gameover_image = pygame.transform.scale(self.gameover_raw_image, new_size)
            else:
                self.gameover_image = None

    def draw(self):
        def get_font(size=36):
            return self.font_chinese if self.font_chinese else pygame.font.Font(None, size)
        # 1. 绘制背景（所有状态共用）
        self.screen.blit(self.full_background, (0, 0),
                         (self.viewport_x, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

        # 2. 根据状态绘制不同内容
        if self.state == 'intro':
            # 绘制开场僵尸
            for zombie in self.opening_zombies:
                screen_x = zombie.world_x - self.viewport_x
                screen_y = zombie.world_y
                self.screen.blit(zombie.image, (screen_x, screen_y))
            # 绘制开始按钮
#handle中同步添加 选卡的状态

            pygame.draw.rect(self.screen, (0, 100, 255), self.new_game_rect)   # 深绿色
            pygame.draw.rect(self.screen, (255, 255, 255), self.new_game_rect, 2)  # 白色边框

            text = get_font(36).render("新游戏", True, (255, 255, 255))
            text_rect = text.get_rect(center=self.new_game_rect.center)
            self.screen.blit(text, text_rect)

            # 绘制继续按钮
            if self.unlocked_level < len(LEVELS):
                btn_color = (255, 165, 0)  # 绿色
                btn_text = f"继续 (第{self.unlocked_level + 1}关)"
            else:
                btn_color = (100, 100, 100)  # 灰色
                btn_text = "最后一关"
            pygame.draw.rect(self.screen, btn_color, self.continue_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), self.new_game_rect, 2)  # 白色边框
            text = get_font(36).render(btn_text, True, (255, 255, 255))
            text_rect = text.get_rect(center=self.continue_rect.center)
            self.screen.blit(text, text_rect)

            # 显示进度文本
            progress_font = self.font_chinese if self.font_chinese else pygame.font.Font(None, 30)
            progress_text = progress_font.render(f"通关进度: {self.unlocked_level}/{len(LEVELS)}", True,
                                                 (255, 255, 255))
            self.screen.blit(progress_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 120))

        elif self.state in ('battle', 'transition_to_battle', 'fail_animation',"win_delay"):
            # 更新所有游戏实体的屏幕坐标

            self.update_screen_positions()

            # 将子弹和其他精灵分开（子弹应在植物/僵尸上方）
            bullets = [s for s in self.all_sprites if isinstance(s, Bullet)]
            others = [s for s in self.all_sprites if not isinstance(s, Bullet)]
            others.sort(key=lambda s: (s.row, s.world_x))  # 按行和x坐标排序，保证前后遮挡关系

            if self.state in ('battle', 'win_delay'):
                for mower in self.mowers:
                    self.screen.blit(mower.image, mower.rect)

                def draw_ui():
                    if self.seed_bank_img:
                        self.screen.blit(self.seed_bank_img, (0, 0))
                        # 显示阳光数量（如果取消上限开启，显示实际值，否则最大9999）
                        if self.cheat_config.get("sun_unlimited"):
                            display_sun = self.sun_amount
                        else:
                            display_sun = min(self.sun_amount, 9999)
                        sun_text = self.sun_font.render(f"{display_sun}", True, (0, 0, 0))
                        text_rect = sun_text.get_rect(center=(50, 80))
                        self.screen.blit(sun_text, text_rect)
                    else:
                        # 无种子袋图片时的备用显示
                        display_sun = self.sun_amount if self.cheat_config.get("sun_unlimited") else min(self.sun_amount,
                                                                                                         9999)
                        sun_text = self.sun_font.render(f"{display_sun}", True, (255, 255, 0))
                        self.screen.blit(sun_text, (10, 10))

                    # now = pygame.time.get_ticks()  # 用于冷却计算
                    game_now = self.game_time
                    # 卡片底图
                    self.screen.blit(self.peashooter_card_img, self.card_rects[0].topleft)
                    self.screen.blit(self.sunflower_card_img, self.card_rects[1].topleft)
                    self.screen.blit(self.cherrybomb_card_img,self.card_rects[2].topleft)
                    self.screen.blit(self.wallnut_card_img, self.card_rects[3].topleft)
                    # 定义绘制卡片遮罩的函数（冷却和阳光不足）
                    def draw_card_mask(rect, plant_name):
                        price = PLANT_PRICES[plant_name]
                        cooldown = PLANT_COOLDOWNS[plant_name]
                        last_time = self.last_plant_time[plant_name]

                        elapsed = cooldown if last_time == 0 else game_now - last_time
                        is_cooling = (elapsed < cooldown) and not self.cheat_config.get("no_cooldown")
                        is_no_sun = self.sun_amount < price

                        # 阳光不足遮罩（底层）
                        if is_no_sun:
                            mask = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
                            mask.fill((128, 128, 128, 120))
                            self.screen.blit(mask, rect.topleft)

                        # 冷却遮罩（上层，从顶部向下覆盖）
                        if is_cooling:
                            remaining_ratio = 1 - (elapsed / cooldown)
                            mask = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
                            mask.fill((0, 0, 0, 180))
                            mask_height = int(remaining_ratio * CARD_HEIGHT)
                            self.screen.blit(mask, rect.topleft, pygame.Rect(0, 0, CARD_WIDTH, mask_height))

                    # 应用遮罩
                    draw_card_mask(self.card_rects[0], 'peashooter')
                    draw_card_mask(self.card_rects[1], 'sunflower')
                    draw_card_mask(self.card_rects[2], 'cherrybomb')
                    draw_card_mask(self.card_rects[3], 'wallnut')
                    # 绘制选中边框
                    if self.selected_card == 0:
                        pygame.draw.rect(self.screen, (0, 255, 0), self.card_rects[0], 3)
                    elif self.selected_card == 1:
                        pygame.draw.rect(self.screen, (0, 255, 0), self.card_rects[1], 3)
                    elif self.selected_card == 2:
                        pygame.draw.rect(self.screen, (0, 255, 0), self.card_rects[2], 3)
                    elif self.selected_card == 3:
                        pygame.draw.rect(self.screen, (0, 255, 0), self.card_rects[3], 3)

                    # 卡片底图已绘制，接着绘制铲子背景和图标
                    if self.shovel_bank_img:
                        self.screen.blit(self.shovel_bank_img, self.shovel_rect.topleft)
                    if self.shovel_img and not self.shovel_mode:
                        self.screen.blit(self.shovel_img, self.shovel_rect.topleft)
                    # 绘制选中边框
                    if self.shovel_mode:
                        pygame.draw.rect(self.screen, (0, 255, 0), self.shovel_rect, 3)

                    # 绘制旗帜进度条
                    # 绘制旗帜进度条（从右向左）
                    if self.flag_empty and self.flag_full:
                        # 绘制空进度条（背景）
                        self.screen.blit(self.flag_empty, self.flag_rect)
                        # 根据进度绘制满进度条的右侧部分
                        if self.flag_progress > 0:
                            full_width = int(FLAGMETER_SIZE[0] * self.flag_progress)
                            if full_width > 0:
                                # 裁剪满进度条的右侧部分
                                sub_rect = pygame.Rect(FLAGMETER_SIZE[0] - full_width, 0, full_width, FLAGMETER_SIZE[1])
                                full_sub = self.flag_full.subsurface(sub_rect)
                                # 在屏幕上绘制在矩形右侧对应位置
                                dest_x = self.flag_rect.x + (FLAGMETER_SIZE[0] - full_width)
                                self.screen.blit(full_sub, (dest_x, self.flag_rect.y))
                    if self.selected_card is not None:
                        i = self.selected_card
                        rect = self.card_rects[i]
                        mask = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
                        mask.fill((64, 64, 64, 250))  # 深灰色半透明
                        self.screen.blit(mask, rect.topleft)
                if not self.ui_on_top:
                    draw_ui()
                    # 绘制非子弹精灵（植物、僵尸）
                    for sprite in others:
                        if isinstance(sprite, Plant) and sprite.shovel_hover:
                            # 动态生成变亮图像
                            img = sprite.image
                            temp_surf = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                            temp_surf.blit(img, (0, 0))
                            # 白色叠加层，透明度 128，使用 ADD 模式变亮
                            white_surf = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                            white_surf.fill((120, 120, 120, 40))
                            temp_surf.blit(white_surf,(0, 0), special_flags=pygame.BLEND_RGB_ADD)
                            self.screen.blit(temp_surf, sprite.rect)
                        else:
                            self.screen.blit(sprite.image, sprite.rect)

                    # 绘制子弹
                    for sprite in bullets:
                        self.screen.blit(sprite.image, sprite.rect)

                else:
                    # 绘制非子弹精灵（植物、僵尸）
                    for sprite in others:
                        if isinstance(sprite, Plant) and sprite.shovel_hover:
                            # 动态生成变亮图像
                            img = sprite.image
                            temp_surf = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                            temp_surf.blit(img, (0, 0))
                            # 白色叠加层，透明度 128，使用 ADD 模式变亮
                            white_surf = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                            white_surf.fill((120, 120, 120, 40))
                            temp_surf.blit(white_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
                            self.screen.blit(temp_surf, sprite.rect)
                        else:
                            self.screen.blit(sprite.image, sprite.rect)

                    # 绘制子弹
                    for sprite in bullets:
                        self.screen.blit(sprite.image, sprite.rect)
                    draw_ui()


            else:
                # 非战斗和win_delay状态（transition_to_battle / fail_animation）：只绘制精灵，不绘制 UI
                for sprite in others:
                    self.screen.blit(sprite.image, sprite.rect)
                for sprite in bullets:
                    self.screen.blit(sprite.image, sprite.rect)

            # 最后绘制阳光（确保在最上层，覆盖UI）
            for sun in self.sun_sprites:
                self.screen.blit(sun.image, sun.rect)

            # 绘制种植预览阴影（仅当选中卡片且鼠标位于可种植的空格）
            if self.state == 'battle' and self.selected_card is not None:
                mx, my = pygame.mouse.get_pos()
                world_x = mx + self.viewport_x
                world_y = my
                col = int((world_x - LAWN_TOP_LEFT_X) / CELL_WIDTH)
                row = int((world_y - LAWN_TOP_LEFT_Y) / CELL_HEIGHT)
                if (LAWN_TOP_LEFT_X <= world_x <= LAWN_BOTTOM_RIGHT_X and
                        LAWN_TOP_LEFT_Y <= world_y <= LAWN_BOTTOM_RIGHT_Y):
                # 检查是否在草坪范围内且该格子没有植物

                    plants_in_cell = self.lawn.get_plants_at(row, col)
                    show_preview=False
                    if self.cheat_config.get("overlap_plant") :
                        show_preview=True
                    if not plants_in_cell:
                        show_preview=True
                    elif self.selected_card==3: #坚果墙
                        for p in plants_in_cell:
                            if isinstance(p,Wallnut) and p.current_state!="normal":
                                show_preview=True
                                break




                    if show_preview:  # 格子为空
                        cell_screen_x = LAWN_TOP_LEFT_X - self.viewport_x + col * CELL_WIDTH
                        cell_screen_y = LAWN_TOP_LEFT_Y + row * CELL_HEIGHT
                        if self.selected_card == 0:  # 豌豆射手
                            self.screen.blit(self.peashooter_preview, (cell_screen_x, cell_screen_y))
                        elif self.selected_card == 1:  # 向日葵
                            self.screen.blit(self.sunflower_preview, (cell_screen_x, cell_screen_y))
                        elif self.selected_card == 2:  # 樱桃炸弹
                            self.screen.blit(self.cherrybomb_preview, (cell_screen_x, cell_screen_y))
                        elif self.selected_card == 3:  # 坚果
                            self.screen.blit(self.wallnut_preview, (cell_screen_x, cell_screen_y))






            else:
                # 非战斗状态（transition_to_battle, fail_animation）直接绘制阳光（无UI）
                for sun in self.sun_sprites:
                    self.screen.blit(sun.image, sun.rect)

        elif self.state == 'dave_dialogue':
            self.dave.draw(self.screen)

        elif self.state == 'ready_set_plant':
            # 绘制居中的 Ready/Set/Plant 图片
            if self.ready_set_plant_index == 0:
                self.screen.blit(self.ready_img, self.ready_rect)
            elif self.ready_set_plant_index == 1:
                self.screen.blit(self.set_img, self.set_rect)
            elif self.ready_set_plant_index == 2:
                self.screen.blit(self.plant_img, self.plant_rect)


        elif self.state == 'win':
            # 绘制游戏实体（植物、僵尸等）
            self.update_screen_positions()
            self.all_sprites.draw(self.screen)
            # 绘制小推车（未丢失的）
            for mower in self.mowers:
                self.screen.blit(mower.image, mower.rect)
            # 全屏白色叠加层（透明度随 shine_alpha 增加）
            white_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            white_overlay.set_alpha(self.shine_alpha)
            white_overlay.fill((255, 255, 255))
            self.screen.blit(white_overlay, (0, 0))

            # 绘制旋转光影遮罩（也受 shine_alpha 影响整体透明度）
            if self.light_mask and self.shine_alpha > 0:
                rotated_mask = pygame.transform.rotate(self.light_mask, self.shine_angle)
                mask_rect = rotated_mask.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                rotated_mask.set_alpha(self.shine_alpha)  # 整体透明度随 alpha 变化
                self.screen.blit(rotated_mask, mask_rect)  # 普通混合，不加特殊标志

            # 绘制静止的奖杯
            if self.trophy_img:
                trophy_rect = self.trophy_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(self.trophy_img, trophy_rect)

            # 胜利文字和点击提示（保持原样）
            try:
                if self.font_chinese:
                    text = self.font_chinese.render("胜利！", True, (255, 215, 0))
                else:
                    text = pygame.font.Font(None, 36).render("Victory!", True, (255, 215, 0))
            except:
                text = pygame.font.Font(None, 36).render("Victory!", True, (255, 215, 0))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
            self.screen.blit(text, text_rect)

            #这个中文不会显示，会进入else语句
            if self.font_chinese:
                tip = self.font_chinese.render("点击屏幕继续", True, (50, 50, 50))  # 深灰色
            else:
                tip = pygame.font.Font(None, 30).render("Click to continue", True, (50, 50, 50))
            tip_rect = tip.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
            self.screen.blit(tip, tip_rect)

        elif self.state == 'gameover':
            # 绘制所有游戏实体
            self.update_screen_positions()
            self.all_sprites.draw(self.screen)

            # 半透明黑幕
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))

            # GameOver 图片动画
            if self.gameover_image:
                img_rect = self.gameover_image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(self.gameover_image, img_rect)

            # 点击继续提示
            if self.gameover_anim_finished:
                try:
                    if self.font_chinese:
                        text = self.font_chinese.render("点击屏幕继续", True, WHITE)
                    else:
                        raise Exception("无中文字体")
                except:
                    font_en = pygame.font.Font(None, 30)
                    text = font_en.render("Click to continue", True, WHITE)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
                self.screen.blit(text, text_rect)

        # 3. 绘制血条（仅当显示且存在僵尸时）
        if self.show_health_bars and self.zombies and self.state != 'win':
            for zombie in self.zombies:
                health_ratio = max(0, zombie.health / zombie.max_health)
                bar_width = zombie.rect.width // 1.8
                bar_height = 10
                bar_x = int(zombie.rect.x + zombie.rect.width * 0.3)
                bar_y = zombie.rect.y - bar_height + 100
                # 背景框
                pygame.draw.rect(self.screen, (0, 0, 0), (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2), 0)
                pygame.draw.rect(self.screen, (255, 255, 255), (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2), 1)
                # 血条
                pygame.draw.rect(self.screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 0)
                red_width = int(bar_width * health_ratio)
                if red_width > 0:
                    pygame.draw.rect(self.screen, (255, 0, 0), (bar_x, bar_y, red_width, bar_height), 0)
                # 文字
                hp_text = f"HP: {int(zombie.health)}"
                text_surf = self.health_font.render(hp_text, True, (0, 255, 0))
                text_rect = text_surf.get_rect(center=(zombie.rect.centerx, bar_y + 5))
                self.screen.blit(text_surf, text_rect)

        # 绘制鼠标跟随的铲子（如果铲子模式）
        if self.shovel_mode and self.shovel_img:
            mx, my = pygame.mouse.get_pos()
            cursor_rect = self.shovel_img.get_rect()
            cursor_rect.bottomleft = (mx-10, my+10)  # 图片左下角对齐鼠标（铲尖）
            self.screen.blit(self.shovel_img, cursor_rect)

        if not self.shovel_mode and self.selected_card is not None and self.preview_follow_img:
            mx, my = pygame.mouse.get_pos()
            # 图片中心对准鼠标（可调整为其他对齐方式）
            preview_rect = self.preview_follow_img.get_rect(center=(mx, my))
            self.screen.blit(self.preview_follow_img, preview_rect)


        # 绘制暂停图片（位于最上层）
        if self.state == 'battle' and self.paused:
            self.screen.blit(self.suspend_image, self.suspend_rect)
        pygame.display.flip()# ！！！如果没有这行直接黑屏

    #这里没有啥用
    # def draw_grid(self):
    #     for row in range(LAWN_ROWS):
    #         for col in range(LAWN_COLS):
    #             rect = pygame.Rect(LAWN_TOP_LEFT_X - self.viewport_x + col * CELL_WIDTH,
    #                                LAWN_TOP_LEFT_Y + row * CELL_HEIGHT,
    #                                CELL_WIDTH, CELL_HEIGHT)
    #             pygame.draw.rect(self.screen, (0, 255, 0), rect, 1)