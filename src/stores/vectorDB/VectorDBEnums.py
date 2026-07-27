from enum import Enum

class VectorDBEnums( Enum):
    QDRANT = "QDRANT"
    PGVECTOR = "PGVECTOR"

class DistanceMethodEnums( Enum):
    COSINE = "COSINE"
    DOT = "DOT"
    EUCLIDEAN = "EUCLIDEAN"

class PgvectorTableSchemeEnums(Enum):
    ID="id"
    TEXT="text"
    METADATA="metadata"
    VECTOR="vector"
    CHUNK_ID='chunk_id'
    _PREFIX = 'pgvector'

class PgvectorDistanceMethodEnums(Enum):
    COSINE='vector_cosine_ops'
    DOT = 'vector_l2_ops'

class PgvectorIndexTypeEnums(Enum):
    HNSW='hnsw'
    IVFFLAT='ivfflat'
    