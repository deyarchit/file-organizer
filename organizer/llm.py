import json
from typing import List, Union

from litellm import CustomStreamWrapper, completion
from litellm.types.utils import ModelResponse, StreamingChoices

from organizer.models import FlatFileItem, LLMResponseSchema


class IntelligentFileOrganizer:
    def __init__(self, model: str = "gemini/gemini-2.5-flash"):
        self.model = model
        self.system_prompt = """
        You are an expert file system organizer. Your task is to analyze the provided directory structure and propose up to three distinct, logical, and practical reorganization plans. Each plan should aim to improve clarity, accessibility, and reduce clutter.

        For each proposed plan, you must output a JSON object that adheres strictly to the defined `response_schema`.

        Your proposed plans could provide suggestions that:
        * **Group similar file types** (e.g., all `.csv` files, all `.xml` files).
        * **Consolidate files related to the same project or client**
        * **Reduce unnecessary nested subfolders.**
        * **You are encouraged to rename folders to improve organization but do not rename files.**


        Present your suggestions as a JSON array, where each element is one of your proposed organization strategy JSON object.
            """

    def generate_reorganization_strategies(
        self, current_structure: List[FlatFileItem]
    ) -> LLMResponseSchema:
        current_structure_json = json.dumps(
            [item.model_dump() for item in current_structure], indent=2
        )

        response: Union[ModelResponse, CustomStreamWrapper] = completion(
            model=self.model,
            response_format=LLMResponseSchema,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": f"Here is the current file structure in JSON:\n{current_structure_json}",
                },
            ],
            temperature=0.0,
        )

        if isinstance(response, CustomStreamWrapper):
            raise TypeError("Expected Non-Streaming response but got streaming response")

        if isinstance(response.choices[0], StreamingChoices):
            raise TypeError("Expected Non-Streaming response but got streaming response")

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("LLM response content is None")

        return LLMResponseSchema.model_validate_json(content)
