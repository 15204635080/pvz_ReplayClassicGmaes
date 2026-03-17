# entities/wave_manager.py
import pygame
import random
import math
from collections import deque

class WaveManager:
    """
    波次管理器：负责僵尸生成的时间、行分配、波次控制及小推车保护机制。
    与游戏主循环解耦，通过 update 方法返回需要生成的僵尸信息。
    波次配置格式：
        - 旧格式：int（只有普通僵尸）或 (int, bool)（数量和旗帜标志）
        - 新格式：({type: count, ...}, bool)  例如 ({"normal":3, "conehead":5}, False)
    """

    def __init__(self, total_zombies=None, waves=None, first_spawn_interval=5.0, last_spawn_interval=1.0,
                 first_spawn_time=30000, rows=5, emergency_multiplier=1.5,
                 flag_followers_min=4, flag_followers_max=6):
        """
        :param total_zombies: 关卡预设僵尸总数（若为 None 则自动计算）
        :param waves: 波次配置列表，元素可为 int、(int,bool) 或 (dict,bool)
        :param spawn_interval: 波次内普通僵尸生成间隔（毫秒）
        :param first_spawn_time: 兜底触发第一只僵尸的时间（毫秒）
        :param rows: 草坪行数
        """
        # 标准化 waves 为内部格式：每个元素为 (type_dict, flag)
        self.raw_waves = waves if waves is not None else [5, 7, 10, 8]
        normalized_waves = []
        for wave in self.raw_waves:
            if isinstance(wave, (int, float)):
                # 纯数字：普通波，只有普通僵尸
                normalized_waves.append(({"normal": int(wave)}, False))
            elif isinstance(wave, (tuple, list)) and len(wave) == 2:
                if isinstance(wave[0], dict):
                    # 新格式 (type_dict, flag)
                    normalized_waves.append((wave[0], wave[1]))
                else:
                    # 旧格式 (count, flag)
                    normalized_waves.append(({"normal": wave[0]}, wave[1]))
            else:
                raise ValueError(f"无效的波次格式: {wave}")
        self.waves = normalized_waves

        if total_zombies is None:
            self.total_zombies = self._calculate_total_zombies()
        else:
            self.total_zombies = total_zombies
        print("WaveManager total_zombies =", self.total_zombies)

        self.first_spawn_interval_ms = int(first_spawn_interval * 1000)
        self.last_spawn_interval_ms = int(last_spawn_interval * 1000)
        self.wave_intervals = self._calculate_wave_intervals()
        self.first_spawn_time = first_spawn_time
        self.rows = rows

        # 运行时状态
        self.game_start_time = 0
        self.first_zombie_spawned = False
        self.current_wave_index = 0       # 当前波次索引（0-based）
        self.spawned_in_wave = 0          # 当前波次已生成数量（包括旗帜）
        self.last_spawn_time = 0
        self.total_spawned = 0
        self.planted_sunflowers = 0

        # 行级冷却（上次生成时间）
        self.last_spawn_time_per_row = {}  # row -> timestamp

        # 小推车保护期（受保护到哪一波）
        self.row_protected_until_wave = {}  # row -> wave_index (含)

        self.row_max_spawn_this_wave = {}  # row -> max
        self.row_spawned_this_wave = {}    # row -> current
        self.emergency_multiplier = emergency_multiplier
        self.emergency_spawn_count_this_wave = 0
        self.flag_followers_min = flag_followers_min
        self.flag_followers_max = flag_followers_max

        self.killed_count = 0

        # 旗帜波跟随生成状态
        self.followers_to_spawn = 0        # 还需生成的跟随僵尸数
        self.followers_spawned_in_wave = 0 # 本波已生成的跟随数量（用于控制）
        self._last_protected_rows = []     # 用于调试

        self.next_wave_delay_until = 0     # 下一波延迟结束时间
        self.next_wave_is_flag = False     # 下一波是否为旗帜波（用于音效）
        self.delayed_wave_index = -1

        # 本波剩余僵尸类型队列（按生成顺序）
        self.spawn_queue = deque()         # 存储僵尸类型字符串，如 'normal', 'conehead'

    def _calculate_wave_intervals(self):
        """根据波次数量计算每个波次的生成间隔（毫秒）"""
        n = len(self.waves)
        if n == 0:
            return []
        if n == 1:
            return [self.first_spawn_interval_ms]
        intervals = []
        for i in range(n):
            ratio = i / (n - 1)
            interval = self.first_spawn_interval_ms - (
                        self.first_spawn_interval_ms - self.last_spawn_interval_ms) * ratio
            intervals.append(int(interval))
        return intervals

    def _calculate_total_zombies(self):
        """根据 waves 自动计算总僵尸数"""
        total = 0
        for type_dict, _ in self.waves:
            total += sum(type_dict.values())
        return total

    def _choose_row(self, now):
        """
        根据上限和冷却选择一行
        :return: (row, emergency) 或 (None, False)
                 emergency 为 True 表示当前处于所有行都受保护后的失效模式
        """
        eligible = [r for r in range(self.rows) if self.row_spawned_this_wave[r] < self.row_max_spawn_this_wave[r]]
        if not eligible:
            return None, False
        best_row = max(eligible, key=lambda r: now - self.last_spawn_time_per_row.get(r, 0))
        all_protected = all(
            r in self.row_protected_until_wave and self.current_wave_index <= self.row_protected_until_wave[r]
            for r in range(self.rows))
        return best_row, all_protected

    def reset(self, game_start_time):
        """重置管理器状态，在每局游戏开始时调用"""
        self.game_start_time = game_start_time
        self.first_zombie_spawned = False
        self.current_wave_index = 0
        self.spawned_in_wave = 0
        self.last_spawn_time = 0
        self.total_spawned = 0
        self.planted_sunflowers = 0
        self.last_spawn_time_per_row.clear()
        self.row_protected_until_wave.clear()
        self.emergency_spawn_count_this_wave = 0
        self.killed_count = 0
        self.followers_to_spawn = 0
        self.followers_spawned_in_wave = 0
        self.row_max_spawn_this_wave.clear()
        self.row_spawned_this_wave.clear()
        self._last_protected_rows = []
        self.spawn_queue.clear()

    def _get_current_wave_info(self):
        """获取当前波次的信息： (type_dict, flag)"""
        return self.waves[self.current_wave_index]

    def _calculate_row_limits(self):
        """计算本波次每行最大可生成数量（基于保护行和单行上限）"""
        type_dict, _ = self._get_current_wave_info()
        wave_count = sum(type_dict.values())

        # 找出受保护的行
        protected_rows = [r for r in range(self.rows) if r in self.row_protected_until_wave and self.current_wave_index <= self.row_protected_until_wave[r]]
        available_rows = [r for r in range(self.rows) if r not in protected_rows]

        if not available_rows:
            print("保护状态失效")
            available_rows = list(range(self.rows))
            protected_rows = []

        base_per_row = math.ceil(wave_count / len(available_rows))
        limit_per_row = int(base_per_row * self.emergency_multiplier + 0.5)

        self.row_max_spawn_this_wave.clear()
        self.row_spawned_this_wave.clear()
        for r in range(self.rows):
            self.row_max_spawn_this_wave[r] = limit_per_row if r in available_rows else 0
            self.row_spawned_this_wave[r] = 0

        if protected_rows != self._last_protected_rows:
            print(f"[波次 {self.current_wave_index}] 受保护行: {protected_rows}, 可用行: {available_rows}, 行上限: {self.row_max_spawn_this_wave}")
            self._last_protected_rows = protected_rows.copy()

    def _recalculate_row_limits_mid_wave(self):
        """在波次中间保护触发时，重新计算剩余僵尸的行上限，返回是否容量不足"""
        type_dict, _ = self._get_current_wave_info()
        wave_count = sum(type_dict.values())
        remaining = wave_count - self.spawned_in_wave
        if remaining <= 0:
            return False

        protected_rows = [r for r in range(self.rows) if r in self.row_protected_until_wave and self.current_wave_index <= self.row_protected_until_wave[r]]
        available_rows = [r for r in range(self.rows) if r not in protected_rows]

        if not available_rows:
            available_rows = list(range(self.rows))
            protected_rows = []

        base_per_row = math.ceil(remaining / len(available_rows))
        limit_per_row = int(base_per_row * self.emergency_multiplier + 0.5)
        total_capacity = limit_per_row * len(available_rows)

        for r in range(self.rows):
            self.row_max_spawn_this_wave[r] = limit_per_row if r in available_rows else 0

        print(f"[波次中间] 剩余 {remaining} 只, 新上限: {self.row_max_spawn_this_wave}, 总容量: {total_capacity}")
        return total_capacity < remaining

    def protect_row(self, row, current_wave_index):
        if current_wave_index >= len(self.waves):
            print(f"[保护忽略] 波次 {current_wave_index} 已超出范围，忽略保护行{row}")
            return
        self.row_protected_until_wave[row] = current_wave_index + 2
        print(f"[保护] 行{row} 被保护到波次 {current_wave_index + 2} (触发波次 {current_wave_index})")
        insufficient = self._recalculate_row_limits_mid_wave()
        if insufficient:
            type_dict, _ = self._get_current_wave_info()
            self.spawned_in_wave = sum(type_dict.values())  # 强制结束本波
            print(f"[波次提前结束] 波次 {self.current_wave_index} 因容量不足，强制结束")

    def add_sunflower_planted(self):
        """记录向日葵种植（用于触发第一只僵尸）"""
        self.planted_sunflowers += 1

    def get_progress(self):
        """返回总体进度（0~1），基于关卡总僵尸数"""
        if self.total_zombies <= 0:
            return 0.0
        progress = self.killed_count / self.total_zombies / 2
        return max(0.0, min(1.0, progress))

    def is_all_spawned_and_dead(self, alive_zombies_count):
        """判断是否胜利：所有僵尸已生成且场上无存活僵尸"""
        return self.current_wave_index >= len(self.waves) and alive_zombies_count == 0

    def zombie_killed(self):
        """外部调用：僵尸死亡时增加消灭计数"""
        self.killed_count += 1

    def _build_spawn_queue(self):
        """根据当前波次的 type_dict 构建随机顺序的生成队列"""
        type_dict, _ = self._get_current_wave_info()
        queue = []
        for ztype, count in type_dict.items():
            queue.extend([ztype] * count)
        random.shuffle(queue)
        self.spawn_queue = deque(queue)

    def _get_current_spawn_interval(self):
        """返回当前波次对应的生成间隔（毫秒）"""
        if self.current_wave_index < len(self.wave_intervals):
            return self.wave_intervals[self.current_wave_index]
        # 如果已超出（游戏结束），返回最后一个波次的间隔作为默认
        return self.wave_intervals[-1] if self.wave_intervals else 5000


    def update(self, now,alive_zombies_count, triggered_mower_rows=None):
        # ----- 第一只僵尸触发判定 -----
        if not self.first_zombie_spawned:
            if self.planted_sunflowers >= 3 or now - self.game_start_time >= self.first_spawn_time:
                self.first_zombie_spawned = True
                self.last_spawn_time = now

                return self._spawn_first_zombie(now)
            return []

        # ----- 延迟检查（旗帜波延迟） -----
        if self.next_wave_delay_until > now and alive_zombies_count > 0:
            return []  # 延迟中，不生成僵尸
        if self.next_wave_delay_until != 0 and now >= self.next_wave_delay_until:
            self.next_wave_delay_until = 0
            self.next_wave_is_flag = False

        # ----- 波次处理 -----
        if self.current_wave_index >= len(self.waves):
            return []

        type_dict, is_flag_wave = self._get_current_wave_info()
        wave_count = sum(type_dict.values())

        # 新波次初始化
        if self.spawned_in_wave == 0:
            self._calculate_row_limits()
            self._build_spawn_queue()          # 构建本波僵尸类型队列
            self.followers_to_spawn = 0
            self.followers_spawned_in_wave = 0

        # 当前波次已生成完成，准备进入下一波
        if self.spawned_in_wave >= wave_count:
            next_idx = self.current_wave_index + 1
            if next_idx < len(self.waves):
                next_type_dict, next_flag = self.waves[next_idx]
                # 先进入下一波
                self.current_wave_index = next_idx
                self.spawned_in_wave = 0
                self.followers_to_spawn = 0
                self.followers_spawned_in_wave = 0

                if next_flag:
                    if alive_zombies_count > 0:
                        self.next_wave_delay_until = now + 2000
                        self.next_wave_is_flag = True
                        print(f"[下一波旗帜波] 延迟2秒后进入波次 {next_idx}")
                        return []
                    else:
                        # 直接开始新波次
                        type_dict, is_flag_wave = self._get_current_wave_info()
                        self._calculate_row_limits()
                        self._build_spawn_queue()
                        # 继续执行后续生成逻辑（本帧可能立即生成僵尸）
                else:
                    # 普通波：直接开始
                    type_dict, is_flag_wave = self._get_current_wave_info()
                    self._calculate_row_limits()
                    self._build_spawn_queue()
            else:
                self.current_wave_index += 1  # 使其等于 len(waves)
                return []

        # ----- 正常生成逻辑 -----
        zombies_to_spawn = []

        # 跟随僵尸优先处理（来自旗帜波）
        if self.followers_to_spawn > 0:
            while self.followers_to_spawn > 0 and len(zombies_to_spawn) < 3:
                row, emergency = self._choose_row(now)
                if row is not None:
                    if emergency:
                        self.emergency_spawn_count_this_wave += 1
                    if self.spawn_queue:
                        ztype = self.spawn_queue.popleft()
                    else:
                        break  # 队列为空，不应该发生
                    zombies_to_spawn.append((row, ztype))
                    self.followers_to_spawn -= 1
                    self.spawned_in_wave += 1
                    self.total_spawned += 1
                    self.last_spawn_time = now
                    self.last_spawn_time_per_row[row] = now
                    self.row_spawned_this_wave[row] += 1
                else:
                    break
            if zombies_to_spawn:
                return zombies_to_spawn

        # 正常生成间隔检查
        if alive_zombies_count > 0 and now - self.last_spawn_time < self._get_current_spawn_interval():
            return []

        # 旗帜僵尸处理（波次的第一只，且是旗帜波）
        is_first_of_wave = (self.spawned_in_wave == 0)
        if is_first_of_wave and is_flag_wave:
            row, emergency = self._choose_row(now)
            if row is not None:
                zombies_to_spawn.append((row, 'flag'))   # 旗帜僵尸特殊类型
                self.spawned_in_wave += 1
                self.total_spawned += 1
                self.last_spawn_time = now
                self.last_spawn_time_per_row[row] = now
                self.row_spawned_this_wave[row] += 1

                remaining = wave_count - self.spawned_in_wave
                followers = random.randint(self.flag_followers_min, self.flag_followers_max)
                self.followers_to_spawn = min(followers, remaining)
                self.followers_spawned_in_wave = 0

                return zombies_to_spawn

        # 普通僵尸生成（从队列中取类型）
        row, emergency = self._choose_row(now)
        if row is not None:
            if self.spawn_queue:
                ztype = self.spawn_queue.popleft()
            else:
                # 队列为空但理论上还有剩余，强制结束本波
                print(f"[警告] 波次 {self.current_wave_index} 队列已空但仍有剩余，强制结束")
                self.spawned_in_wave = wave_count
                return []

            zombies_to_spawn.append((row, ztype))
            self.spawned_in_wave += 1
            self.total_spawned += 1
            self.last_spawn_time = now
            self.last_spawn_time_per_row[row] = now
            self.row_spawned_this_wave[row] += 1

        # 强制结束检测（无可用行）
        if self.spawned_in_wave < wave_count:
            test_row, _ = self._choose_row(now)
            if test_row is None:
                self.spawned_in_wave = wave_count
                print(f"[波次强制结束] 波次 {self.current_wave_index} 因无可用行")
                return []

        return zombies_to_spawn

    # ---------- 内部辅助方法 ----------
    def _spawn_first_zombie(self, now):
        """生成第一只僵尸（从当前波次队列中弹出）"""
        # 确保当前波次索引有效
        if self.current_wave_index >= len(self.waves):
            return []

        # 获取当前波次信息
        type_dict, is_flag_wave = self._get_current_wave_info()
        wave_count = sum(type_dict.values())

        # 如果队列为空，说明波次尚未初始化，先计算行上限并构建队列
        if not self.spawn_queue:
            self._calculate_row_limits()
            self._build_spawn_queue()

        # 选择一行（优先使用 _choose_row，如果无可用行则随机）
        row, _ = self._choose_row(now)
        if row is None:
            row = random.randrange(self.rows)

        # 从队列中弹出第一只僵尸的类型
        if self.spawn_queue:
            first_type = self.spawn_queue.popleft()
        else:
            # 队列为空（理论上不应发生），回退到普通僵尸
            first_type = 'normal'

        # 更新计数
        self.spawned_in_wave += 1
        self.total_spawned += 1
        self.last_spawn_time_per_row[row] = now
        self.row_spawned_this_wave[row] += 1

        return [(row, first_type)]