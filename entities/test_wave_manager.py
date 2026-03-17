# test_wave_manager.py
import random
from entities.wave_manager import WaveManager

def print_zombie(zombies, tag=""):
    """格式化打印生成的僵尸列表"""
    if zombies:
        print(f"{tag} 生成: {', '.join([f'行{r}/{t}' for r,t in zombies])}")
    else:
        print(f"{tag} 未生成")

def test_first_spawn():
    print("\n=== 测试第一只僵尸触发 ===")
    wm = WaveManager(total_zombies=30, waves=[5,7,8], spawn_interval=500, first_spawn_time=3000, rows=5)
    start = 1000
    wm.reset(start)
    now = start

    # 情况1：种植向日葵触发
    print("--- 种3向日葵触发 ---")
    wm.add_sunflower_planted()
    wm.add_sunflower_planted()
    wm.add_sunflower_planted()
    zombies = wm.update(now)
    print_zombie(zombies, "种3后立即调用")
    assert zombies and zombies[0][1]=='normal', "向日葵触发失败"

    # 情况2：兜底触发（重置后不种向日葵，30秒后）
    print("--- 兜底30秒触发 ---")
    wm.reset(start)
    now = start
    spawned = False
    target = start + 3000
    while now <= target + 500:
        zombies = wm.update(now)
        if zombies:
            print_zombie(zombies, f"时间 {now}")
            spawned = True
            break
        now += 500
    assert spawned, f"30秒内未生成僵尸（兜底触发失败），最后时间 {now}"

def test_spawn_interval():
    print("\n=== 测试生成间隔 ===")
    wm = WaveManager(total_zombies=30, waves=[5,7,8], spawn_interval=500, first_spawn_time=3000, rows=5)
    start = 1000
    wm.reset(start)
    wm.first_zombie_spawned = True  # 跳过第一只判定
    wm.last_spawn_time = start
    wm.spawned_in_wave = 1          # 模拟第一波已生成1只
    wm.total_spawned = 1

    # 初始化行上限
    wm._calculate_row_limits()
    wm.row_spawned_this_wave[0] = 1

    now = start + 300  # 间隔300 < 500，应不生成
    zombies = wm.update(now)
    print_zombie(zombies, f"时间 {now} (间隔300)")
    assert not zombies, f"间隔300不应生成，但生成了 {zombies}"

    now = start + 600  # 间隔600 > 500，应生成
    zombies = wm.update(now)
    print_zombie(zombies, f"时间 {now} (间隔600)")
    assert zombies, f"间隔600应生成，但未生成"

def test_row_distribution():
    print("\n=== 测试行分布与冷却 ===")
    wm = WaveManager(total_zombies=30, waves=[10], spawn_interval=200, first_spawn_time=3000, rows=5)
    start = 1000
    wm.reset(start)
    wm.first_zombie_spawned = True
    wm.last_spawn_time = start
    # 手动设置行上限（全5行可用，基准每行2，上限3）
    wm.row_max_spawn_this_wave = {i:3 for i in range(5)}
    wm.row_spawned_this_wave = {i:0 for i in range(5)}

    now = start
    spawn_counts = {i:0 for i in range(5)}
    for _ in range(15):  # 生成15只，应覆盖所有行
        now += 250
        zombies = wm.update(now)
        if zombies:
            row, typ = zombies[0]
            spawn_counts[row] += 1
            print_zombie(zombies, f"时间 {now}")
    print("各行生成数量:", spawn_counts)
    # 检查：所有行都应该有生成，且每行不超过3
    for row, cnt in spawn_counts.items():
        assert cnt <= 3, f"行{row}生成{cnt}次，超过上限3"
        assert cnt > 0, f"行{row}从未生成"

