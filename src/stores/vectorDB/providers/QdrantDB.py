from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
from qdrant_client import QdrantClient , models
import logging
from typing import List

class QdrantDB(VectorDBInterface):

    def __init__(self ,db_path:str , distance_method:str):
        self.client = None
        self.db_path = db_path

        distance_method = distance_method.upper()

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT
        elif distance_method == DistanceMethodEnums.EUCLIDEAN.value:
            self.distance_method = models.Distance.EUCLID
        else:
            raise ValueError("Invalid distance method")
        
        self.logger = logging.getLogger(__name__)

    def connect(self):
        if self.db_path == ":memory:":
            self.client = QdrantClient(location=":memory:")
        else:
            self.client = QdrantClient(path=self.db_path)

    def disconnect(self):
        self.client=None
        
    def is_connection_exsited(self,collection_name:str)->bool:
        return self.client.collection_exists(collection_name)

    def list_all_collections(self)->list:
        return self.client.get_collections()

    def delete_collection(self,collection_name:str):
        if self.is_connection_exsited(collection_name):
            return self.client.delete_collection(collection_name)
        return None
    
    def get_collection_info(self,collection_name:str):
        if not self.is_connection_exsited(collection_name):
            return None
        return self.client.get_collection(collection_name)
    
    def create_collection(self,collection_name:str,embedding_size:int,do_reset:bool=False):
        if do_reset:
            _ = self.delete_collection(collection_name)
        if not self.is_connection_exsited(collection_name):
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                size=embedding_size,
                distance=self.distance_method))
            return True
        return False
    
    def insert_one(self,collection_name:str,text:str,vector:list,metadata:dict=None,recored_id:str =None):
        if not self.is_connection_exsited(collection_name):
            self.logger.error(f"Collection {collection_name} not found")
            return False
        try:
            _ = self.client.upload_points(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=recored_id,
                        vector=vector,
                        payload={
                            "text":text,
                            **(metadata or {})
                        }
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"Error while inserting record in {collection_name}: {e}")
            return False
        return True
    
    def insert_many(self,collection_name:str,texts:list,vectors:list,
    metadata:list=None,recored_ids:list =None , batch_size:int =50):

        if metadata is None:
            metadata = [None]*len(texts)

        if recored_ids is None:
            recored_ids = list(range(0,len(texts)))


        for i in range(0,len(texts),batch_size):
            end = min(i+batch_size,len(texts))
            batch_texts = texts[i:end]
            batch_vectors = vectors[i:end]
            batch_metadata = metadata[i:end]
            batch_recored_ids = recored_ids[i:end]

            batch_recored = [
                models.PointStruct(
                    id=batch_recored_ids[j],
                    vector=batch_vectors[j],
                    payload={
                        "text":batch_texts[j],
                        **(batch_metadata[j] or {})
                    }
                ) for j in range(len(batch_texts))
            ]

            try:
                _ = self.client.upload_points(
                    collection_name=collection_name,
                    points=batch_recored,
                )
            except Exception as e:
                self.logger.error(f"Error while inserting batch records in {collection_name}: {e}")
                return False
            
        return True
        
    
    def search_by_vector(self,collection_name:str,vector:list,limit:int):
        results = self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit
        )
        return results.points
    
        
    
        
    