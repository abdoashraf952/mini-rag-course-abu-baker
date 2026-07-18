from ..LLMInterface import LLMInterface
from ..LLMEnums import OpenAIEnums
from openai import OpenAI
import logging

class OpenAIProvider(LLMInterface):
    
    def __init__(self, api_key: str = None, api_url: str =None , 
                default_input_max_characters: int=1000,
                default_generation_max_output_tokens: int=1000,
                default_generation_temperature: float=0.1):
        
        self._api_key = api_key
        self._api_url = api_url
        self._default_input_max_characters = default_input_max_characters
        self._default_generation_max_output_tokens = default_generation_max_output_tokens
        self._default_generation_temperature = default_generation_temperature
        
        self.generation_model_id =None
        self.embedding_model_id =None

        self.embedding_size = None

        self.client = OpenAI(
            api_key=self._api_key,
            base_url=self._api_url
        )

        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str ,embedding_size:int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self,text:str):
        return text[:self._default_input_max_characters].strip()
        

    def generate_text(self, prompt: str,chat_history: list=[], max_output_tokens: int=None , temperature: float = None):
        
        if not self.client:
            self.logger.error("Client not initialized")
            return None
        
        if not self.generation_model_id:
            self.logger.error("Generation model not set")
            return None

        max_output_tokens =max_output_tokens if max_output_tokens is not None else self._default_generation_max_output_tokens
        temperature =temperature if temperature is not None else self._default_generation_temperature

        chat_history.append(self.construct_prompt(prompt, OpenAIEnums.USER.value))

        response = self.client.chat.completions.create(
            model=self.generation_model_id,
            messages=chat_history,
            max_tokens=max_output_tokens,
            temperature=temperature
        )

        if not response or not response.choices or len(response.choices) == 0:
            self.logger.error("Error getting response from OpenAI")
            return None

        if response.choices[0].finish_reason == "content_filter":
            self.logger.warning("Content filtered")
            return ""

        if not response.choices[0].message or not response.choices[0].message.content:
            self.logger.error("No content in response")
            return None

        return response.choices[0].message.content.strip()


    def embed_text(self, text:str, document_type:str = None):
        if not self.client:
            self.logger.error("Client not initialized")
            return None
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model not set")
            return None
        
        response = self.client.embeddings.create(
            input=text,
            model=self.embedding_model_id
        )
        if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
            self.logger.error("Error getting embeddings")
            return None
        
        return response.data[0].embedding

    def embed_texts(self, texts: list[str], document_type: str = None) -> list[list[float]]:
        if not self.client:
            self.logger.error("Client not initialized")
            return None
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model not set")
            return None
        
        processed_texts = [self.process_text(text) for text in texts]
        response = self.client.embeddings.create(
            input=processed_texts,
            model=self.embedding_model_id
        )
        if not response or not response.data or len(response.data) == 0:
            self.logger.error("Error getting embeddings")
            return None
        
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    def construct_prompt(self,prompt: str , role:str):
        return {"role":role,"content":self.process_text(prompt)}

        

