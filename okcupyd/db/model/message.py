from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from okcupyd.db import Base


class Message(Base):

    __tablename__ = "message"

    __table_args__ = (
        UniqueConstraint('message_thread_id', 'thread_index'),
    )

    okc_id = Column(Integer, unique=True)

    message_thread_id = Column(Integer, ForeignKey("message_thread.id"),
                               nullable=False)

    sender_id = Column(Integer, ForeignKey("user.id"))
    sender = relationship("User", foreign_keys=[sender_id])

    recipient_id = Column(Integer, ForeignKey("user.id"))
    recipient = relationship("User", foreign_keys=[recipient_id])

    text = Column(String, nullable=False)
    thread_index = Column(Integer, nullable=False)
