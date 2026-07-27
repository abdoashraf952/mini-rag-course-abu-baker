from .BaseController import BaseController
from .ProjectController import ProjectController
import os
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from models import ProcessingEnum
from typing import List
from dataclasses import dataclass
@dataclass
class Document:
    page_content: str
    metadata: dict

class ProcessController(BaseController):
    def __init__(self, project_id: str):
        super().__init__()
        
        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)
        
    def get_file_extension(self, file_id: str):
        return os.path.splitext(file_id)[1]

    def get_file_loader(self, file_id: str):

        file_ext = self.get_file_extension(file_id=file_id)
        file_path = os.path.join(
            self.project_path,
            file_id
        )

        if not os.path.exists(file_path):
            return None

        if file_ext == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path)

        elif file_ext == ProcessingEnum.TXT.value:
            return TextLoader(file_path, encoding="utf-8")
        else:
            return None

    def get_file_content(self, file_id: str):
        loader = self.get_file_loader(file_id=file_id)
        if loader is None:
            return None
            
        return loader.load()

    def process_file_content(self, file_content, file_id: str, chunk_size: int = 100, overlap_size: int = 20):


        file_text     = [rec.page_content for rec in file_content]
        file_metadata = [rec.metadata     for rec in file_content]

        return self.process_simpler_splitter(texts=file_text, metadatas=file_metadata, chunk_size=chunk_size)

     
    def process_simpler_splitter(self, texts: List[str], metadatas: List[dict], chunk_size: int = 100,spllitter_tag="\n"):
        full_text = " ".join(texts)

        lines=[doc.strip() for doc in full_text.split(spllitter_tag)if len(doc.strip())>1]

        chunks =[]
        current_chunk = ""
        
        for line in lines:
            current_chunk+=line +spllitter_tag
            if len(current_chunk)>= chunk_size:
                chunks.append(Document(
                    page_content=current_chunk.strip(),
                    metadata= {}   
                ))

                current_chunk= ""

        if current_chunk.strip():
            chunks.append(Document(
                page_content=current_chunk.strip(),
                metadata= {}
            ))
            
        return chunks
            
