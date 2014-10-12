from okcupyd.search import search_filters


def test_a_bunch_of_filters():
    search_filters.build(religion='buddhist',
                         height_min=66, height_max=68, gentation='everybody',
                         smokes=['no', 'trying to quit'], age_min=18, age_max=24,
                         radius=12, last_online=1234125,
                         status='single', drugs=['very_often', 'sometimes'],
                         job=['retired'], education_level=['high school'],
                         income='less than $20,000', monogamy='monogamous',
                         diet='vegan', ethnicities=['asian', 'middle eastern'],
                         cats=['likes cats'], dogs=['has dogs'], has_kids='has a kid')


def test_empty_string_gentation():
    search_filters.build(gentation='')
