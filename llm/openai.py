from io import BufferedReader
from typing import List
from .llmstrategy import LLMStrategy
from utils import get_env_var, print_pretty
from openai import OpenAI
from openai import models
from openai.types.beta.vector_store import VectorStore
from openai.types.beta.vector_stores import VectorStoreFile, VectorStoreFileBatch
from openai.types.beta.threads.run import Run
from openai.types.beta.threads.message import Message
from openai.types.beta.threads.message_content import MessageContent
import time
import requests


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

RUN_TERMINAL_STATES = ["requires_action", "cancelled", "completed", "failed", "expired", "incomplete"]

client = OpenAI(api_key=get_env_var("OPENAI_API_KEY"))
available_models = client.models.list()
available_models_names = [model.id for model in available_models]

def get_and_set_vector_store() -> VectorStore:
    vector_stores = client.beta.vector_stores.list()
    for vector_store in vector_stores:
        if vector_store.name == "Cloud Certificate Vector Store":
            return vector_store

    vector_store = client.beta.vector_stores.create(
        name="Cloud Certificate Vector Store",
        metadata={"description": "Vector store for Cloud Certificate Assistant"},
    )
    return vector_store

vector_store: VectorStore = get_and_set_vector_store()

class ChatGPTStrategy(LLMStrategy):
    def __init__(self, model: str = GPT_DEFAULT_MODELS["gpt4o"], max_tokens: int = 300) -> None:
        if model not in available_models_names:
            if model == GPT_DEFAULT_MODELS["gpt4o"]:
                raise ValueError(f"Default model {model} not available. Available models are: {available_models_names}")
            model = GPT_DEFAULT_MODELS["gpt4o"]
            print(f"Model {model} not available. Using default model {model}")
        self.model = model
        self.max_tokens = max_tokens

        global assistant
        assistant = client.beta.assistants.create(
            name="Document Analyst Assistant",
            instructions="You are an expert in analyzing documents and returning information read from them in a structured format. Use your knowledge base to answer questions from the documents provided.",
            model=self.model,
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )

        super().__init__()

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
    
    def generate_response_with_image(self, prompt: str, base64_image: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_env_var('OPENAI_API_KEY')}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": prompt
                    },
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                    }
                ]
                }
            ],
            "max_tokens": self.max_tokens
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        print_pretty(response.json())
        return "Not implemented yet."
    
    def upload_to_vector_store(self, file_buffer: BufferedReader) -> VectorStoreFileBatch:
        file_batch: VectorStoreFileBatch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=[file_buffer]
        )
        return file_batch
    
    def get_response_with_given_file_id(self, prompt: str, file_id: str) -> Message:
        print('Creating thread...')
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "attachments": [{
                        "file_id": file_id,
                        "tools": [{ "type": "file_search"}],
                    }],
                }
            ],
        )

        print('Creating run...')
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="You are an expert in analyzing documents and returning information read from them in a structured format. Use your knowledge base to answer questions from the documents provided.",
        )

        r: Run = None
        while True:
            r = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            print('Run status:', r.status)
            if r.status in RUN_TERMINAL_STATES:
                break
            time.sleep(1)
            
        print('Getting messages...')
        messages: List[Message] = client.beta.threads.messages.list(thread_id=thread.id).data
        m: Message = messages[0]
        return m
    
    def generate_response_with_file(self, prompt: str, file_buffer: BufferedReader) -> str:
        # uploaded_file = self.upload_to_vector_store(file_buffer)
        
        print('Creating file...')
        message_file = client.files.create(
            file=file_buffer,
            purpose="assistants"
        )
        
        print('Creating thread...')
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "attachments": [{
                        "file_id": message_file.id,
                        "tools": [{ "type": "file_search"}],
                    }],
                }
            ],
        )

        print('Creating run...')
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="You are an expert in analyzing documents and returning information read from them in a structured format. Use your knowledge base to answer questions from the documents provided.",
        )

        r: Run = None
        while True:
            r = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            print('Run status:', r.status)
            if r.status in RUN_TERMINAL_STATES:
                break
            time.sleep(1)
            
        print('Getting messages...')
        messages: List[Message] = client.beta.threads.messages.list(thread_id=thread.id).data
        print('Messages:', messages)
        m: Message = messages[0]
        mC: MessageContent = m.content
        return mC[0].text.value

class GPT3Strategy(ChatGPTStrategy):
    def __init__(self) -> None:
        super().__init__(GPT_DEFAULT_MODELS["gpt3"])
    

class GPT4Strategy(ChatGPTStrategy):
    def __init__(self) -> None:
        super().__init__(GPT_DEFAULT_MODELS["gpt4"])
        
class GPT4TurboStrategy(ChatGPTStrategy):
    def __init__(self) -> None:
        super().__init__(GPT_DEFAULT_MODELS["gpt4-turbo"])
        
class GPT4oStrategy(ChatGPTStrategy):
    def __init__(self) -> None:
        super().__init__(GPT_DEFAULT_MODELS["gpt4o"])
