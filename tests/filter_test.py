from okcupyd.filter import Filters


def test_a_bunch_of_filters():
    filters = Filters(location='new york, ny', religion='buddhist',
                      height_min=66, height_max=68, gentation='everybody',
                      smokes=['no', 'trying to quit'], age_min=18, age_max=24,
                      radius=12, order_by='MATCH', last_online=1234125,
                      status='single', drugs=['very_often', 'sometimes'],
                      job=['retired'], education=['high school'],
                      income='less than $20,000', monogomy='monogamous',
                      diet='vegan', ethnicity=['asian', 'middle eastern'],
                      pets=['owns dogs', 'likes cats'], kids=['has a kid'])

    # Just an acceptance test for now.
    filters.build()


def test_empty_string_gentation():
    Filters(gentation='').build()
