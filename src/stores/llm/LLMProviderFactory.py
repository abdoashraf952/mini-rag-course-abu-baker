from .providers.OpenAIProvider import OpenAIProvider
from .providers.CohereProvider import CohereProvider
from .LLMEnums import LLMEnum


class LLMProviderFactory:

    def __init__(self, config:dict):
        self._config = config

    def create(self,provider:str):
        if provider == LLMEnum.OPENAI.value:
            return OpenAIProvider(
                api_key=self._config.OPENAI_API_KEY,
                api_url=self._config.OPENAI_API_URL,
                default_input_max_characters=self._config.INPUT_DAFAULT_MAX_CHARACTERS,
                default_generation_max_output_tokens=self._config.GENERATION_DAFAULT_MAX_TOKENS,
                default_generation_temperature=self._config.GENERATION_DAFAULT_TEMPERATURE
            )
        elif provider == LLMEnum.COHERE.value:
            return CohereProvider(
                api_key=self._config.COHERE_API_KEY,
                default_input_max_characters=self._config.INPUT_DAFAULT_MAX_CHARACTERS,
                default_generation_max_output_tokens=self._config.GENERATION_DAFAULT_MAX_TOKENS,
                default_generation_temperature=self._config.GENERATION_DAFAULT_TEMPERATURE
            )
        else:
            raise ValueError(f"Invalid provider: {provider}")


        