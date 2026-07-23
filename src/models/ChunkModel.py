from .BaseDataModel import BaseDataModel
from .db_schemes import DataChunk
from bson.objectid import ObjectId
from sqlalchemy import select,delete

class ChunkModel(BaseDataModel):

    def __init__(self,db_client:object):

        super().__init__(db_client)
        self.db_client =db_client


    @classmethod
    async def create_instance(cls ,db_client:object):
        
        instance=cls(db_client)
        return instance

    async def create_chunks(self,chunk:DataChunk):
        async with self.db_client() as session:
            async with session.begin():
                session.add(chunk)
                await session.commit()
                await session.refresh(chunk)
        return chunk

    async def get_chunk(self,chunk_id:str):
        async with self.db_client() as session:
            async with session.begin():
                result = await session.execute(select(DataChunk).where(DataChunk.chunk_id == chunk_id))
                chunk = result.scalar_one_or_none()
        return chunk

    async def insert_many_chunks(self,chunks:list[DataChunk] , batch_size:int = 100):
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0,len(chunks),batch_size):
                    session.add_all(chunks[i:i+batch_size])
                    await session.commit()
        return len(chunks)
    
    async def delete_chunks_by_project_id(self,project_id:ObjectId ):
        async with self.db_client() as session:
            async with session.begin():
                atmt = delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
                result = await session.execute(atmt)
                await session.commit()
        return result.rowcount

    async def get_DataChunks(self,project_id:ObjectId,page_no:int=1,page_size:int=100):
        async with self.db_client() as session:
            async with session.begin():
                result = await session.execute(select(DataChunk).where(DataChunk.chunk_project_id == project_id).limit(page_size).offset((page_no-1)*page_size))
                chunks = result.scalars().all()
        return chunks