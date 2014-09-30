from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

from okcupyd.db import Base, OKCBase


class User(OKCBase):

    __tablename__ = 'user'

    handle = Column(String, nullable=False)
    age = Column(String, nullable=False)
    location = Column(String, nullable=False)


class OKCupydUser(Base):

    __tablename__ = 'okcupyd_user'

    inbox_last_updated = Column(DateTime, nullable=True)
    outbox_last_updated = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", foreign_keys=[user_id],
                        backref=backref('okcupyd_user', uselist=False))
