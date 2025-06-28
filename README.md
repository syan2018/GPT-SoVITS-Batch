# GPT-SoVITS 配音工具 (GUI版)

这是一个使用 GPT-SoVITS API 进行批量配音的工具，提供了图形用户界面（GUI）以便于操作。

## 功能

-   通过 GUI 加载和管理剧本。
-   支持结构化的 YAML 剧本格式，可定义每句对话的情感等参数。
-   逐句生成配音，并可对单句进行重新生成。
-   直接在应用内播放生成的音频。
-   将生成的配音文件按章节和角色进行组织。

## 项目结构

```
GPT-SoVITS-Batch/
│
├── raw_scripts/
│   ├── 青丘山剧本.txt      (旧格式)
│   └── 青丘山剧本.yaml    (新格式)
│
├── dubbing_tool/
│   ├── __init__.py
│   ├── api_client.py       # 封装与 GPT-SoVITS API 的交互
│   ├── script_parser.py    # 解析 YAML 剧本文件
│   ├── gui.py              # GUI 应用主文件
│   └── main.py             # GUI 应用启动入口
│
├── output/                 # 存放生成的配音文件
│
├── config.yaml             # 配置文件，如 API 地址、角色语音模型映射
├── requirements.txt        # Python 依赖
└── README.md               # 项目说明文档
```

## 使用方法

1.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **配置 `config.yaml`**:
    根据您的设置，修改 API 地址和角色对应的声音模型。

    ```yaml
    api:
      base_url: "http://127.0.0.1:8000"
    
    characters:
      玩家: "shika" # 角色名: voice 参数
      精卫: "misato"
      # ... 其他角色
    ```

3.  **准备剧本**:
    将 YAML 格式的剧本文件放入 `raw_scripts` 文件夹。推荐使用新的 YAML 格式。

4.  **运行工具**:
    在项目的根目录下（即 `GPT-SoVITS-Batch` 目录），运行以下命令：
    ```bash
    python -m dubbing_tool.main
    ```
    这将会启动 GUI 应用。

## 剧本格式标准 (YAML)

为了便于程序解析和功能拓展，我们约定使用以下 YAML 格式：

```yaml
script_name: 剧本标题
scenes:
  - scene_name: 章节一的标题
    dialogues:
      - character: 角色名
        text: "对话内容第一句"
        emotion: "开心" # 可选的情感参数
      - character: 另一个角色
        text: "对话内容第二句"
        emotion: "默认"
  - scene_name: 章节二的标题
    dialogues:
      # ...
```
--- 