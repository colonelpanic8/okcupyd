import logging
import os

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import ColumnProperty, Query, class_mapper, sessionmaker
from sqlalchemy.sql import func
from wrapt import decorator

from . import types


log = logging.getLogger(__name__)


class Query(Query):
    pass


echo = False


engine = create_engine('sqlite://', convert_unicode=True, echo=True)
Session = sessionmaker(
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
    query_cls=Query
)


class txn(object):

    def __init__(self, session_class=None):
        self.session_class = session_class or Session

    def __call__(self, func):
        def wrapped(*args, **kwargs):
            with self:
                return func(self.session, *args, **kwargs)
        return wrapped

    def __enter__(self):
        self.session = self.session_class()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.session.rollback()

            if isinstance(exc_val, Exception):
                raise
            else:
                raise exc_type(exc_val)
        else:
            self.session.commit()
            self.session.close()


@decorator
def with_txn(function, instance, args, kwargs):
    with txn() as session:
        return function(session, *args, **kwargs)


class Base(object):

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False, default=func.now())

    def upsert_model(self, id_key='id'):
        return self.upsert([self], id_key=id_key)

    @classmethod
    def columns(cls):
        return [prop for prop in class_mapper(cls).iterate_properties
                if isinstance(prop, ColumnProperty)]

    @classmethod
    def upsert_no_txn(cls, session, models, id_key='id'):
        ids_to_look_for = [getattr(model, id_key) for model in models]
        found_models = cls.find_all_no_txn(session, ids_to_look_for,
                                           id_key=id_key)
        id_to_model = {getattr(model, id_key): model for model in found_models}
        try:
            key_type = type(next(iter(id_to_model.keys())))
        except:
            key_type = int
        for model in models:
            model_id = key_type(getattr(model, id_key))
            if model_id in id_to_model:
                # Get the primary key in a better way here
                model.id = id_to_model[model_id].id
                session.merge(model)
            else:
                id_to_model[model_id] = model
                session.add(model)
        log.info(id_to_model)
        return id_to_model

    @classmethod
    def upsert_one_no_txn(cls, session, model, **kwargs):
        return next(iter(cls.upsert_no_txn(session, [model], **kwargs).values()))

    upsert = with_txn(upsert_no_txn)

    @classmethod
    def safe_upsert(cls, *args, **kwargs):
        # TODO(imalison): use a retry decorator here.
        try:
            return cls.upsert(*args, **kwargs)
        except IntegrityError:
            return cls.upsert(*args, **kwargs)

    @classmethod
    def upsert_okc(cls, model, **kwargs):
        return next(iter(cls.safe_upsert([model], id_key='okc_id').values()))

    @classmethod
    def find_all_no_txn(cls, session, identifiers, id_key='id'):
        return cls.find_query(session, identifiers, id_key=id_key).all()

    find_all = with_txn(find_all_no_txn)

    @classmethod
    def find_no_txn(cls, session, identifier, id_key='id'):
        return cls.find_query(session, [identifier], id_key=id_key).one()

    find = with_txn(find_no_txn)

    @classmethod
    def query_no_txn(cls, session, *args, **kwargs):
        if not kwargs and len(args) == 1 and isinstance(args[0], (int, str)):
            args = cls.id == args[0],
        return cls.build_query(session, *args, **kwargs).all()

    query = with_txn(query_no_txn)

    @classmethod
    def find_query(cls, session, identifiers, id_key='id'):
        return session.query(cls).filter(getattr(cls, id_key).in_(identifiers))

    @classmethod
    def build_query(cls, session, *args, **kwargs):
        return session.query(cls).filter(*args).filter_by(**kwargs)


Base = declarative_base(engine, cls=Base)


class OKCBase(Base):

    __abstract__ = True

    okc_id = Column(types.StringBackedInteger, nullable=False, unique=True)


def reset_engine(engine):
    Session.configure(bind=engine)
    Base.metadata.bind = engine
    return engine


def set_sqlite_db_file(file_path):
    return reset_engine(create_engine('sqlite:///{0}'.format(file_path),
                                      convert_unicode=True,
                                      echo=echo))


database_uri = os.path.join(os.path.dirname(__file__), 'okcupyd.db')
set_sqlite_db_file(database_uri)
