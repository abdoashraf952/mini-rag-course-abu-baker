from helpers.config import get_settings , Settings
import os
import random
import string

class BaseController:
    def __init__(self) -> None:
        self.settings : Settings = get_settings()
        self.base_dir : str = os.path.dirname(os.path.dirname(__file__))
        self.file_dir : str = os.path.join(self.base_dir,"assets","files")

    def generate_random_string(self,length:int=16) -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

        