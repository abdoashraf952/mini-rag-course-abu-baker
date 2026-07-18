from .BaseDataModel import BaseDataModel
from .db_schemes import Data_chunk
from .enums.DataBaseEnum import DataBaseEnum
from bson.objectid import ObjectId
from pymongo import InsertOne

class ChunkModel(BaseDataModel):

    def __init__(self,db_client:object):

        super().__init__(db_client)
        self.collection = self.db[DataBaseEnum.COLLECTION_CHUNK_NAME.value]


    @classmethod
    async def create_instance(cls ,db_client:object):
        
        instance=cls(db_client)
        await instance.init_collection()
        return instance

    async def init_collection(self):
        all_collections = await self.db.list_collection_names()

        if DataBaseEnum.COLLECTION_CHUNK_NAME.value not in all_collections:
            self.collection = self.db[DataBaseEnum.COLLECTION_CHUNK_NAME.value]
            indexes = Data_chunk.get_indexes()

            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    unique=index["unique"],
                    name=index["name"]
                )
        else:
            self.collection = self.db[DataBaseEnum.COLLECTION_CHUNK_NAME.value]


    async def create_chunks(self,chunk:Data_chunk):
        result = await self.collection.insert_one(chunk.dict(by_alias=True, exclude_unset=True))
        chunk.id = result.inserted_id
        return chunk

    async def get_chunk(self,chunk_id:str):
        result = await self.collection.find_one({"_id":ObjectId(chunk_id)})
        if result is None:
            return None
        
        return Data_chunk(**result)

    async def insert_many_chunks(self,chunks:list , batch_size:int = 100):
        for i in range(0,len(chunks),batch_size):
            batch_chunks = chunks[i:i+batch_size]
            
            operations = [
                InsertOne(chunk.dict(by_alias=True, exclude_unset=True))
                for chunk in batch_chunks
            ]

            await self.collection.bulk_write(operations)
        
        return len(chunks)
    
    
    
    async def delete_chunks_by_project_id(self,project_id:ObjectId ):
        result = await self.collection.delete_many({
            "chunk_project_id":project_id
        })
        return result.deleted_count

    async def get_data_chunks(self,project_id:ObjectId,page_no:int=1,page_size:int=100):
        result = await self.collection.find({
            "chunk_project_id":project_id
        }).skip((page_no-1)*page_size).limit(page_size).to_list(length=None)
        return [Data_chunk(**chunk) for chunk in result]