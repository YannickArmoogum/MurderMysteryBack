"""
    Aim here is to build a facade singleton DB_manager to hide complexity of sql statements and avoid creating a db instancec for each connection
    DB instance can be instatiated at LifeSpan fastapi and persists across lifetime of application
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


class DbManager:
    #Here it is an attribute that is not dependant of the class and will be shared and persists independently if class is initialised or not
    _instance = None
    """
        New is the stp that handles creation of class instance
    """
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance =super().__new__(cls) #creates new class instance
        return cls._instance
    """
        Init the step attributes and class are initialised values are passed
    """
    def __init__(self,url):
        self.engine =  create_engine(url=url)
        self._Session = sessionmaker(bind=self.engine) #This returns the factory object of the session not yet the actual object

    def get_session(self) -> Session:
        return self._Session()
