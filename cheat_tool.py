import tkinter as tk
from tkinter import messagebox
import json
import os
import random
import pygame  # 用于播放音乐

CONFIG_FILE = "cheat.json"
MUSIC_FILES = ["辞九门回忆.mp3", "唐人恋曲.mp3"]  # 音乐文件名（需与程序同一目录）

class CheatTool:
    def __init__(self, root):
        self.root = root
        root.title("植物大战僵尸 外挂设置")
        root.geometry("500x480")  # 增加高度容纳新控件
        root.resizable(False, False)
        default_font = ("微软雅黑", 12)
        root.option_add("*Font", default_font)
        # 初始化 pygame 混音器（仅音频）
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"音频初始化失败: {e}")

        # 随机选择一首歌并循环播放
        self.play_music()

        self.config = self.load_config()

        # 复选框变量
        self.sun_infinite = tk.BooleanVar(value=self.config.get("sun_infinite", False))
        self.sun_never_decrease = tk.BooleanVar(value=self.config.get("sun_never_decrease", False))
        self.sun_unlimited = tk.BooleanVar(value=self.config.get("sun_unlimited", False))
        self.overlap_plant = tk.BooleanVar(value=self.config.get("overlap_plant", False))
        self.auto_collect_sun = tk.BooleanVar(value=self.config.get("auto_collect_sun", False))
        self.no_cooldown = tk.BooleanVar(value=self.config.get("no_cooldown", False))
        self.pause_spawn = tk.BooleanVar(value=self.config.get("pause_spawn", False))  # 新增

        # 布局
        tk.Checkbutton(root, text="阳光无限 (始终9999)", variable=self.sun_infinite).pack(anchor='w', padx=20, pady=5)
        tk.Checkbutton(root, text="不减阳光 (阳光只增不减)", variable=self.sun_never_decrease).pack(anchor='w', padx=20, pady=5)
        tk.Checkbutton(root, text="取消阳光上限 (可超过9999)", variable=self.sun_unlimited).pack(anchor='w', padx=20, pady=5)
        tk.Checkbutton(root, text="随意种植 (可重叠植物)", variable=self.overlap_plant).pack(anchor='w', padx=20, pady=5)
        tk.Checkbutton(root, text="阳光自动收集", variable=self.auto_collect_sun).pack(anchor='w', padx=20, pady=5)
        tk.Checkbutton(root, text="取消植物冷却", variable=self.no_cooldown).pack(anchor='w', padx=20, pady=5)
        tk.Checkbutton(root, text="暂停出怪", variable=self.pause_spawn).pack(anchor='w', padx=20, pady=5)  # 新增

        custom_frame = tk.Frame(root)
        custom_frame.pack(pady=5)
        tk.Label(custom_frame, text="自定义阳光数量:").pack(side='left', padx=5)
        self.custom_sun_var = tk.StringVar()
        # 加载配置中的 custom_sun 作为初始值（如果有）
        self.custom_sun_var.set(str(self.config.get("custom_sun", "1000")))
        tk.Entry(custom_frame, textvariable=self.custom_sun_var, width=10).pack(side='left', padx=5)
        tk.Button(custom_frame, text="设置阳光", command=self.set_custom_sun).pack(side='left', padx=5)

        # 按钮框架（第一行）
        btn_frame1 = tk.Frame(root)
        btn_frame1.pack(pady=5)

        tk.Button(btn_frame1, text="立即恢复小推车", command=self.restore_mowers, width=15).pack(side='left', padx=5)
        tk.Button(btn_frame1, text="别唱了", command=self.stop_music, width=10).pack(side='left', padx=5)

        # 按钮框架（第二行）
        btn_frame2 = tk.Frame(root)
        btn_frame2.pack(pady=5)

        tk.Button(btn_frame2, text="立即清除僵尸", command=self.kill_all_zombies, width=15).pack(side='left', padx=5)
        tk.Button(btn_frame2, text="清除配置", command=self.clear_config, width=10).pack(side='left', padx=5)

        tk.Button(root, text="保存设置", command=self.save_config).pack(pady=5)
        tk.Button(root, text="退出", command=self.on_close).pack()


        # 原有按钮框架（第一行）
        btn_frame1 = tk.Frame(root)
        btn_frame1.pack(pady=5)

        if "custom_sun" not in self.config:
            self.config["custom_sun"] = 100
        self.custom_sun_var.set(str(self.config["custom_sun"]))
    def set_custom_sun(self):
        """设置自定义阳光数量（触发型）"""
        try:
            value = int(self.custom_sun_var.get())
            if value <= 50:
                value=50
                # messagebox.showerror("错误", "请输入正整数")
                return
        except ValueError:
            # messagebox.showerror("错误", "请输入有效数字")
            return

        config = self.load_config()
        config["set_sun_amount"] = True
        config["custom_sun"] = value
        # 如果未开启阳光上限，可在此限制（但游戏内会处理，也可不限制）
        if not config.get("sun_unlimited", False):
            if value > 9999:
                value=9999
                # messagebox.showwarning("提示", "未开启「取消阳光上限」，数值将被限制为9999")
        try:
            with open(CONFIG_FILE, "w", encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            # messagebox.showinfo("成功", f"阳光已设置为 {value}")
        except Exception as e:
            # messagebox.showerror("错误", f"保存失败: {e}")
            pass



    def play_music(self):
        """随机选择一首音乐并循环播放"""
        available_music = [f for f in MUSIC_FILES if os.path.exists(f)]
        if not available_music:
            print("未找到音乐文件，跳过播放")
            return
        chosen = random.choice(available_music)
        try:
            pygame.mixer.music.load(chosen)
            pygame.mixer.music.play(-1)  # -1 表示无限循环
            print(f"正在播放: {chosen}")
        except Exception as e:
            print(f"播放音乐失败: {e}")

    def stop_music(self):
        """停止音乐"""
        try:
            pygame.mixer.music.stop()
            print("音乐已停止")
        except Exception as e:
            print(f"停止音乐失败: {e}")

    def on_close(self):
        """窗口关闭时停止音乐并退出"""
        self.stop_music()
        self.root.quit()

    def load_config(self):
        try:
            with open(CONFIG_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"加载配置失败: {e}")
            return {}

    def save_config(self):
        config = {
            "sun_infinite": self.sun_infinite.get(),
            "sun_never_decrease": self.sun_never_decrease.get(),
            "sun_unlimited": self.sun_unlimited.get(),
            "overlap_plant": self.overlap_plant.get(),
            "auto_collect_sun": self.auto_collect_sun.get(),
            "no_cooldown": self.no_cooldown.get(),
            "pause_spawn": self.pause_spawn.get(),      # 新增
            "restore_mowers": False,
            "kill_all_zombies": False ,                   # 新增，由按钮单独触发
            "set_sun_amount": False,  # 新增
            "custom_sun": int(self.custom_sun_var.get())  # 保存输入框的值
        }
        try:
            with open(CONFIG_FILE, "w", encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")

    def restore_mowers(self):
        """触发小推车恢复"""
        config = self.load_config()
        config["restore_mowers"] = True
        try:
            with open(CONFIG_FILE, "w", encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            messagebox.showerror("错误", f"发送失败: {e}")

    def kill_all_zombies(self):
        """触发清除草坪内僵尸"""
        config = self.load_config()
        config["kill_all_zombies"] = True
        try:
            with open(CONFIG_FILE, "w", encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            messagebox.showerror("错误", f"发送失败: {e}")

    def clear_config(self):
        """删除配置文件，恢复默认"""
        if os.path.exists(CONFIG_FILE):
            try:
                os.remove(CONFIG_FILE)
                self.sun_infinite.set(False)
                self.sun_never_decrease.set(False)
                self.sun_unlimited.set(False)
                self.overlap_plant.set(False)
                self.auto_collect_sun.set(False)
                self.no_cooldown.set(False)
                self.pause_spawn.set(False)  # 新增
                self.custom_sun_var.set("100")  # 重置输入框
                # 不弹出提示
            except Exception as e:
                messagebox.showerror("错误", f"清除失败: {e}")
        else:
            messagebox.showinfo("提示", "配置文件不存在")

if __name__ == "__main__":
    root = tk.Tk()
    app = CheatTool(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()