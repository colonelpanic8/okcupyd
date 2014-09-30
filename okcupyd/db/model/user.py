from sqlalchemy import Column
from sqlalchemy import String

from . import OKCBase


class User(OKCBase):

    __tablename__ = "user"

    handle = Column(String, nullable=False)
    age = Column(String, nullable=False)
    location = Column(String, nullable=False)
