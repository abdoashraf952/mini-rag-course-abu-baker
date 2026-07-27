from helpers.config import Settings,get_settings


class BaseDataModel:

    def __init__(self,db_client : object):
        self.db = db_client
        self.settings = get_settings()



        