def test_protection_mechanism():
    print("\n=== 测试保护机制与单行上限 ===")
    wm = WaveManager(total_zombies=30, waves=[10], spawn_interval=200, first_spawn_time=3000, rows=5, emergency_multiplier=1.5)
    start = 1000
    wm.reset(start)
    wm.first_zombie_spawned = True
    wm.last_spawn_time = start
    # 保护第0行和第1行
    wm.protect_row(0, 0)  # 保护到波次2
    wm.protect_row(1, 0)
    wm._calculate_row_limits()  # 手动计算上限

    # 检查上限：可用行应为2,3,4，基准=ceil(10/3)=4，上限=4*1.5=6
    print("行上限:", wm.row_max_spawn_this_wave)
    assert wm.row_max_spawn_this_wave[0]==0 and wm.row_max_spawn_this_wave[1]==0, "保护行上限应为0"
    assert all(wm.row_max_spawn_this_wave[i]==6 for i in [2,3,4]), "可用行上限应为6"

    # 模拟生成，看是否始终避开0,1行，且单行不超过6
    now = start
    spawn_counts = {i:0 for i in range(5)}
    for _ in range(10):  # 生成全部10只
        now += 250
        zombies = wm.update(now)
        if zombies:
            row, typ = zombies[0]
            spawn_counts[row] += 1
            print_zombie(zombies, f"时间 {now}")
    print("各行生成数量:", spawn_counts)
    assert spawn_counts[0]==0 and spawn_counts[1]==0, "保护行生成了僵尸"
    assert sum(spawn_counts.values()) == 10, "总生成数应为10"
    for row in [2,3,4]:
        assert spawn_counts[row] <= 6, f"行{row}生成{spawn_counts[row]}，超过上限6"

def test_all_protected_emergency():
    print("\n=== 测试所有行保护时的紧急模式 ===")
    wm = WaveManager(total_zombies=30, waves=[10], spawn_interval=200, first_spawn_time=3000, rows=5, emergency_multiplier=1.5)
    start = 1000
    wm.reset(start)
    wm.first_zombie_spawned = True
    wm.last_spawn_time = start
    # 保护所有行
    for r in range(5):
        wm.protect_row(r, 0)
    wm._calculate_row_limits()
    # 所有行都应可用，且上限相同（基准=ceil(10/5)=2，上限=3）
    print("行上限:", wm.row_max_spawn_this_wave)
    assert all(wm.row_max_spawn_this_wave[r]==3 for r in range(5)), "紧急模式下每行上限应为3"

    now = start
    spawn_counts = {i:0 for i in range(5)}
    for _ in range(10):
        now += 250
        zombies = wm.update(now)
        if zombies:
            row, typ = zombies[0]
            spawn_counts[row] += 1
            print_zombie(zombies, f"时间 {now}")
    print("各行生成数量:", spawn_counts)
    assert sum(spawn_counts.values()) == 10, "总生成数应为10"
    for row in range(5):
        assert spawn_counts[row] <= 3, f"行{row}生成{spawn_counts[row]}，超过上限3"

def test_flag_followers():
    print("\n=== 测试旗帜僵尸跟随生成 ===")
    wm = WaveManager(total_zombies=30, waves=[(8, True), 7, 5], spawn_interval=500, first_spawn_time=3000, rows=5,
                     flag_followers_min=4, flag_followers_max=6)
    start = 1000
    wm.reset(start)
    wm.first_zombie_spawned = True
    wm.last_spawn_time = start
    wm._calculate_row_limits()

    now = start + 600  # 确保间隔满足
    # 第一次调用，应生成旗帜僵尸
    zombies = wm.update(now)
    print_zombie(zombies, "第1帧")
    assert zombies and zombies[0][1]=='flag', "应生成旗帜僵尸"

    # 紧接着的几帧，应连续生成跟随僵尸（忽略间隔）
    followers = []
    for i in range(6):  # 最多6次
        now += 1
        zombies = wm.update(now)
        if zombies:
            for z in zombies:
                print_zombie([z], f"第{i+2}帧")
                followers.append(z[1])
        else:
            break
    print(f"跟随僵尸数量: {len(followers)}")
    assert 4 <= len(followers) <= 6, f"跟随僵尸数量应为4-6，实际{len(followers)}"
    assert all(t=='normal' for t in followers), "跟随僵尸类型应为 normal"
    assert wm.spawned_in_wave == 1 + len(followers), "波次内生成计数错误"

