# settings.py
import pygame

# 屏幕尺寸
SCREEN_WIDTH =1080
SCREEN_HEIGHT = 600

# 背景图片尺寸
BACKGROUND_WIDTH = 1400
BACKGROUND_HEIGHT = 600

# 视口偏移量
VIEWPORT_RIGHT_OFFSET = BACKGROUND_WIDTH - SCREEN_WIDTH
# VIEWPORT_LEFT_OFFSET = int(BACKGROUND_WIDTH * 0.06)
VIEWPORT_LEFT_OFFSET = 84# 84 (6% 位置)
VIEWPORT_FAIL_OFFSET = 0                                 # 失败时显示最左边

# 过渡速度（像素/秒）
TRANSITION_SPEED = 300
# 游戏标题
TITLE = "植物大战僵尸"
# settings.py
ZOMBIE_BASE_SPEED = 0.273  # 像素/帧，与 NormalZombie 的 speed 一致
# 帧率
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# 草坪参数（5行 x 9列，根据实际背景调整偏移和格子大小）

# 资源根目录
IMAGE_DIR = "images/"
SOUND_DIR = "music/"


PEASHOOTER_FRAMES = 13      # Peashooter_00 ~ Peashooter_12
SUNFLOWER_FRAMES = 13       # SunFlower_00 ~ SunFlower_12
WALLNUT_FRAMES = 13         # WallNut_00 ~ WallNut_12（裂纹状态可后续添加）
ZOMBIE_WALK_FRAMES = 22     # Zombie_0 ~ Zombie_21
ZOMBIE_ATTACK_FRAMES = 21   # ZombieAttack_0 ~ ZombieAttack_20
ZOMBIE_DIE_FRAMES = 10      # ZombieDie_0 ~ ZombieDie_9

# 可种植区域坐标（世界坐标，相对于背景图左上角）
LAWN_TOP_LEFT_X = 258
LAWN_TOP_LEFT_Y = 93
LAWN_BOTTOM_RIGHT_X = 995
LAWN_BOTTOM_RIGHT_Y = 576
LAWN_COLS = 9
LAWN_ROWS = 5

# 计算每个格子的尺寸（浮点数，保证精确覆盖整个区域）
CELL_WIDTH = (LAWN_BOTTOM_RIGHT_X - LAWN_TOP_LEFT_X) / LAWN_COLS   # ≈ 81.888...
CELL_HEIGHT = (LAWN_BOTTOM_RIGHT_Y - LAWN_TOP_LEFT_Y) / LAWN_ROWS  # = 99.0


#音频管理

LOSE_SOUND = "lose.mp3"

#是否看过戴夫动画
DAVE_SEEN_FILE = ".dave_seen"


#植物卡背景
seedbank_x=600
seedbank_y=90


#阳光相关
# ========== 阳光系统配置（新增/修改） ==========
SUN_SCALE = 1.3                         # 阳光放大比例
SUN_ANIMATION_FOLDER = "sun"
SUN_ANIMATION_PREFIX = "Sun_"
SUN_ANIMATION_COUNT = 17
SUN_ANIMATION_START_INDEX = 1
SUN_ANIMATION_DIGITS = 1
SUN_ANIMATION_SPEED = 12
SUN_LIFETIME = 20000                      # 落地后存在时间（毫秒）
SUN_FADE_DURATION = 2000                   # 消失前闪烁持续时间（毫秒）
SUN_DEFAULT_VALUE = 25
SUN_FALL_SPEED = 75                         # 下落速度（像素/秒）
SUN_DROP_INTERVAL = 10000                    # 自然掉落间隔（毫秒）
SUN_DROP_X_RANGE = (200, BACKGROUND_WIDTH - 200)  # 自然掉落x坐标范围（世界坐标）
SUN_DROP_Y_START = -100                        # 掉落起始y坐标
# 新增：落地高度范围（草坪中下部，世界坐标）
SUN_LAND_Y_MIN = int(LAWN_TOP_LEFT_Y + 2 * CELL_HEIGHT)   # 约第三行
SUN_LAND_Y_MAX = int(LAWN_TOP_LEFT_Y + (LAWN_ROWS - 1) * CELL_HEIGHT)  # 最后一行
# 新增：收集动画持续时间（毫秒）
SUN_COLLECT_DURATION = 1000
# UI 图片
SEED_BANK_IMAGE = "screen/SeedBank.png"    # 阳光UI背景图
SUN_UI_POS = (10, 10)

