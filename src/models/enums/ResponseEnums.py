from enum import Enum

class ResponseSignal(Enum):
    
    FILE_VALIDATED_SUCCESS ="file validated success"
    FILE_TYPE_NOT_SUPPORTED = "file_type not supported "
    FILE_SIZE_EXCEDED ="file size excedded"
    FILE_UPLOAD_SUCCESS = "file upload success"
    FILE_UPLOAD_FAILED = "file upload failed"

    DATA_UPLOADED_SUCCESS = "data uploaded success"

    FILE_PROCESSING_FAILED = "file processing failed"

    FILE_PROCESSING_SUCCESS = "file processing success"

    FILE_ID_ERROR = "file id is invalid"

    PROJECT_ID_ERROR = "project id is invalid"

    INSERT_INTO_VECTOR_DB_ERROR = "insert into vector db error"
    INSERT_INTO_VECTOR_DB_SUCCESS = "insert into vector db success"

    VECTOR_DB_COLLECTION_RETRIEVED = "vector db collection retrieved" 

    SEARCH_IN_VECTOR_DB_SUCCESS = "search in vector db success"

    SEARCH_IN_VECTOR_DB_ERROR = "search in vector db error"

    ANSWER_RAG_QUESTION_SUCCESS = "answer rag question success"
    ANSWER_RAG_QUESTION_ERROR = "answer rag question error"
