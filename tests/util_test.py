from pyokc import util


@util.n_partialable
def crazy(a, self):
    return a + self.starter


class HasPartialableMethods(object):

    def __init__(self, starter):
        self.starter = starter
        self.on_instance = crazy

    @util.n_partialable
    def partialable(self, x, y=0):
        return self.starter * x * y

    on_class = crazy(1)


def test_partialable_method_behavior():
    assert HasPartialableMethods(2).partialable(y=2)(1) == 4
    hpm = HasPartialableMethods(2)
    assert hpm.on_instance(2, hpm) == 4
    assert hpm.on_class() == 3