def test_mid_wave_recalc():
    print("\n=== 测试波次中间重新计算上限（保护触发后分配） ===")
    wm = WaveManager(total_zombies=30, waves=[10], spawn_interval=200, first_spawn_time=3000, rows=5, emergency_multiplier=1.5)
    start = 1000
    wm.reset(start)
    wm.first_zombie_spawned = True
    wm.last_spawn_time = start
    wm._calculate_row_limits()  # 初始上限

    # 模拟已经生成了5只僵尸（分布在多行）
    wm.spawned_in_wave = 5
    wm.total_spawned = 5
    wm.row_spawned_this_wave[0] = 2
    wm.row_spawned_this_wave[1] = 2
    wm.row_spawned_this_wave[2] = 1
    # 保护行0
    wm.protect_row(0, wm.current_wave_index)  # 会触发重新计算
    # 重新计算后，可用行应为1,2,3,4，剩余5只，基准=ceil(5/4)=2，上限=3，总容量=12
    print("重新计算后上限:", wm.row_max_spawn_this_wave)
    assert wm.row_max_spawn_this_wave[0] == 0
    for r in [1,2,3,4]:
        assert wm.row_max_spawn_this_wave[r] == 3
    # 检查已生成数未变
    assert wm.row_spawned_this_wave[0] == 2
    assert wm.row_spawned_this_wave[1] == 2

def test_progress_and_victory():
    print("\n=== 测试进度条和胜利判定 ===")
    wm = WaveManager(total_zombies=10, waves=[5,5], spawn_interval=200, first_spawn_time=3000, rows=5)
    start = 1000
    wm.reset(start)
    wm.first_zombie_spawned = True
    wm.last_spawn_time = start

    # 初始进度为0
    assert wm.get_progress() == 0, "初始进度应为0"

    # 模拟生成5只僵尸，但尚未消灭
    now = start
    for i in range(5):
        now += 250
        zombies = wm.update(now)
    # 进度仍为0（基于消灭）
    assert wm.get_progress() == 0, "生成但未消灭，进度应为0"

    # 消灭2只
    for _ in range(2):
        wm.zombie_killed()
    assert wm.get_progress() == 2/5, f"消灭2只，进度应为0.4，实际{wm.get_progress()}"

    # 继续生成剩余5只僵尸（第二波）
    for i in range(5):
        now += 250
        zombies = wm.update(now)
    # 此时所有僵尸已生成，但波次可能未标记为完成，需要一次额外的update来触发波次切换
    wm.update(now)  # 触发波次结束，current_wave_index 变为2

    # 消灭5只（第二波生成的）
    for _ in range(5):
        wm.zombie_killed()
    # 此时总生成10只，消灭7只，进度应为0.7
    assert wm.get_progress() == 0.7, f"消灭7只，进度应为0.7，实际{wm.get_progress()}"

    # 消灭最后3只
    for _ in range(3):
        wm.zombie_killed()
    assert wm.get_progress() == 1.0, "全部消灭，进度应为1.0"

    # 胜利条件：所有波次结束且无存活
    assert wm.current_wave_index == len(wm.waves), "波次应已全部完成"
    assert wm.is_all_spawned_and_dead(0) == True, "胜利条件应满足"
    assert wm.is_all_spawned_and_dead(1) == False, "还有存活僵尸不应胜利"

if __name__ == "__main__":
    test_first_spawn()
    test_spawn_interval()
    test_row_distribution()
    test_protection_mechanism()
    test_all_protected_emergency()
    test_flag_followers()
    test_mid_wave_recalc()
    test_progress_and_victory()
    print("\n所有测试完成！")