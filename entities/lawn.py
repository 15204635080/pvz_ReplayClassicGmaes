# entities/lawn.py
from settings import LAWN_ROWS, LAWN_COLS

class LawnGrid:
    def __init__(self):
        # 每个格子存储一个植物列表，按添加顺序排列
        self.grid = [[[] for _ in range(LAWN_COLS)] for _ in range(LAWN_ROWS)]

    def add_plant(self, row, col, plant):
        """普通种植：格子必须为空才添加（用于非作弊模式）"""
        if 0 <= row < LAWN_ROWS and 0 <= col < LAWN_COLS and not self.grid[row][col]:
            self.grid[row][col].append(plant)
            return True
        return False

    def add_plant_overlap(self, row, col, plant):
        """重叠种植：直接追加到列表末尾（用于作弊模式）"""
        if 0 <= row < LAWN_ROWS and 0 <= col < LAWN_COLS:
            self.grid[row][col].append(plant)
            return True
        return False

    def remove_plant(self, plant):
        """从格子中移除指定的植物（当植物死亡或被铲除时调用）"""
        for row in range(LAWN_ROWS):
            for col in range(LAWN_COLS):
                if plant in self.grid[row][col]:
                    self.grid[row][col].remove(plant)
                    return True
        return False

    def get_plants_at(self, row, col):
        """返回该格子的所有植物列表（可能为空）"""
        if 0 <= row < LAWN_ROWS and 0 <= col < LAWN_COLS:
            return self.grid[row][col]
        return []

    def get_plant_at(self, row, col):
        """返回该格子的第一个植物（兼容旧代码）"""
        plants = self.get_plants_at(row, col)
        return plants[0] if plants else None