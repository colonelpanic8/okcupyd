from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

from okcupyd.db import Base, OKCBase


class User(OKCBase):

    __tablename__ = 'user'

    @classmethod
    def from_profile(cls, profile):
        return cls(okc_id=profile.id, handle=profile.username, age=profile.age,
                   location=profile.location)

    handle = Column(String, nullable=False)
    age = Column(String, nullable=False)
    location = Column(String, nullable=False)


class OKCupydUser(Base):

    __tablename__ = 'okcupyd_user'

    inbox_last_updated = Column(DateTime, nullable=True)
    outbox_last_updated = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True)
    user = relationship("User", foreign_keys=[user_id],
                        backref=backref('okcupyd_user', uselist=False))
