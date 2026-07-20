from .BaseController import BaseController
from models.db_schemes import Project , Data_chunk
from stores.llm.LLMEnums import DocumentTypeEnum
from typing import List
import json



class NLPController(BaseController):

    def __init__(self,vector_client , generation_client , embedding_client,template_parser):
        super().__init__()
        self.vector_client = vector_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser
        
    def create_collection_name(self,project_id:str):
        return f"collection_{project_id}".strip()

    def reset_vector_db_collection(self,project:Project):
        collection_name = self.create_collection_name(project.id)
        return self.vector_client.delete_collection(collection_name)

    def get_vector_db_collection_info(self,project:Project):
        collection_name = self.create_collection_name(project.id)
        collection_info = self.vector_client.get_collection_info(collection_name)
        if collection_info is None:
            return None
        return json.loads(
            json.dumps(collection_info,default=lambda x:x.__dict__)
            )

    def index_into_vector_db(self,project:Project,chunks:List[Data_chunk],chunks_ids:List[int],do_reset:bool=False):

        collection_name = self.create_collection_name(project.id)

        texts = [chunk.chunk_text for chunk in chunks]
        metadata = [chunk.chunk_metadata for chunk in chunks]
        vectors = self.embedding_client.embed_texts(texts, document_type=DocumentTypeEnum.DOCUMENT.value)
        if not vectors:
            return False

        _ = self.vector_client.create_collection(collection_name,embedding_size=self.embedding_client.embedding_size,do_reset=do_reset)

        _ = self.vector_client.insert_many(collection_name=collection_name,texts=texts,vectors=vectors,metadata=metadata,recored_ids=chunks_ids)

        return True   

    def search_vector_db_collection(self,project:Project,text:str,limit:int = 10):
        collection_name = self.create_collection_name(project.id)
        vector = self.embedding_client.embed_text(text, document_type=DocumentTypeEnum.QUERY.value)

        if not vector or len(vector)==0:
            return False

        result = self.vector_client.search_by_vector(collection_name=collection_name,vector=vector,limit=limit)
        if not result:
            return False
        return json.loads(
            json.dumps(result,default=lambda x:x.__dict__)
            )
        
    def answer_rag_qustion(self,project:Project,query:str ,limit:int =10):
        answer , full_prompt ,chat_history= None,None,None
        retrived_documents = self.search_vector_db_collection(project,query,limit)
        if not retrived_documents or len(retrived_documents)==0:
            return answer , full_prompt ,chat_history
        
        system_prompt = self.template_parser.get("rag","system_prompt")
        documents_prompt = "\n\n".join([
            self.template_parser.get("rag","document_prompt",{
                "doc_no":idx+1,
                "chunk_text":doc["text"]
            }) for idx, doc in enumerate(retrived_documents)
        ])

        footer_prompt = self.template_parser.get("rag","footer_prompt")

        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value)
        ]

        full_prompt = "/n/n".join([documents_prompt,footer_prompt])
        
        answer= self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history
        )

        return answer , full_prompt ,chat_history

        
        

        


    