# 向日葵配置
SUNFLOWER_ANIMATION_FOLDER = "sunflower"
SUNFLOWER_ANIMATION_PREFIX = "SunFlower_"
SUNFLOWER_ANIMATION_COUNT = 13
SUNFLOWER_ANIMATION_START_INDEX = 0
SUNFLOWER_ANIMATION_DIGITS = 2          # 文件名如 SunFlower_00.png
SUNFLOWER_ANIMATION_SPEED = 0.1          # 动画速度（秒/帧），与豌豆射手保持一致
SUNFLOWER_PRODUCE_INTERVAL = 24000      # 产生阳光间隔（毫秒），原版约24秒
SUNFLOWER_PRODUCE_VALUE = 25            # 每次产生的阳光价值
SUNFLOWER_PRICE = 50                     # 种植所需阳光（后续启用）




# ========== 卡片配置 ==========
CARD_WIDTH = 80
CARD_HEIGHT = 80
CARD_PEASHOOTER_ICON ="cards\card_peashooter.png"  # 豌豆射手卡片图标
CARD_SUNFLOWER_ICON = "cards\card_sunflower.png"      # 向日葵卡片图标
CARD_CHERRYBOMB_ICON="cards\card_cherrybomb.png"
CARD_WALLNUT_ICON="cards\card_wallnut.png"
CARD_START_X = 110                                    # 第一张卡片左上角x坐标（相对于屏幕）
CARD_START_Y = 5                                  # 卡片y坐标（种子袋下方）
CARD_SPACING = -3                                    # 卡片间距

# 植物价格
PLANT_PRICES = {
    'peashooter': 100,
    'sunflower': 50,
    'wallnut':50,
    "cherrybomb":150,
}
# 植物冷却时间（毫秒）
PLANT_COOLDOWNS = {
    'peashooter': 7000,   # 7秒
    'sunflower': 7000,    # 7秒
    'wallnut':60000,
    "cherrybomb":50000
}
# 樱桃炸弹动画帧数（图片数量）
CHERRYBOMB_FRAMES = 26

# 动画速度（秒/帧）
CHERRYBOMB_ANIMATION_SPEED = 0.05

# 爆炸触发的帧索引（从0开始，建议13）
CHERRYBOMB_EXPLODE_FRAME = 15


#小推车
# 小推车配置
LAWNMOWER_START_X = 160          # 小推车起始 x 坐标（世界坐标）
LAWNMOWER_TRIGGER_X = 160        # 触发小推车的僵尸 x 坐标阈值（可根据需要调整，例如设为 110）
LAWNMOWER_SPEED = 300             # 移动速度（像素/秒）、
# 小推车触发后该行禁止生成僵尸的冷却时间（毫秒）
MOWER_COOLDOWN = 60000
# 小推车触发后，冷却行僵尸转移的比例（0.2 表示 20%）
MOWER_TRANSFER_RATIO = 0.3
MOWER_SCALE = 0.7

#铲子
# 铲子配置
SHOVEL_ICON = "screen/Shovel.png"
SHOVEL_BANK_IMAGE = "screen/ShovelBank.png"
SHOVEL_BANK_POS = (600,0)  # 在两张卡片右侧
SHOVEL_BANK_SIZE = (CARD_WIDTH, CARD_HEIGHT)   # 与卡片大小相同

#进度
# 旗帜进度条位置和大小（右下角）
FLAGMETER_POS = (SCREEN_WIDTH - 220, SCREEN_HEIGHT - 60)   # 可微调
FLAGMETER_SIZE = (200, 40)                                  # 宽度、高度

# 僵尸灰烬动画帧数
CHARRED_FRAMES = 10
# 动画速度（秒/帧）
CHARRED_ANIMATION_SPEED = 0.2


