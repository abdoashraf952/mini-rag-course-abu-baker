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
