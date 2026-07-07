from pydantic import BaseModel , Field ,validator
from typing import Optional
from bson.objectid import ObjectId

class Project(BaseModel):
    _id :Optional[str]
    Project_id : str = Field(...,min_length=1)

    @validator('Project_id')
    def validate_Project_id(cls , v):
        if  not v.isalnum():
            raise ValueError('Project_id must be alphanumeric')
        
        return v


    class Config:
        arbitrary_types_allowed = True
        
        

