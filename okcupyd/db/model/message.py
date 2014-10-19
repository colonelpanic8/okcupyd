from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from okcupyd.db import OKCBase


class Message(OKCBase):

    __tablename__ = "message"

    __table_args__ = (
        UniqueConstraint('message_thread_id', 'thread_index'),
    )

    time_sent = Column(DateTime, nullable=True)

    message_thread_id = Column(Integer, ForeignKey("message_thread.id"),
                               nullable=False)

    sender_id = Column(Integer, ForeignKey("user.id"))
    sender = relationship("User", foreign_keys=[sender_id],
                          backref='sent_messages')

    recipient_id = Column(Integer, ForeignKey("user.id"))
    recipient = relationship("User", foreign_keys=[recipient_id],
                             backref='received_messages')

    text = Column(String, nullable=False)
    thread_index = Column(Integer, nullable=False)
