from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from okcupyd.db import Base, OKCBase


class Question(OKCBase):

    __tablename__ = 'question'

    text = Column(String, nullable=False)


class UserQuestionAnswerOption(Base):

    user_id = Column(Integer, ForeignKey("user.id"))
