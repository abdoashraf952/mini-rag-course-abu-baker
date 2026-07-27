from ..VectorDBInterface import VectorDBInterface
from .. VectorDBInterface import VectorDBInterface
from .. VectorDBEnums import (PgvectorTableSchemeEnums,DistanceMethodEnums,PgvectorIndexTypeEnums,PgvectorDistanceMethodEnums)

import logging
from typing import List
from models.db_schemes import RetrivedDocument
from sqlalchemy.sql import text as sql_text
import json

class PGVectorProvider(VectorDBInterface):

    def __init__(self,db_client,default_vector_size :int =786,distance_method : str =None,index_threshold:int=100):
        self.db_client=db_client
        self.default_vector_size=default_vector_size

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method=PgvectorDistanceMethodEnums.COSINE.value
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method=PgvectorDistanceMethodEnums.DOT.value
        elif distance_method == DistanceMethodEnums.EUCLIDEAN.value:
            self.distance_method=PgvectorDistanceMethodEnums.EUCLIDEAN.value
            
        self.pgvector_table_prefix = PgvectorTableSchemeEnums._PREFIX.value
        self.index_threshold=index_threshold
        self.logger = logging.getLogger("uvicorn")
        self.defult_index_name = lambda collection_name:f"{collection_name}_vector_idx"
        
    async def connect(self):
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(
                        sql_text(f"CREATE EXTENSION IF NOT EXISTS vector;"  )
                    )

                await session.commit()

    async def disconnect(self):
        pass 

    async def is_connection_exsited(self,collection_name : str) -> bool:
        async with self.db_client() as session:
            async with session.begin():
                list_tbl = sql_text(f'SELECT * FROM pg_tables WHERE tablename = :collection_name')
                result =await session.execute(list_tbl,{"collection_name":collection_name})
                record = result.scalar_one_or_none()
                return bool(record)

    async def list_all_collections(self) -> List[str]:
        records=[]
        async with self.db_client() as session:
            async with session.begin():
                list_tbl = sql_text(f'SELECT * FROM pg_tables WHERE tablename LIKE :prefix')
                result =await session.execute(list_tbl,{'prefix':self.pgvector_table_prefix+'%'})
                records = result.scalars().all()
        return records

    async def get_collection_info(self, collection_name: str) -> dict:
        async with self.db_client() as session:
            async with session.begin():
                table_info_sql = sql_text('''
                SELECT schemaname, tablename, tableowner, tablespace, hasindexes
                FROM pg_tables
                WHERE tablename = :collection_name
                ''')
                count_sql = sql_text(f'SELECT count(*) FROM {collection_name}')

                table_info_result = await session.execute(table_info_sql, {
                    "collection_name": collection_name
                })
                record_count_result = await session.execute(count_sql)

                table_info = table_info_result.one_or_none()
                record_count = record_count_result.scalar()

                if not table_info:
                    return None

                return {
                    "table_info":{
                        "schemaname": table_info.schemaname,
                        "tablename": table_info.tablename,
                        "tableowner": table_info.tableowner,
                        "tablespace": table_info.tablespace,
                        "hasindexes": table_info.hasindexes
                    },
                    "record_count": record_count
                }
    
    async def delete_collection(self, collection_name: str):
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f"Deleting collection: {collection_name}")
                delete_table_sql = sql_text(f'DROP TABLE IF EXISTS {collection_name}')
                await session.execute(delete_table_sql)

                await session.commit()
        return True

    async def create_collection(self, collection_name: str , embedding_size:int,do_reset:bool=False):
        if do_reset:
            _ = await self.delete_collection(collection_name)

        is_collection_existed= await self.is_connection_exsited(collection_name)

        if not is_collection_existed:
            self.logger.info(f"creating collection: {collection_name}")

            async with self.db_client() as session:
                async with session.begin():
                    
                    create_table_sql = sql_text(f"""
                CREATE TABLE {collection_name} (
                    {PgvectorTableSchemeEnums.ID.value} BIGSERIAL PRIMARY KEY,
                    {PgvectorTableSchemeEnums.VECTOR.value} VECTOR({embedding_size}),
                    {PgvectorTableSchemeEnums.METADATA.value} JSONB DEFAULT \'{{}}\',
                    {PgvectorTableSchemeEnums.TEXT.value} TEXT,
                    {PgvectorTableSchemeEnums.CHUNK_ID.value} INTEGER,
                    FOREIGN KEY ({PgvectorTableSchemeEnums.CHUNK_ID.value}) REFERENCES chunks(chunk_id)

                )
                """)
                    await session.execute(create_table_sql)
                    await session.commit()
                
            return True

        return False   


    async def is_index_exsited(self,collection_name:str) -> bool:
        idx_name = self.defult_index_name(collection_name)
        async with self.db_client() as session:
            async with session.begin():
                idx = await session.execute(
                    sql_text('SELECT * FROM pg_indexes WHERE indexname = :idx_name AND tablename = :collection_name'),
                    {"idx_name": idx_name, "collection_name": collection_name}
                )
                record = idx.first()
                return bool(record)

    async def create_vector_index(self,collection_name:str,index_type : str = PgvectorIndexTypeEnums.HNSW.value ): 
        is_index_exsited = await self.is_index_exsited(collection_name)
        if is_index_exsited:
            self.logger.info(f"Index already exists for collection: {collection_name}")
            return False

        async with self.db_client() as session:
            async with session.begin():
                count_sql=sql_text(f"SELECT COUNT(*) FROM {collection_name}")
                result= await session.execute(count_sql)
                count=result.scalar_one()

                if count < self.index_threshold:
                    return False

                self.logger.info(f"Creating index for collection: {collection_name}")

                idx_name = self.defult_index_name(collection_name)
                create_index_sql = sql_text(f"""
                CREATE INDEX {idx_name} ON {collection_name} USING {index_type} ({PgvectorTableSchemeEnums.VECTOR.value} {self.distance_method})
                """)

                await session.execute(create_index_sql)
                await session.commit()

                self.logger.info(f"Index created for collection: {collection_name}")
                return True
                    

    async def reset_vector_index(self,collection_name:str,index_type:str=PgvectorIndexTypeEnums.HNSW.value)->bool:
        idx_name = self.defult_index_name(collection_name)


        async with self.db_client() as session:
            async with session.begin():
                delete_index_sql = sql_text(f"DROP INDEX {idx_name}")
                await session.execute(delete_index_sql)
                await session.commit()
                self.logger.info(f"Index reset for collection: {collection_name}")
                return await self.create_vector_index(collection_name,index_type)




    async def insert_one(self,collection_name:str,text:str,vector:list,metadata:dict=None,record_id:str=None):
        is_collection_existed = await self.is_connection_exsited(collection_name)
        if not is_collection_existed:
            self.logger.error(f"Collection {collection_name} does not exist")
            return False
        
        if not record_id:
            self.logger.error(f"Record id is required as i can't insert without chunk id in the collection {collection_name}")
            return False

        async with self.db_client() as session:
            async with session.begin():
                insert_sql = sql_text(f"""INSERT INTO {collection_name} (
                    {PgvectorTableSchemeEnums.VECTOR.value},
                    {PgvectorTableSchemeEnums.METADATA.value},
                    {PgvectorTableSchemeEnums.TEXT.value},
                    {PgvectorTableSchemeEnums.CHUNK_ID.value}
                ) VALUES (
                    :vector,
                    :metadata,
                    :text,
                    :chunk_id
                )""")

                await session.execute(insert_sql,{
                    "vector":"["+ ",".join([str(v) for v in vector]) +"]",
                    "metadata":json.dumps(metadata) if metadata is not None else '{}',
                    "text":text,
                    "chunk_id":record_id
                })

        await self.create_vector_index(collection_name)
                
        return True


    async def insert_many(self,collection_name:str,texts:list,vectors:list,metadatas:list=None,record_ids:list=None,batch_size:int=50):
        is_collection_existed = await self.is_connection_exsited(collection_name)
        if not is_collection_existed:
            self.logger.error(f"Collection {collection_name} does not exist")
            return False
        
        if len(texts) != len(vectors) or len(texts) != len(metadatas) or len(texts) != len(record_ids):
            self.logger.error(f"Texts, vectors, metadatas, and record_ids must have the same length")
            return False

        if not metadatas or len(metadatas)==0:
            metadatas=[None]*len(texts)
        

        async with self.db_client() as session:
            async with session.begin():
                for i in range(0,len(texts),batch_size):
                    batch_vectors =vectors[i:i+batch_size]
                    batch_metadatas = metadatas[i:i+batch_size]
                    batch_texts = texts[i:i+batch_size]
                    batch_record_ids = record_ids[i:i+batch_size]

                    values=[]
                    for _text,_vector,_metadata,_record_id in zip(batch_texts,batch_vectors,batch_metadatas,batch_record_ids):
                        values.append({
                            "vector":"["+ ",".join([str(v) for v in _vector]) + "]",
                            "metadata":json.dumps(_metadata) if _metadata is not None else '{}',
                            "text":_text,
                            "chunk_id":_record_id
                        })

                    insert_sql = sql_text(f"""INSERT INTO {collection_name}( 
                    {PgvectorTableSchemeEnums.VECTOR.value},
                    {PgvectorTableSchemeEnums.METADATA.value},
                    {PgvectorTableSchemeEnums.TEXT.value},
                    {PgvectorTableSchemeEnums.CHUNK_ID.value}  )
                 VALUES (:vector,:metadata,:text,:chunk_id)""")

                    await session.execute(insert_sql,values)

        await self.create_vector_index(collection_name)
                
        return True

    async def search_by_vector(self,collection_name:str,vector:list,limit:int=5):
        is_collection_existed = await self.is_connection_exsited(collection_name)
        if not is_collection_existed:
            self.logger.error(f"Collection {collection_name} does not exist")
            return False

        vector_sql = "["+ ",".join([str(v) for v in vector]) + "]"

        async with self.db_client() as session:
            async with session.begin():
                search_sql = sql_text(f"""SELECT {PgvectorTableSchemeEnums.TEXT.value} as text,
                (1 - ({PgvectorTableSchemeEnums.VECTOR.value} <=> :vector)) as score
                FROM {collection_name}
                ORDER BY score DESC
                LIMIT :limit""")

                result = await session.execute(search_sql,{"vector":vector_sql,"limit":limit})
                records = result.fetchall()
                return [
                    RetrivedDocument(
                        text=record.text,
                        score=record.score
                    ) for record in records
                ]
        