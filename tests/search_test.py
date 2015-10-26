import operator

import mock
import pytest

from okcupyd import User
from okcupyd import magicnumbers
from okcupyd.magicnumbers import maps
from okcupyd.profile import Profile
from okcupyd.json_search import SearchFetchable, search
from okcupyd.location import LocationQueryCache
from okcupyd.session import Session

from . import util


SEARCH_FILTERS_BEING_REIMPLEMENTED = "SEARCH_FILTERS_ARE_BEING_REIMPLEMENTED"


@util.use_cassette
def test_age_filter():
    age = 22
    search_fetchable = SearchFetchable(gentation='everybody',
                                       minimum_age=age, maximum_age=age)
    for profile in search_fetchable[:5]:
        assert profile.age == age


@util.use_cassette
def test_count_variable(request):
    profiles = search(gentation='everybody', count=14)
    assert len(profiles) == 14

    for profile in profiles:
        profile.username
        profile.age
        profile.location
        profile.match_percentage
        profile.enemy_percentage
        profile.id
        profile.rating
        profile.contacted


@util.use_cassette
def test_location_filter():
    session = Session.login()
    location_cache = LocationQueryCache(session)
    location = 'Portland, OR'
    search_fetchable = SearchFetchable(location=location, location_cache=location_cache, radius=1)
    for profile in search_fetchable[:5]:
        assert profile.location == 'Portland, OR'


@util.use_cassette(path='search_function')
def test_search_function():
    profile, = search(count=1)
    assert isinstance(profile, Profile)

    profile.username
    profile.age
    profile.location
    profile.match_percentage
    profile.enemy_percentage
    profile.id
    profile.rating
    profile.contacted


@pytest.mark.xfail(reason=SEARCH_FILTERS_BEING_REIMPLEMENTED)
@util.use_cassette
def test_search_fetchable_iter():
    search_fetchable = SearchFetchable(gentation='everybody',
                                       religion='buddhist', age_min=25, age_max=25,
                                       location='new york, ny', keywords='bicycle')
    for count, profile in enumerate(search_fetchable):
        assert isinstance(profile, Profile)
        if count > 30:
            break


@pytest.mark.xfail(reason=SEARCH_FILTERS_BEING_REIMPLEMENTED)
@util.use_cassette
def test_easy_search_filters():
    session = Session.login()
    query_test_pairs = [# ('bodytype', maps.bodytype),
                        # TODO(@IvanMalison) this is an alist feature,
                        # so it can't be tested for now.
                        ('drugs', maps.drugs), ('smokes', maps.smokes),
                        ('diet', maps.diet,), ('job', maps.job)]
    for query_param, re_map in query_test_pairs:
        for value in sorted(re_map.pattern_to_value.keys()):
            profile = SearchFetchable(**{
                'gentation': '',
                'session': session,
                'count': 1,
                query_param: value
            })[0]
            attribute = getattr(profile.details, query_param)
            assert value in (attribute or '').lower()


@pytest.mark.xfail(reason=SEARCH_FILTERS_BEING_REIMPLEMENTED)
@util.use_cassette
def test_children_filter():
    session = Session.login()
    profile = SearchFetchable(session, wants_kids="wants kids", count=1)[0]
    assert "wants" in profile.details.children.lower()

    profile = SearchFetchable(session, has_kids=["has kids"],
                              wants_kids="doesn't want kids",
                              count=0)[0]
    assert "has kids" in profile.details.children.lower()
    assert "doesn't want" in profile.details.children.lower()


@pytest.mark.xfail(reason=SEARCH_FILTERS_BEING_REIMPLEMENTED)
@util.use_cassette
def test_pets_queries():
    session = Session.login()
    profile = SearchFetchable(session, cats=['dislikes cats', 'likes cats'],
                              count=1)[0]
    assert 'likes cats' in profile.details.pets.lower()

    profile = SearchFetchable(session, dogs='likes dogs', cats='has cats', count=1)[0]

    assert 'likes dogs' in profile.details.pets.lower()
    assert 'has cats' in profile.details.pets.lower()


@pytest.mark.xfail(reason=SEARCH_FILTERS_BEING_REIMPLEMENTED)
@util.use_cassette
def test_height_filter():
    session = Session.login()
    profile = SearchFetchable(session, height_min='5\'6"', height_max='5\'6"',
                              gentation='girls who like guys', radius=25, count=1)[0]
    match = magicnumbers.imperial_re.search(profile.details.height)
    assert int(match.group(1)) == 5
    assert int(match.group(2)) == 6

    profile = SearchFetchable(session, height_min='2.00m', count=1)[0]
    match = magicnumbers.metric_re.search(profile.details.height)
    assert float(match.group(1)) >= 2.00

    profile = SearchFetchable(session, height_max='1.5m', count=1)[0]
    match = magicnumbers.metric_re.search(profile.details.height)
    assert float(match.group(1)) <= 1.5


@pytest.mark.xfail(reason=SEARCH_FILTERS_BEING_REIMPLEMENTED)
@util.use_cassette
def test_language_filter():
    session = Session.login()
    profile = SearchFetchable(session, language='french', count=1)[0]
    assert 'french' in [language_info[0].lower()
                        for language_info in profile.details.languages]

    profile = SearchFetchable(session, language='Afrikaans', count=1)[0]
    assert 'afrikaans' in map(operator.itemgetter(0), profile.details.languages)


@pytest.mark.xfail
@util.use_cassette
def test_attractiveness_filter():
    session = Session.login()
    profile = SearchFetchable(session, attractiveness_min=4000,
                              attractiveness_max=6000, count=1)[0]

    assert profile.attractiveness > 4000
    assert profile.attractiveness < 6000


@pytest.mark.xfail
@util.use_cassette
def test_question_filter():
    user = User()
    user_question = user.questions.somewhat_important[0]
    for profile in user.search(question=user_question)[:5]:
        question = profile.find_question(user_question.id)
        assert question.their_answer_matches


@pytest.mark.xfail
@util.use_cassette
def test_question_filter_with_custom_answers():
    user = User()
    user_question = user.questions.somewhat_important[1]
    unacceptable_answers = [answer_option.id
                            for answer_option in user_question.answer_options
                            if not answer_option.is_match]
    for profile in user.search(question=user_question.id,
                               question_answers=unacceptable_answers)[:5]:
        question = profile.find_question(user_question.id)
        assert not question.their_answer_matches


@pytest.mark.xfail
@util.use_cassette
def test_question_count_filter():
    user = User()
    for profile in user.search(question_count_min=250)[:5]:
        assert profile.questions[249]


@pytest.mark.xfail(reason="ProfileBuilder needs to be improved to actually get data from profile results")
@util.use_cassette
def test_search_populates_upfront():
    user = User()
    search_fetchable = user.search()
    for profile in search_fetchable[:4]:
        profile_session = profile._session
        with mock.patch.object(profile, '_session') as mock_session:
            mock_session.okc_get.side_effect = profile_session.okc_get
            assert profile.id > 0
            assert mock_session.okc_get.call_count == 0
            profile.essays.self_summary
            assert mock_session.okc_get.call_count == 1
