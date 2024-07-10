from abc import ABC, abstractmethod
import json
from llm.llmstrategy import LLMStrategy
from jsonschema import validate, ValidationError
import traceback
import strip_markdown
from get_code_from_markdown import *

'''
json structure:
{
    "name": "John Doe",
    "certification": "Cloud Practitioner",
    "qualification_level": "Associate",
    "cloud_provider": "AWS",
    "issue_date": "2022-01-01",
    "expiry_date": "2025-01-01",
    "certificate_id": "123456"
}
'''

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "first_names": {"type": "string"},
        "surname": {"type": "string"},
        "certification": {"type": "string"},
        "qualification_level": {"type": "string"},
        "cloud_provider": {"type": "string"},
        "issue_date": {"type": "string"},
        "expiry_date": {"type": "string"},
        "certificate_id": {"type": "string"},
        "issuing_organization": {"type": "string"},
        "certification_url": {"type": "string"},
    },
    "required": ["first_names", "surname", "certification", "qualification_level", "cloud_provider", "issue_date", "certificate_id", "issuing_organization"]
}

class FileHandler(ABC):
    def __init__(self, llm_strategy: LLMStrategy, max_retry: int = 3) -> None:
        self.llm_strategy = llm_strategy
        self.max_retry = max_retry
        self.default_prompt = "Using the information from the document, can you return a JSON object (with no extra information except the fields required) that adheres to the given schema? schema: " + json.dumps(JSON_SCHEMA)

    def process_file(self, file_path: str) -> dict:
        pass

    def process_file_with_custom_prompt(self, file_path: str, prompt: str) -> dict:
        pass

    def valid_response(self, response: str) -> bool:
        try:
            j = json.loads(response)
            if "error" in j:
                return False
            validate(j, JSON_SCHEMA)
        except json.JSONDecodeError:
            return False
        except ValidationError:
            return False
        except Exception as e:
            print("Error validating response")
            traceback.print_exc()
            return False

        return True

    def strip_md(self, text: str):
        # replace all "```json" with "```" to avoid JSON parsing errors
        print(text)
        text = text.replace("```json", "```")
        text = text.replace("``` json", "```")
        return strip_markdown.strip_markdown(text)
