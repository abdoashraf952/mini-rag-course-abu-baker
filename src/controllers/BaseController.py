from helpers.config import get_settings , Settings
import os
import random
import string

class BaseController:
    def __init__(self) -> None:
        self.settings : Settings = get_settings()
        self.base_dir : str = os.path.dirname(os.path.dirname(__file__))
        self.file_dir : str = os.path.join(self.base_dir,"assets","files")
        self.datase_dir : str = os.path.join(self.base_dir,"assets","datase")
        

    def generate_random_string(self,length:int=16) -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

        
    def get_database_path(self,db_name:str):
        database_full_path = os.path.join(self.datase_dir,db_name)
        if not os.path.exists(database_full_path):
            os.makedirs(database_full_path)
        return database_full_path
        