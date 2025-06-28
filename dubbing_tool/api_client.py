import requests
import os

class ApiClient:
    """
    与 GPT-SoVITS API 交互的客户端。
    """

    def __init__(self, base_url: str):
        """
        初始化 API 客户端。

        :param base_url: API 的基础 URL。
        """
        self.base_url = base_url.rstrip('/')

    def generate_audio(self, text: str, voice: str, model: str = "tts-v4", response_format: str = "wav", **kwargs) -> bytes | None:
        """
        调用 API 生成音频。

        :param text: 要转换为语音的文本。
        :param voice: 使用的声音模型 (对应 'voice' 参数)。
        :param model: 使用的 TTS 模型 (对应 'model' 参数)。
        :param response_format: 音频格式。
        :param kwargs: 其他 API 参数。
        :return: 音频文件的二进制数据，如果失败则返回 None。
        """
        endpoint = "/v1/audio/speech"
        url = self.base_url + endpoint

        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": response_format,
            "other_params": kwargs  # 传递额外参数
        }

        try:
            response = requests.post(url, json=payload, timeout=300) # 设置较长的超时时间
            response.raise_for_status()  # 如果请求失败 (状态码非 2xx)，则抛出异常
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"调用 API 失败: {e}")
            return None 