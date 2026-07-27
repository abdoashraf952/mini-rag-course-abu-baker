from dns import tsigkeyring
import os 

class TemplateParser:
    
    def __init__(self, language:str=None,default_lang:str="en"):
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.language = language
        self.default_lang = default_lang

    def set_language(self,language:str):
        if not language :
            self.language = self.default_lang
        
        language_path = os.path.join(self.current_path,"locales",language)
        if not os.path.exists(language_path):
            self.language = self.language

        else:
            self.language = self.default_lang

    def get(self, group: str, key: str, vars: dict = {}):

        if not group or not key:
            return None

        group_path = os.path.join(self.current_path, "locales", self.language, f"{group}.py")
        target_language = self.language

        if not os.path.exists(group_path):
            group_path = os.path.join(self.current_path, "locales", self.default_lang, f"{group}.py")
            target_language = self.default_lang

        if not os.path.exists(group_path):
            return None

        module = __import__(f"stores.llm.templates.locales.{target_language}.{group}", fromlist=[group])
        if not module:
            return None

        if not hasattr(module, key):
            return None

        key_attribute = getattr(module, key)
        return key_attribute.substitute(vars)
            
        
        
        

        
        
            
    
    
        
        
        
        