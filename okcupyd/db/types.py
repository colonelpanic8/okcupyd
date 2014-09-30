from sqlalchemy.types import TypeDecorator, VARCHAR
import simplejson


class JSONType(TypeDecorator):

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = simplejson.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = simplejson.loads(value)
        return value


class StringBackedInteger(TypeDecorator):

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return int(value)