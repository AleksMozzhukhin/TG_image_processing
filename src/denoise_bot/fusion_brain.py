import json
import time

import requests


class FusionBrainAPI:
    """Клиент для взаимодействия с API FusionBrain (Kandinsky)."""

    def __init__(self, url: str, api_key: str, secret_key: str):
        """
        Инициализирует API клиент.

        Args:
            url (str): Базовый URL для API.
            api_key (str): Ваш API ключ.
            secret_key (str): Ваш секретный ключ.
        """
        self.URL = url
        self.AUTH_HEADERS = {
            "X-Key": f"Key {api_key}",
            "X-Secret": f"Secret {secret_key}",
        }

    def get_pipeline(self) -> str:
        """
        Получает идентификатор доступной модели (pipeline).

        Returns:
            str: Идентификатор первого доступного pipeline.
        """
        response = requests.get(self.URL + "key/api/v1/pipelines", headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]["id"]

    def generate(self, prompt: str, pipeline_id: str, images: int = 1, width: int = 1024, height: int = 1024) -> str:
        """
        Запускает процесс генерации изображения.

        Args:
            prompt (str): Текстовое описание для генерации.
            pipeline_id (str): Идентификатор модели для использования.
            images (int): Количество генерируемых изображений.
            width (int): Ширина изображения.
            height (int): Высота изображения.

        Returns:
            str: UUID запущенной задачи генерации.
        """
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {"query": f'"{prompt}"'},
        }

        data = {"pipeline_id": (None, pipeline_id), "params": (None, json.dumps(params), "application/json")}
        response = requests.post(self.URL + "key/api/v1/pipeline/run", headers=self.AUTH_HEADERS, files=data)
        data = response.json()
        return data["uuid"]

    def check_generation(self, request_id: str, attempts: int = 10, delay: int = 10) -> list:
        """
        Проверяет статус генерации и возвращает результат.

        Args:
            request_id (str): UUID задачи для проверки.
            attempts (int): Количество попыток проверки.
            delay (int): Задержка между попытками в секундах.

        Returns:
            list: Список сгенерированных изображений в формате base64.
        """
        while attempts > 0:
            response = requests.get(self.URL + "key/api/v1/pipeline/status/" + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data["status"] == "DONE":
                return data["result"]["files"]

            attempts -= 1
            time.sleep(delay)
