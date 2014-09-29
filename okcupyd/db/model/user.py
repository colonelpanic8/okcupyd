from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from okcupyd.db import Base


class User(Base):

    __tablename__ = "user"

    okc_id = Column(Integer, unique=True)

    handle = Column(String, nullable=False)
    age = Column(String, nullable=False)
    location = Column(String, nullable=False)
