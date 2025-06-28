import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, ttk, TclError
import json
from .script_parser import parse_script
from .api_client import ApiClient
from .utils import sanitize_filename
import os
from threading import Thread
import winsound

class App(ctk.CTk):
    def __init__(self, api_client, output_dir):
        super().__init__()

        self.api_client = api_client
        self.output_dir = output_dir
        self.script_character_mapping = {}

        self.title("GPT-SoVITS 配音工具")
        self.geometry("1200x900")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- 状态变量 ---
        self.script_data = None
        self.current_dialogue_info = None
        self.overview_widgets = {}

        # ---- UI布局 ----
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 左侧框架
        self.left_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.left_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.left_frame.grid_rowconfigure(2, weight=1)
        
        self.open_button = ctk.CTkButton(self.left_frame, text="打开剧本 (YAML)", command=self.open_script)
        self.open_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.batch_generate_button = ctk.CTkButton(self.left_frame, text="批量生成缺失音频", command=self.batch_generate, state="disabled")
        self.batch_generate_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.tree = ttk.Treeview(self.left_frame, show="tree headings")
        self.tree.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # 右侧主框架 (Tab视图)
        self.main_tab_view = ctk.CTkTabview(self, anchor="w")
        self.main_tab_view.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.overview_tab = self.main_tab_view.add("总览")
        self.details_tab = self.main_tab_view.add("详情编辑")
        self.settings_tab = self.main_tab_view.add("全局设置")
        self.main_tab_view.set("总览")

        # --- 总览页面 ---
        # 固定的剧本信息区域（不滚动）
        self.overview_info_frame = ctk.CTkFrame(self.overview_tab)
        self.overview_info_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        # 可滚动的对话列表区域
        self.overview_scroll_frame = ctk.CTkScrollableFrame(self.overview_tab)
        self.overview_scroll_frame.pack(fill="both", expand=True, padx=5, pady=(5, 5))
        ctk.CTkLabel(self.overview_scroll_frame, text="请先从左侧打开一个剧本文件。").pack(pady=20)
        
        # --- 详情页面 ---
        self.details_frame = ctk.CTkFrame(self.details_tab)
        self.details_frame.pack(fill="both", expand=True)
        self.details_frame.grid_columnconfigure(0, minsize=80) # 固定标签列宽度防抖动
        self.details_frame.grid_columnconfigure(1, weight=1)
        
        # --- 全局设置页面 ---
        self.settings_frame = ctk.CTkScrollableFrame(self.settings_tab)
        self.settings_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.settings_frame.grid_columnconfigure(1, weight=1)
        self.create_settings_page()
        
        # 底部状态栏
        self.status_bar = ctk.CTkLabel(self, text="准备就绪", anchor="w")
        self.status_bar.grid(row=1, column=1, rowspan=2, padx=10, pady=5, sticky="ew")

    def open_script(self):
        winsound.PlaySound(None, winsound.SND_PURGE)
        file_path = filedialog.askopenfilename(
            title="选择 YAML 剧本文件",
            filetypes=(("YAML files", "*.yaml"), ("All files", "*.*"))
        )
        if not file_path: return

        self.script_data = parse_script(file_path)
        if not self.script_data:
            self.status_bar.configure(text=f"错误: 无法解析剧本 {os.path.basename(file_path)}")
            return
        
        self.script_character_mapping = self.script_data.get('character_models', {})
        self.populate_tree()
        self.populate_overview_page()
        self.batch_generate_button.configure(state="normal")
        self.status_bar.configure(text=f"已加载剧本: {self.script_data.get('script_name', '无标题')}")

    def populate_tree(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for scene_idx, scene in enumerate(self.script_data.get("scenes", [])):
            scene_id = self.tree.insert("", "end", f"scene_{scene_idx}", text=scene.get("scene_name", "未命名章节"))
            for dialogue_idx, dialogue in enumerate(scene.get("dialogues", [])):
                dialogue_text = f"{dialogue.get('character', '?')}: {dialogue.get('text', '')[:20]}..."
                self.tree.insert(scene_id, "end", f"dialogue_{scene_idx}_{dialogue_idx}", text=dialogue_text)

    def populate_overview_page(self):
        # 清空固定信息区域
        for widget in self.overview_info_frame.winfo_children(): 
            widget.destroy()
        
        # 清空滚动区域
        for widget in self.overview_scroll_frame.winfo_children(): 
            widget.destroy()
        self.overview_widgets.clear()

        # 剧本信息区域（固定在顶部）
        self.overview_info_frame.grid_columnconfigure(1, weight=1)
        
        # 剧本标题
        script_name = self.script_data.get('script_name', '未命名剧本')
        ctk.CTkLabel(self.overview_info_frame, text=f"剧本: {script_name}", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # 演员映射信息
        ctk.CTkLabel(self.overview_info_frame, text="演员映射:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=1, column=0, padx=10, pady=2, sticky="w")
        
        # 获取剧本内角色映射
        if self.script_character_mapping:
            mapping_text = " | ".join([f"{char}: {model}" for char, model in self.script_character_mapping.items()])
        else:
            mapping_text = "未配置"
        
        mapping_label = ctk.CTkLabel(self.overview_info_frame, text=mapping_text, wraplength=800)
        mapping_label.grid(row=1, column=1, padx=10, pady=2, sticky="w")
        
        # 提示信息
        ctk.CTkLabel(self.overview_info_frame, text="提示: 剧本信息请到配置文件中修改", 
                    font=ctk.CTkFont(size=12), text_color="gray").grid(row=2, column=0, columnspan=2, padx=10, pady=2, sticky="w")

        # 对话列表区域（可滚动）
        list_frame = ctk.CTkFrame(self.overview_scroll_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 为总览页的表格布局设置列配置
        list_frame.grid_columnconfigure(0, minsize=140) # Scene
        list_frame.grid_columnconfigure(1, minsize=90)  # Character
        list_frame.grid_columnconfigure(2, minsize=70)  # Emotion
        list_frame.grid_columnconfigure(3, weight=1)    # Text
        list_frame.grid_columnconfigure(4, minsize=50)  # Status
        list_frame.grid_columnconfigure(5, minsize=65)  # Button
        list_frame.grid_columnconfigure(6, minsize=65)  # Button

        # 添加表头
        header_font = ctk.CTkFont(weight="bold")
        headers = ["场景", "角色", "情感", "对话", "状态"]
        for col, header_text in enumerate(headers):
            ctk.CTkLabel(list_frame, text=header_text, font=header_font).grid(row=0, column=col, sticky="w", padx=5)
        
        for i, dialogue_info in enumerate(self.get_all_dialogues()):
            dialogue_id = f"dialogue_{dialogue_info['scene_idx']}_{dialogue_info['dialogue_idx']}"
            
            ctk.CTkLabel(list_frame, text=dialogue_info['scene_name'], anchor="w").grid(row=i+1, column=0, sticky="ew", padx=5, pady=2)
            ctk.CTkLabel(list_frame, text=dialogue_info['character'], anchor="w").grid(row=i+1, column=1, sticky="ew", padx=5, pady=2)
            ctk.CTkLabel(list_frame, text=dialogue_info['emotion'], anchor="w").grid(row=i+1, column=2, sticky="ew", padx=5, pady=2)
            ctk.CTkLabel(list_frame, text=dialogue_info['text'], anchor="w", wraplength=350).grid(row=i+1, column=3, sticky="ew", padx=5, pady=2)

            output_path = self.get_output_path(dialogue_info)
            status, color = ("已生成", "green") if os.path.exists(output_path) else ("缺失", "red")
            
            status_label = ctk.CTkLabel(list_frame, text=status, width=40, text_color=color)
            status_label.grid(row=i+1, column=4, padx=5, pady=2)

            regen_button = ctk.CTkButton(list_frame, text="生成", width=60, command=lambda info=dialogue_info: self.perform_audio_generation(info))
            regen_button.grid(row=i+1, column=5, padx=5, pady=2)

            play_button = ctk.CTkButton(list_frame, text="播放", width=60, command=lambda p=output_path: self.perform_audio_play(p))
            if status == "缺失": play_button.configure(state="disabled")
            play_button.grid(row=i+1, column=6, padx=5, pady=2)
            
            self.overview_widgets[dialogue_id] = {'status_label': status_label, 'play_button': play_button}

    def on_tree_select(self, event):
        winsound.PlaySound(None, winsound.SND_PURGE)
        selected_id = self.tree.selection()
        if not selected_id or not selected_id[0].startswith("dialogue_"):
            self.clear_main_frame()
            self.current_dialogue_info = None
            return
        
        _, scene_idx, dialogue_idx = selected_id[0].split('_')
        dialogue = self.script_data["scenes"][int(scene_idx)]["dialogues"][int(dialogue_idx)]
        scene_name = self.script_data["scenes"][int(scene_idx)]["scene_name"]
        
        self.current_dialogue_info = {"scene_idx": int(scene_idx), "dialogue_idx": int(dialogue_idx), "scene_name": scene_name, **dialogue}
        self.display_dialogue_details()
        self.main_tab_view.set("详情编辑")

    def display_dialogue_details(self):
        self.clear_main_frame()
        if not self.current_dialogue_info: return

        info = self.current_dialogue_info
        character = info.get("character", "N/A")
        model_name = self.script_character_mapping.get(character)
        model_display = f"({model_name})" if model_name else "(未配置模型)"

        ctk.CTkLabel(self.details_frame, text="角色:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=10, pady=(10,0), sticky="w")
        ctk.CTkLabel(self.details_frame, text=f"{character} {model_display}", font=ctk.CTkFont(size=14)).grid(row=0, column=1, padx=10, pady=(10,0), sticky="w")

        ctk.CTkLabel(self.details_frame, text="文本:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=1, column=0, padx=10, pady=(10,0), sticky="w")
        self.text_box = ctk.CTkTextbox(self.details_frame, height=150)
        self.text_box.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        self.text_box.insert("1.0", info.get("text", ""))
        
        ctk.CTkLabel(self.details_frame, text="情感:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=3, column=0, padx=10, pady=(10,0), sticky="w")
        self.emotion_var = ctk.StringVar(value=info.get("emotion", "默认"))
        self.emotion_entry = ctk.CTkEntry(self.details_frame, textvariable=self.emotion_var)
        self.emotion_entry.grid(row=3, column=1, padx=10, pady=(10,0), sticky="ew")

        # 常用设置（始终显示）
        ctk.CTkLabel(self.details_frame, text="语速:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.speed_slider = ctk.CTkSlider(self.details_frame, from_=0.1, to=2.0, number_of_steps=19)
        self.speed_slider.set(self.api_client.default_params.get('speed_facter', 1.0))
        self.speed_slider.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.details_frame, text="随机种子:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.seed_var = ctk.StringVar(value=str(self.api_client.default_params.get('seed', -1)))
        self.seed_entry = ctk.CTkEntry(self.details_frame, textvariable=self.seed_var)
        self.seed_entry.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

        # 高级设置区域（可折叠）
        self.advanced_expanded = ctk.BooleanVar(value=False)
        self.advanced_toggle = ctk.CTkButton(self.details_frame, text="▶ 高级设置", 
                                           command=self.toggle_advanced_settings,
                                           font=ctk.CTkFont(size=14, weight="bold"))
        self.advanced_toggle.grid(row=6, column=0, columnspan=2, pady=(15, 5), sticky="w")
        
        # 高级设置容器
        self.advanced_frame = ctk.CTkFrame(self.details_frame)
        self.advanced_frame.grid(row=7, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.advanced_frame.grid_remove()  # 初始隐藏
        
        # 语言设置
        ctk.CTkLabel(self.advanced_frame, text="文本语言:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.text_lang_var = ctk.StringVar(value=self.api_client.default_params.get('text_lang', '中文'))
        self.text_lang_combo = ctk.CTkComboBox(self.advanced_frame, variable=self.text_lang_var, 
                                               values=["中文", "英文", "日文", "中英混合", "日英混合", "多语种混合"])
        self.text_lang_combo.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.advanced_frame, text="提示语言:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.prompt_lang_var = ctk.StringVar(value=self.api_client.default_params.get('prompt_text_lang', '中文'))
        self.prompt_lang_combo = ctk.CTkComboBox(self.advanced_frame, variable=self.prompt_lang_var,
                                                 values=["中文", "英文", "日文"])
        self.prompt_lang_combo.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # 生成参数
        ctk.CTkLabel(self.advanced_frame, text="Top K:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.top_k_var = ctk.StringVar(value=str(self.api_client.default_params.get('top_k', 10)))
        self.top_k_entry = ctk.CTkEntry(self.advanced_frame, textvariable=self.top_k_var)
        self.top_k_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.advanced_frame, text="Top P:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.top_p_var = ctk.StringVar(value=str(self.api_client.default_params.get('top_p', 1.0)))
        self.top_p_entry = ctk.CTkEntry(self.advanced_frame, textvariable=self.top_p_var)
        self.top_p_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.advanced_frame, text="Temperature:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.temperature_var = ctk.StringVar(value=str(self.api_client.default_params.get('temperature', 1.0)))
        self.temperature_entry = ctk.CTkEntry(self.advanced_frame, textvariable=self.temperature_var)
        self.temperature_entry.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        
        # 文本处理参数
        ctk.CTkLabel(self.advanced_frame, text="文本切分:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.text_split_var = ctk.StringVar(value=self.api_client.default_params.get('text_split_method', '按标点符号切'))
        self.text_split_combo = ctk.CTkComboBox(self.advanced_frame, variable=self.text_split_var,
                                                values=["按标点符号切", "凑四句一切", "凑50字一切", "按中文句号。切", "按英文句号.切", "按换行切"])
        self.text_split_combo.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        
        # 音频处理参数
        ctk.CTkLabel(self.advanced_frame, text="片段间隔:").grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.fragment_interval_var = ctk.StringVar(value=str(self.api_client.default_params.get('fragment_interval', 0.3)))
        self.fragment_interval_entry = ctk.CTkEntry(self.advanced_frame, textvariable=self.fragment_interval_var)
        self.fragment_interval_entry.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        
        # 配置advanced_frame的列权重
        self.advanced_frame.grid_columnconfigure(1, weight=1)
        
        # 提示：全局默认参数在设置页面配置
        tip_label = ctk.CTkLabel(self.details_frame, text="💡 全局默认参数请在'全局设置'标签页中配置", 
                                text_color="gray", font=ctk.CTkFont(size=12))
        tip_label.grid(row=8, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        button_frame = ctk.CTkFrame(self.details_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=20)
        
        self.generate_button = ctk.CTkButton(button_frame, text="生成音频", command=self.generate_audio_for_current_details)
        self.generate_button.pack(side="left", padx=10)
        
        self.play_button = ctk.CTkButton(button_frame, text="播放音频", command=self.play_audio_for_current_details)
        self.play_button.pack(side="left", padx=10)
        self.update_play_button_state()
        
    def get_output_path(self, dialogue_info, ext=".wav"):
        if not dialogue_info or not self.script_data: return None
        script_name = sanitize_filename(self.script_data.get('script_name', 'UntitledScript'))
        script_dir = os.path.join(self.output_dir, script_name)
        scene_dir = os.path.join(script_dir, sanitize_filename(dialogue_info['scene_name']))
        filename_preview = sanitize_filename(dialogue_info['text'])
        line_num = dialogue_info['scene_idx'] * 1000 + dialogue_info['dialogue_idx']
        filename = f"{line_num:04d}_{sanitize_filename(dialogue_info['character'])}_{filename_preview}{ext}"
        return os.path.join(scene_dir, filename)

    def get_all_dialogues(self):
        if not self.script_data: return []
        all_dialogues = []
        for scene_idx, scene in enumerate(self.script_data.get("scenes", [])):
            for dialogue_idx, dialogue in enumerate(scene.get("dialogues", [])):
                all_dialogues.append({"scene_idx": scene_idx, "dialogue_idx": dialogue_idx, "scene_name": scene.get("scene_name"), **dialogue})
        return all_dialogues

    def batch_generate(self):
        missing_dialogues = [
            info for info in self.get_all_dialogues() 
            if not os.path.exists(self.get_output_path(info))
        ]
        
        if not missing_dialogues:
            self.status_bar.configure(text="所有音频均已生成，无需批量生成。")
            return

        self.open_button.configure(state="disabled")
        self.batch_generate_button.configure(state="disabled")

        def task():
            total = len(missing_dialogues)
            for i, info in enumerate(missing_dialogues):
                self.status_bar.configure(text=f"批量生成中 ({i+1}/{total}): {info['text'][:15]}...")
                self.perform_audio_generation(info, blocking=True)
            self.status_bar.configure(text="批量生成完成！")
            self.open_button.configure(state="normal")
            self.batch_generate_button.configure(state="normal")

        Thread(target=task, daemon=True).start()

    def generate_audio_for_current_details(self):
        if not self.current_dialogue_info: return
        self.perform_audio_generation(self.current_dialogue_info)

    def play_audio_for_current_details(self):
        if not self.current_dialogue_info: return
        output_path = self.get_output_path(self.current_dialogue_info)
        self.perform_audio_play(output_path)

    def perform_audio_generation(self, dialogue_info, blocking=False):
        character = dialogue_info['character']
        
        # 获取参数：从详情编辑页面或使用对话信息本身
        if self.current_dialogue_info and dialogue_info == self.current_dialogue_info:
            text = self.text_box.get("1.0", "end-1c")
            emotion = self.emotion_var.get()
            try:
                # 基础参数
                speed = self.speed_slider.get()
                seed = int(self.seed_var.get())
                
                # 高级参数（如果高级设置已展开且控件存在）
                if hasattr(self, 'text_lang_var'):
                    text_lang = self.text_lang_var.get()
                    prompt_text_lang = self.prompt_lang_var.get()
                    top_k = int(self.top_k_var.get())
                    top_p = float(self.top_p_var.get())
                    temperature = float(self.temperature_var.get())
                    text_split_method = self.text_split_var.get()
                    fragment_interval = float(self.fragment_interval_var.get())
                else:
                    # 使用全局默认值
                    text_lang = self.api_client.default_params.get('text_lang', '中文')
                    prompt_text_lang = self.api_client.default_params.get('prompt_text_lang', '中文')
                    top_k = self.api_client.default_params.get('top_k', 10)
                    top_p = self.api_client.default_params.get('top_p', 1.0)
                    temperature = self.api_client.default_params.get('temperature', 1.0)
                    text_split_method = self.api_client.default_params.get('text_split_method', '按标点符号切')
                    fragment_interval = self.api_client.default_params.get('fragment_interval', 0.3)
                    
            except (AttributeError, ValueError) as e:
                self.status_bar.configure(text=f"错误: 参数无效 - {e}")
                return
        else:
            text = dialogue_info['text']
            emotion = dialogue_info['emotion']
            # 使用全局默认参数
            speed = self.api_client.default_params.get('speed_facter', 1.0)
            seed = self.api_client.default_params.get('seed', -1)
            text_lang = self.api_client.default_params.get('text_lang', '中文')
            prompt_text_lang = self.api_client.default_params.get('prompt_text_lang', '中文')
            top_k = self.api_client.default_params.get('top_k', 10)
            top_p = self.api_client.default_params.get('top_p', 1.0)
            temperature = self.api_client.default_params.get('temperature', 1.0)
            text_split_method = self.api_client.default_params.get('text_split_method', '按标点符号切')
            fragment_interval = self.api_client.default_params.get('fragment_interval', 0.3)

        model_name = self.script_character_mapping.get(character)
        if not model_name:
            self.status_bar.configure(text=f"错误: 未找到角色 '{character}' 的模型。")
            return
        
        output_path = self.get_output_path(dialogue_info)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        params_to_save = {
            **self.api_client.default_params,
            "text": text,
            "model_name": model_name,
            "emotion": emotion,
            "speed_facter": speed,
            "seed": seed,
            "text_lang": text_lang,
            "prompt_text_lang": prompt_text_lang,
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "text_split_method": text_split_method,
            "fragment_interval": fragment_interval
        }

        def task():
            if not blocking:
                self.status_bar.configure(text=f"正在为 '{dialogue_info['text'][:10]}...' 生成音频...")
            
            audio_data = self.api_client.generate_audio(**params_to_save)
            
            if audio_data:
                with open(output_path, 'wb') as f: f.write(audio_data)
                
                metadata_path = self.get_output_path(dialogue_info, ext=".json")
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(params_to_save, f, ensure_ascii=False, indent=2)

                if not blocking:
                    self.status_bar.configure(text=f"音频已保存至: {os.path.basename(output_path)}")
                
                dialogue_id = f"dialogue_{dialogue_info['scene_idx']}_{dialogue_info['dialogue_idx']}"
                if dialogue_id in self.overview_widgets:
                    widgets = self.overview_widgets[dialogue_id]
                    widgets['status_label'].configure(text="已生成", text_color="green")
                    widgets['play_button'].configure(state="normal")
                self.update_play_button_state()
            else:
                 if not blocking:
                    self.status_bar.configure(text="错误: API 调用失败。")
        
        if blocking:
            task()
        else:
            Thread(target=task, daemon=True).start()

    def perform_audio_play(self, output_path):
        if not output_path or not os.path.exists(output_path):
            self.status_bar.configure(text="错误: 音频文件不存在。")
            return
        
        winsound.PlaySound(None, winsound.SND_PURGE)
        def task():
            self.status_bar.configure(text=f"正在播放: {os.path.basename(output_path)}")
            try:
                winsound.PlaySound(output_path, winsound.SND_FILENAME)
                self.status_bar.configure(text="播放完毕。")
            except Exception as e:
                self.status_bar.configure(text=f"错误: 无法播放音频: {e}")
        Thread(target=task, daemon=True).start()

    def update_play_button_state(self):
        if not self.current_dialogue_info: return
        output_path = self.get_output_path(self.current_dialogue_info)
        if hasattr(self, 'play_button'):
            state = "normal" if output_path and os.path.exists(output_path) else "disabled"
            self.play_button.configure(state=state)

    def toggle_advanced_settings(self):
        """切换高级设置的显示/隐藏"""
        if self.advanced_expanded.get():
            # 隐藏高级设置
            self.advanced_frame.grid_remove()
            self.advanced_toggle.configure(text="▶ 高级设置")
            self.advanced_expanded.set(False)
        else:
            # 显示高级设置
            self.advanced_frame.grid()
            self.advanced_toggle.configure(text="▼ 高级设置")
            self.advanced_expanded.set(True)

    def create_settings_page(self):
        """创建全局设置页面"""
        # API设置
        ctk.CTkLabel(self.settings_frame, text="API 设置", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        
        ctk.CTkLabel(self.settings_frame, text="API 地址:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.api_url_var = ctk.StringVar(value=self.api_client.base_url)
        self.api_url_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.api_url_var, width=300)
        self.api_url_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # 语言设置
        ctk.CTkLabel(self.settings_frame, text="语言设置", font=ctk.CTkFont(size=18, weight="bold")).grid(row=2, column=0, columnspan=2, pady=(20, 10), sticky="w")
        
        ctk.CTkLabel(self.settings_frame, text="默认文本语言:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.global_text_lang_var = ctk.StringVar(value=self.api_client.default_params.get('text_lang', '中文'))
        self.global_text_lang_combo = ctk.CTkComboBox(self.settings_frame, variable=self.global_text_lang_var,
                                                      values=["中文", "英文", "日文", "中英混合", "日英混合", "多语种混合"])
        self.global_text_lang_combo.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.settings_frame, text="默认提示语言:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.global_prompt_lang_var = ctk.StringVar(value=self.api_client.default_params.get('prompt_text_lang', '中文'))
        self.global_prompt_lang_combo = ctk.CTkComboBox(self.settings_frame, variable=self.global_prompt_lang_var,
                                                        values=["中文", "英文", "日文"])
        self.global_prompt_lang_combo.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        
        # 生成参数
        ctk.CTkLabel(self.settings_frame, text="生成参数", font=ctk.CTkFont(size=18, weight="bold")).grid(row=5, column=0, columnspan=2, pady=(20, 10), sticky="w")
        
        ctk.CTkLabel(self.settings_frame, text="Top K:").grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.global_top_k_var = ctk.StringVar(value=str(self.api_client.default_params.get('top_k', 10)))
        self.global_top_k_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.global_top_k_var)
        self.global_top_k_entry.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.settings_frame, text="Top P:").grid(row=7, column=0, padx=10, pady=5, sticky="w")
        self.global_top_p_var = ctk.StringVar(value=str(self.api_client.default_params.get('top_p', 1.0)))
        self.global_top_p_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.global_top_p_var)
        self.global_top_p_entry.grid(row=7, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.settings_frame, text="Temperature:").grid(row=8, column=0, padx=10, pady=5, sticky="w")
        self.global_temperature_var = ctk.StringVar(value=str(self.api_client.default_params.get('temperature', 1.0)))
        self.global_temperature_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.global_temperature_var)
        self.global_temperature_entry.grid(row=8, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.settings_frame, text="重复惩罚:").grid(row=9, column=0, padx=10, pady=5, sticky="w")
        self.global_repetition_penalty_var = ctk.StringVar(value=str(self.api_client.default_params.get('repetition_penalty', 1.35)))
        self.global_repetition_penalty_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.global_repetition_penalty_var)
        self.global_repetition_penalty_entry.grid(row=9, column=1, padx=10, pady=5, sticky="ew")
        
        # 文本处理参数
        ctk.CTkLabel(self.settings_frame, text="文本处理", font=ctk.CTkFont(size=18, weight="bold")).grid(row=10, column=0, columnspan=2, pady=(20, 10), sticky="w")
        
        ctk.CTkLabel(self.settings_frame, text="文本切分方式:").grid(row=11, column=0, padx=10, pady=5, sticky="w")
        self.global_text_split_var = ctk.StringVar(value=self.api_client.default_params.get('text_split_method', '按标点符号切'))
        self.global_text_split_combo = ctk.CTkComboBox(self.settings_frame, variable=self.global_text_split_var,
                                                       values=["按标点符号切", "凑四句一切", "凑50字一切", "按中文句号。切", "按英文句号.切", "按换行切"])
        self.global_text_split_combo.grid(row=11, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.settings_frame, text="批处理大小:").grid(row=12, column=0, padx=10, pady=5, sticky="w")
        self.global_batch_size_var = ctk.StringVar(value=str(self.api_client.default_params.get('batch_size', 1)))
        self.global_batch_size_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.global_batch_size_var)
        self.global_batch_size_entry.grid(row=12, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.settings_frame, text="批处理阈值:").grid(row=13, column=0, padx=10, pady=5, sticky="w")
        self.global_batch_threshold_var = ctk.StringVar(value=str(self.api_client.default_params.get('batch_threshold', 0.75)))
        self.global_batch_threshold_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.global_batch_threshold_var)
        self.global_batch_threshold_entry.grid(row=13, column=1, padx=10, pady=5, sticky="ew")
        
        # 音频处理参数
        ctk.CTkLabel(self.settings_frame, text="音频处理", font=ctk.CTkFont(size=18, weight="bold")).grid(row=14, column=0, columnspan=2, pady=(20, 10), sticky="w")
        
        ctk.CTkLabel(self.settings_frame, text="片段间隔:").grid(row=15, column=0, padx=10, pady=5, sticky="w")
        self.global_fragment_interval_var = ctk.StringVar(value=str(self.api_client.default_params.get('fragment_interval', 0.3)))
        self.global_fragment_interval_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.global_fragment_interval_var)
        self.global_fragment_interval_entry.grid(row=15, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.settings_frame, text="采样步数:").grid(row=16, column=0, padx=10, pady=5, sticky="w")
        self.global_sample_steps_var = ctk.StringVar(value=str(self.api_client.default_params.get('sample_steps', 16)))
        self.global_sample_steps_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.global_sample_steps_var)
        self.global_sample_steps_entry.grid(row=16, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.settings_frame, text="音频格式:").grid(row=17, column=0, padx=10, pady=5, sticky="w")
        self.global_media_type_var = ctk.StringVar(value=self.api_client.default_params.get('media_type', 'wav'))
        self.global_media_type_combo = ctk.CTkComboBox(self.settings_frame, variable=self.global_media_type_var,
                                                       values=["wav", "mp3", "flac"])
        self.global_media_type_combo.grid(row=17, column=1, padx=10, pady=5, sticky="ew")
        
        # 高级选项
        ctk.CTkLabel(self.settings_frame, text="高级选项", font=ctk.CTkFont(size=18, weight="bold")).grid(row=18, column=0, columnspan=2, pady=(20, 10), sticky="w")
        
        self.global_split_bucket_var = ctk.BooleanVar(value=self.api_client.default_params.get('split_bucket', True))
        self.global_split_bucket_check = ctk.CTkCheckBox(self.settings_frame, text="启用分桶处理", variable=self.global_split_bucket_var)
        self.global_split_bucket_check.grid(row=19, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        self.global_parallel_infer_var = ctk.BooleanVar(value=self.api_client.default_params.get('parallel_infer', True))
        self.global_parallel_infer_check = ctk.CTkCheckBox(self.settings_frame, text="启用并行推理", variable=self.global_parallel_infer_var)
        self.global_parallel_infer_check.grid(row=20, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        self.global_if_sr_var = ctk.BooleanVar(value=self.api_client.default_params.get('if_sr', False))
        self.global_if_sr_check = ctk.CTkCheckBox(self.settings_frame, text="启用超分辨率", variable=self.global_if_sr_var)
        self.global_if_sr_check.grid(row=21, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # 保存按钮
        save_button = ctk.CTkButton(self.settings_frame, text="保存设置", command=self.save_global_settings)
        save_button.grid(row=22, column=0, columnspan=2, pady=20)

    def save_global_settings(self):
        """保存全局设置到配置文件"""
        try:
            # 更新API客户端的参数
            self.api_client.base_url = self.api_url_var.get()
            
            # 收集所有参数
            new_params = {
                'text_lang': self.global_text_lang_var.get(),
                'prompt_text_lang': self.global_prompt_lang_var.get(),
                'top_k': int(self.global_top_k_var.get()),
                'top_p': float(self.global_top_p_var.get()),
                'temperature': float(self.global_temperature_var.get()),
                'repetition_penalty': float(self.global_repetition_penalty_var.get()),
                'text_split_method': self.global_text_split_var.get(),
                'batch_size': int(self.global_batch_size_var.get()),
                'batch_threshold': float(self.global_batch_threshold_var.get()),
                'fragment_interval': float(self.global_fragment_interval_var.get()),
                'sample_steps': int(self.global_sample_steps_var.get()),
                'media_type': self.global_media_type_var.get(),
                'split_bucket': self.global_split_bucket_var.get(),
                'parallel_infer': self.global_parallel_infer_var.get(),
                'if_sr': self.global_if_sr_var.get()
            }
            
            # 更新API客户端的默认参数
            self.api_client.default_params.update(new_params)
            
            # 保存到配置文件
            import yaml
            config_data = {
                'api': {'base_url': self.api_url_var.get()},
                'inference_defaults': {**self.api_client.default_params, **new_params}
            }
            
            with open('config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            self.status_bar.configure(text="全局设置已保存")
            
        except (ValueError, TypeError) as e:
            self.status_bar.configure(text=f"保存设置失败: 参数格式错误 - {e}")
        except Exception as e:
            self.status_bar.configure(text=f"保存设置失败: {e}")

    def clear_main_frame(self):
        for widget in self.details_frame.winfo_children():
            widget.destroy() 