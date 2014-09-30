from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import relationship
from sqlalchemy.ext.orderinglist import ordering_list

from okcupyd.db import OKCBase


class MessageThread(OKCBase):

    __tablename__ = "message_thread"

    initiator_id = Column(Integer, ForeignKey("user.id"))
    initiator = relationship("User", foreign_keys=[initiator_id])

    respondent_id = Column(Integer, ForeignKey("user.id"))
    respondent = relationship("User", foreign_keys=[respondent_id])

    messages = relationship("Message", order_by="Message.thread_index",
                            collection_class=ordering_list('thread_index'),
                            backref='message_thread')
