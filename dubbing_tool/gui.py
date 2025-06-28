import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, ttk
from .script_parser import parse_script
from .api_client import ApiClient
from .utils import sanitize_filename
import os
from threading import Thread
from playsound import playsound

class App(ctk.CTk):
    def __init__(self, api_client, character_mapping, output_dir):
        super().__init__()

        self.api_client = api_client
        self.character_mapping = character_mapping
        self.output_dir = output_dir

        self.title("GPT-SoVITS 配音工具")
        self.geometry("1200x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # ---- UI布局 ----
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 左侧框架 (树状视图)
        self.left_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.left_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.left_frame.grid_rowconfigure(1, weight=1)
        
        self.open_button = ctk.CTkButton(self.left_frame, text="打开剧本 (YAML)", command=self.open_script)
        self.open_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.tree = ttk.Treeview(self.left_frame, show="tree headings")
        self.tree.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # 右侧主框架
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # ... (右侧内容将在选择条目后填充)

        # 底部状态栏
        self.status_bar = ctk.CTkLabel(self, text="准备就绪", anchor="w")
        self.status_bar.grid(row=1, column=1, rowspan=2, padx=10, pady=5, sticky="ew")

        self.script_data = None
        self.current_dialogue_info = None

    def open_script(self):
        file_path = filedialog.askopenfilename(
            title="选择 YAML 剧本文件",
            filetypes=(("YAML files", "*.yaml"), ("All files", "*.*"))
        )
        if not file_path:
            return

        self.script_data = parse_script(file_path)
        if not self.script_data:
            self.status_bar.configure(text=f"错误: 无法解析剧本 {os.path.basename(file_path)}")
            return
        
        self.populate_tree()
        self.status_bar.configure(text=f"已加载剧本: {self.script_data.get('script_name', '无标题')}")

    def populate_tree(self):
        # 清空现有内容
        for item in self.tree.get_children():
            self.tree.delete(item)

        for scene_idx, scene in enumerate(self.script_data.get("scenes", [])):
            scene_id = self.tree.insert("", "end", f"scene_{scene_idx}", text=scene.get("scene_name", "未命名章节"))
            for dialogue_idx, dialogue in enumerate(scene.get("dialogues", [])):
                dialogue_text = f"{dialogue.get('character', '?')}: {dialogue.get('text', '')[:20]}..."
                self.tree.insert(scene_id, "end", f"dialogue_{scene_idx}_{dialogue_idx}", text=dialogue_text)

    def on_tree_select(self, event):
        selected_id = self.tree.selection()
        if not selected_id or not selected_id[0].startswith("dialogue_"):
            self.clear_main_frame()
            self.current_dialogue_info = None
            return

        # 解析ID获取对话信息
        _, scene_idx, dialogue_idx = selected_id[0].split('_')
        scene_idx, dialogue_idx = int(scene_idx), int(dialogue_idx)
        
        dialogue = self.script_data["scenes"][scene_idx]["dialogues"][dialogue_idx]
        scene_name = self.script_data["scenes"][scene_idx]["scene_name"]
        
        self.current_dialogue_info = {
            "scene_idx": scene_idx,
            "dialogue_idx": dialogue_idx,
            "scene_name": scene_name,
            **dialogue
        }
        
        self.display_dialogue_details()

    def display_dialogue_details(self):
        self.clear_main_frame()
        if not self.current_dialogue_info:
            return

        info = self.current_dialogue_info
        
        # 角色
        ctk.CTkLabel(self.main_frame, text="角色:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=10, pady=(10,0), sticky="w")
        self.char_label = ctk.CTkLabel(self.main_frame, text=info.get("character", "N/A"), font=ctk.CTkFont(size=14))
        self.char_label.grid(row=0, column=1, padx=10, pady=(10,0), sticky="w")

        # 文本
        ctk.CTkLabel(self.main_frame, text="文本:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=1, column=0, padx=10, pady=(10,0), sticky="w")
        self.text_box = ctk.CTkTextbox(self.main_frame, height=150)
        self.text_box.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        self.text_box.insert("1.0", info.get("text", ""))
        self.text_box.configure(state="disabled") # 默认不可编辑
        
        # 情感
        ctk.CTkLabel(self.main_frame, text="情感:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=3, column=0, padx=10, pady=(10,0), sticky="w")
        self.emotion_var = ctk.StringVar(value=info.get("emotion", "默认"))
        self.emotion_entry = ctk.CTkEntry(self.main_frame, textvariable=self.emotion_var)
        self.emotion_entry.grid(row=3, column=1, padx=10, pady=(10,0), sticky="ew")

        # 控制按钮
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        self.generate_button = ctk.CTkButton(self.button_frame, text="生成音频", command=self.generate_audio)
        self.generate_button.pack(side="left", padx=10)
        
        self.play_button = ctk.CTkButton(self.button_frame, text="播放音频", command=self.play_audio, state="disabled")
        self.play_button.pack(side="left", padx=10)
        
        self.update_play_button_state()
        
    def get_output_path(self):
        if not self.current_dialogue_info:
            return None
        info = self.current_dialogue_info
        scene_dir = os.path.join(self.output_dir, sanitize_filename(info['scene_name']))
        filename_preview = sanitize_filename(info['text'])
        line_num = info['scene_idx'] * 1000 + info['dialogue_idx'] # 简易唯一ID
        filename = f"{line_num:04d}_{info['character']}_{filename_preview}.wav"
        return os.path.join(scene_dir, filename)

    def generate_audio(self):
        if not self.current_dialogue_info:
            return

        self.status_bar.configure(text="正在生成音频...")
        self.generate_button.configure(state="disabled")

        info = self.current_dialogue_info
        character = info['character']
        text = self.text_box.get("1.0", "end-1c") # 获取当前文本框内容以支持临时修改
        emotion = self.emotion_var.get()
        
        voice = self.character_mapping.get(character)
        if not voice:
            self.status_bar.configure(text=f"错误: 未找到角色 '{character}' 的配置。")
            self.generate_button.configure(state="normal")
            return
        
        output_path = self.get_output_path()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        def task():
            audio_data = self.api_client.generate_audio(
                text=text,
                voice=voice,
                other_params={"emotion": emotion}
            )
            if audio_data:
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                self.status_bar.configure(text=f"音频已保存至: {os.path.basename(output_path)}")
                self.update_play_button_state()
            else:
                self.status_bar.configure(text="错误: API 调用失败。")
            
            self.generate_button.configure(state="normal")
        
        Thread(target=task, daemon=True).start()

    def play_audio(self):
        output_path = self.get_output_path()
        if not output_path or not os.path.exists(output_path):
            self.status_bar.configure(text="错误: 音频文件不存在。")
            return

        def task():
            self.status_bar.configure(text="正在播放...")
            self.play_button.configure(state="disabled")
            try:
                playsound(output_path)
                self.status_bar.configure(text="播放完毕。")
            except Exception as e:
                self.status_bar.configure(text=f"错误: 无法播放音频: {e}")
            self.play_button.configure(state="normal")

        Thread(target=task, daemon=True).start()

    def update_play_button_state(self):
        output_path = self.get_output_path()
        if output_path and os.path.exists(output_path):
            self.play_button.configure(state="normal")
        else:
            self.play_button.configure(state="disabled")

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy() 