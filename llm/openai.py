from typing import Any
from .llmstrategy import LLMStrategy
from utils import get_env_var
from openai import OpenAI
from openai import models


GPT_MODELS = {
    "gpt3": ["gpt-3.5-turbo-1106", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-16k-0613", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-0125", "gpt-3.5-turbo", "gpt-3.5-turbo-instruct", "gpt-3.5-turbo-instruct-0914", "gpt-3.5-turbo-0301"],
    "gpt4": ["gpt-4-32k-0314", "gpt-4-0125-preview", "gpt-4-turbo-preview", "gpt-4-1106-preview", "gpt-4-turbo-2024-04-09", "gpt-4-turbo", "gpt-4", "gpt-4-0613", "gpt-4-0314"],
    "gpt4o": ["gpt-4o", "gpt-4o-2024-05-13"]
}

GPT_DEFAULT_MODELS = {
    "gpt3": "gpt-3.5-turbo",
    "gpt4": "gpt-4",
    "gpt4-turbo": "gpt-4-turbo",
    "gpt4o": "gpt-4o"
}

client = OpenAI(api_key=get_env_var("OPENAI_API_KEY"))
available_models: models = client.models.list()
available_models_names = [model["id"] for model in available_models]

class ChatGPTStrategy(LLMStrategy):
    def __init__(self, model: str = GPT_DEFAULT_MODELS["gpt4o"]) -> None:
        if model not in available_models_names:
            if model == GPT_DEFAULT_MODELS["gpt4o"]:
                raise ValueError(f"Default model {model} not available. Available models are: {available_models_names}")
            model = GPT_DEFAULT_MODELS["gpt4o"]
            print(f"Model {model} not available. Using default model {model}")
        self.model = model

    def generate_response(self, prompt: str) -> str:
        # Implementation for ChatGPT
        chat_completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        return chat_completion.choices[0].message.content

class GPT3Strategy(LLMStrategy):
    def generate_response(self, prompt: str) -> str:
        # Implementation for GPT-3
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-3.5-turbo",
        )

class GPT4Strategy(LLMStrategy):
    def generate_response(self, prompt: str) -> str:
        # Implementation for GPT-4
        return "GPT-4 response"
