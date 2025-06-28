import requests
from urllib.parse import urlparse, urljoin

class ApiClient:
    """
    与 GPT-SoVITS API 交互的客户端。
    """

    def __init__(self, base_url: str, default_params: dict):
        """
        初始化 API 客户端。

        :param base_url: API 的基础 URL。
        :param default_params: /infer_single 接口的默认参数字典。
        """
        self.base_url = base_url.rstrip('/')
        self.default_params = default_params if default_params else {}

    def generate_audio(self, text: str, model_name: str, emotion: str, **kwargs) -> bytes | None:
        """
        调用 /infer_single 接口生成音频。
        此方法执行两步操作：
        1. POST 请求到 /infer_single，获取一个包含音频文件 URL 的 JSON 响应。
        2. GET 请求该 URL，下载音频数据。

        :param text: 要转换为语音的文本。
        :param model_name: 使用的声音模型 (对应 'model_name' 参数)。
        :param emotion: 对话情感。
        :param kwargs: 其他需要覆盖默认值的 API 参数 (如 speed_facter, seed 等)。
        :return: 音频文件的二进制数据，如果失败则返回 None。
        """
        # --- 步骤 1: POST 请求，获取音频 URL ---
        infer_endpoint = "/infer_single"
        infer_url = self.base_url + infer_endpoint

        payload = self.default_params.copy()
        payload.update({
            "text": text,
            "model_name": model_name,
            "emotion": emotion,
        })
        payload.update(kwargs)

        try:
            infer_response = requests.post(infer_url, json=payload, timeout=300)
            infer_response.raise_for_status()
            response_json = infer_response.json()

            audio_url_from_server = response_json.get("audio_url")
            if not audio_url_from_server:
                print(f"API 未返回 audio_url。响应: {response_json}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"调用推理 API 失败: {e}")
            try:
                error_details = infer_response.json()
                print(f"错误详情: {error_details}")
            except (ValueError, AttributeError):
                 print(f"无法解析错误响应: {infer_response.text}")
            return None
        except ValueError: # JSONDecodeError
            print(f"无法解析 API 响应为 JSON。响应内容: {infer_response.text}")
            return None

        # --- 步骤 2: GET 请求，下载音频文件 ---
        try:
            # 服务器可能返回一个非外部可访问的 URL (如 http://0.0.0.0:8000/...)
            # 我们需要提取其路径，并与我们配置的 base_url 结合。
            parsed_url = urlparse(audio_url_from_server)
            audio_path = parsed_url.path
            
            download_url = urljoin(self.base_url, audio_path)

            audio_response = requests.get(download_url, timeout=120)
            audio_response.raise_for_status()
            
            return audio_response.content

        except requests.exceptions.RequestException as e:
            print(f"下载音频文件失败: {e}")
            return None
        except Exception as e:
            print(f"处理音频时发生未知错误: {e}")
            return None 