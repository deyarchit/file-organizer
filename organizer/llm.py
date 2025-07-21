from typing import List, Union

from litellm import CustomStreamWrapper, completion
from litellm.types.utils import ModelResponse, StreamingChoices

from organizer.models import FlatFileItem, LLMResponseSchema


class LLMClient:
    def __init__(self, model: str = "gemini/gemini-2.5-flash"):
        self.model = model

    def generate_options(
        self, current_structure: List[FlatFileItem], system_prompt: str
    ) -> LLMResponseSchema:
        response: Union[ModelResponse, CustomStreamWrapper] = completion(
            model=self.model,
            response_format=LLMResponseSchema,
            messages=[
                {"content": system_prompt, "role": "system"},
                {"content": str(current_structure), "role": "user"},
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
