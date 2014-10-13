from okcupyd import magicnumbers


def test_yield_exponents_of_two():
    assert list(magicnumbers.yield_exponents_of_two(32 + 16)) == [4, 5]
    assert list(magicnumbers.yield_exponents_of_two(1)) == [0]
    assert list(magicnumbers.yield_exponents_of_two(2)) == [1]
    assert list(magicnumbers.yield_exponents_of_two(2+8)) == [1, 3]


def test_get_kids_query_with_both_specified():
    assert magicnumbers.get_kids_int(["has a kid"], ["might want kids",
                                                     "doesn't want kids",
                                                     "wants kids"]) == 33686016
    assert magicnumbers.get_kids_int(["has a kid"], ["might want kids"]) == 512
    assert magicnumbers.get_kids_int(["has a kid", "has kids"],
                                     ["might want kids"]) == 1536
    assert magicnumbers.get_kids_int(["has a kid", "has kids"], []) == 101058054
    assert magicnumbers.get_kids_int(["has a kid", "has kids"],
                                     ["doesn't want kids"]) == 100663296

def test_get_kids_query_when_has_not_specified():
    magicnumbers.get_kids_int([], ['wants kids']) == 4653056
    assert magicnumbers.get_kids_int([], ["doesn't want kids",
                                          "wants kids"]) == 1195835440
    assert magicnumbers.get_kids_int([], ["might want kids",
                                          "doesn't want kids"]) == 1191200560
    assert magicnumbers.get_kids_int([], ["might want kids",
                                          "doesn't want kids",
                                          "wants kids"]) == 1195853616
    assert magicnumbers.get_kids_int([], ["might want kids",
                                          "wants kids"]) == 4671232
    assert magicnumbers.get_kids_int([], ["might want kids"]) == 18176


def test_get_kids_int_when_wants_not_specified():
    assert magicnumbers.get_kids_int(["has a kid"], []) == 33686018
    assert magicnumbers.get_kids_int(["has a kid", "has kids"], []) == 101058054


def test_get_kids_int_with_all():
    assert magicnumbers.get_kids_int(
        ["has a kid",
         "has kids",
         "doesn't have kids"],
        ["might want kids",
         "doesn't want kids",
         "wants kids"]
    ) == 1179010560


def test_bodytype():
    magicnumbers.filters.bodytype('thin') == 30,4
    magicnumbers.filters.bodytype(['thin', 'jacked']) == '30,260'
