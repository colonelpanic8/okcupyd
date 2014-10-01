import datetime
import logging

from lxml import html
import simplejson

from . import helpers
from . import util
from .question import QuestionFetcher
from .xpath import xpb


log = logging.getLogger(__name__)


class LookingFor(object):

    _looking_for_xpb = xpb.div.with_classes('text', 'what_i_want')

    def __init__(self, profile_tree_owner):
        self._profile_tree_owner

    @util.cached_property
    def raw_fields(self):
        li_elements = self._looking_for_xpb.li.apply_(
            self._profile_tree_owner._profile_tree
        )
        return {li.attrib['id'].split('_')[1]: li.text_content()
                for li in li_elements}

    @util.cached_property
    def ages(self):
        return self.raw_fields.get('ages')

    @util.cached_property
    def single(self):
        return bool(self.raw_fields.get('ages', None))

    @util.cached_property
    def near_me(self):
        return 'near' in self.raw_field.get('near', '').lower()

    @util.cached_property
    def looking_for(self):
        return 'near' in self.raw_field.get('near', '').lower()


class Essays(object):

    @staticmethod
    def build_essay_property(essay_index, essay_name):
        essay_xpb = xpb.div(id='essay_{0}'.format(essay_index))
        essay_text_xpb = essay_xpb.div.with_class('text').div.with_class('essay')
        @property
        def essay(self):
            try:
                essay_text = essay_text_xpb.get_text_(self._essays).strip()
            except IndexError:
                return None
            if essay_name not in self._short_name_to_title:
                self._short_name_to_title[essay_name] = helpers.replace_chars(
                    essay_xpb.a.with_class('essay_title').get_text_(
                        self._profile_tree
                    )
                )
            return essay_text

        @essay.setter
        def set_essay_text(self, essay_text):
            self._submit_essay(essay_index, essay_text)

        return set_essay_text

    @classmethod
    def _init_essay_properties(cls):
        for essay_index, essay_name in enumerate(cls.essay_names):
            setattr(cls, essay_name,
                    cls.build_essay_property(essay_index, essay_name))

    _essays_xpb = xpb.div(id='main_column')
    essay_names = ['self_summary', 'my_life', 'good_at', 'people_first_notice',
                   'favorites', 'six_things', 'think_about', 'friday_night',
                   'private_admission', 'message_me_if']

    def __init__(self, session, profile_tree, profile_tree_getter=None):
        self._session = session
        self._profile_tree = profile_tree
        self._profile_tree_getter = profile_tree_getter
        self._short_name_to_title = {}

    @property
    def short_name_to_title(self):
        for i in self: pass # Make sure that all essays names have been retrieved
        return self._short_name_to_title

    @util.cached_property
    def _essays(self):
        return self._essays_xpb.one_(self._profile_tree)

    @util.cached_property
    def _authcode(self):
        return helpers.get_authcode(self._profile_tree)

    def _submit_essay(self, essay_id, essay_body):
        self._session.post('https://www.okcupid.com/profileedit2', data={
            "essay_id": essay_id,
            "essay_body": essay_body,
            "authcode": self._authcode,
            "okc_api": 1
        })
        self.refresh()

    def refresh(self, profile_tree=None):
        if profile_tree is None:
            assert self._profile_tree_getter, (
                "Must provide a profile_tree or a profile_tree_getter"
            )
            self._profile_tree = self._profile_tree_getter()
        util.cached_property.bust_caches(self)

    def __iter__(self):
        for essay_name in self.essay_names:
            yield getattr(self, essay_name)


Essays._init_essay_properties()


class Profile(object):

    def __init__(self, session, username, **kwargs):
        self._session = session
        self.username = username
        self._question_fetcher = QuestionFetcher(session, username,
                                                 is_user=self.is_logged_in_user)
        self.questions = util.Fetchable(self._question_fetcher)

    def refresh(self, reload=True):
        util.cached_property.bust_caches(self)
        if reload:
            return self._profile_tree

    @property
    def is_logged_in_user(self):
        return self._session.log_in_name.lower() == self.username.lower()

    @util.cached_property
    def _profile_response(self):
        return self._session.get(
            'https://www.okcupid.com/profile/{0}'.format(self.username)
        ).content

    @util.cached_property
    def _profile_tree(self):
        return html.fromstring(self._profile_response)

    def message_request_parameters(self, content, thread_id):
        return {
            'ajax': 1,
            'sendmsg': 1,
            'r1': self.username,
            'body': content,
            'threadid': thread_id,
            'authcode': self.authcode,
            'reply': 1 if thread_id else 0,
            'from_profile': 1
        }

    @util.cached_property
    def authcode(self):
        return helpers.get_authcode(self._profile_tree)

    @util.cached_property
    def picture_uris(self):
        pics_request = self._session.okc_get(
            'profile/{0}/photos?cf=profile'.format(self.username)
        )
        pics_tree = html.fromstring(pics_request.content.decode('utf8'))
        return xpb.div(id='album_0').img.select_attribute_('src', pics_tree)

    _rating_xpb = xpb.div(id='rating').ul(id='personality-rating').li.\
                  with_class('current-rating')

    @util.cached_property
    def rating(self):
        if self.is_logged_in_user: return 0
        rating_style = self._rating_xpb.select_attribute_('style').one_(
            self._profile_tree
        )
        width_percentage = int(''.join(c for c in rating_style if c.isdigit()))
        return width_percentage // 20

    _contacted_xpb = xpb.div(id='actions').div.with_classes('tooltip_text',
                                                               'hidden')

    @util.cached_property
    def contacted(self):
        try:
            contacted_span = self._contacted_xpb.span.with_class('fancydate').\
                             one_(self._profile_tree)
        except:
            return False
        else:
            timestamp = contacted_span.attrib['id'].split('_')[-1][:-2]
            return datetime.datetime.fromtimestamp(int(timestamp[:10]))

    @util.cached_property
    def responds(self):
        contacted_text = self._contacted_xpb.get_text_(self._profile_tree).lower()
        if 'contacted' not in contacted_text:
            return contacted_text.strip().replace('replies ', '')

    @util.cached_property
    def id(self):
        if self.is_logged_in_user: return self._current_user_id
        return int(self._rating_xpb.select_attribute_('id').
                   one_(self._profile_tree).split('-')[-2])

    @util.cached_property
    def _current_user_id(self):
        return int(helpers.get_id(self._profile_tree))

    @util.cached_property
    def essays(self):
        return Essays(self._session, self._profile_tree,
                      profile_tree_getter=self.refresh)

    @util.cached_property
    def age(self):
        return int(xpb.span(id='ajax_age').get_text_(self._profile_tree).strip())

    _percentages_and_ratings_xpb = xpb.div(id='percentages_and_ratings')

    @util.cached_property
    def match_percentage(self):
        return int(self._percentages_and_ratings_xpb.
                   div.with_class('match').
                   span.with_class('percent').
                   get_text_(self._profile_tree).strip('%'))

    @util.cached_property
    def enemy_percentage(self):
        return int(self._percentages_and_ratings_xpb.
                   div.with_class('enemy').
                   span.with_class('percent').
                   get_text_(self._profile_tree).strip('%'))

    @util.cached_property
    def location(self):
        return xpb.span(id='ajax_location').get_text_(self._profile_tree)

    @util.cached_property
    def gender(self):
        return xpb.span(id='ajax_gender').get_text_(self._profile_tree)

    @util.cached_property
    def orientation(self):
        return xpb.dd(id='ajax_orientation').get_text_(self._profile_tree).strip()

    _details_xpb = xpb.div(id='profile_details')

    @util.cached_property
    def details(self):
        details = {}
        details_div = self._details_xpb.one_(self._profile_tree)
        for dl in details_div.iter('dl'):
            title = dl.find('dt').text
            item = dl.find('dd')
            if title == 'Last Online' and item.find('span') is not None:
                details[title.lower()] = item.find('span').text.strip()
            elif title.lower() in details and len(item.text):
                details[title.lower()] = item.text.strip()
            else:
                continue
            details[title.lower()] = helpers.replace_chars(details[title.lower()])
        return details

    @util.n_partialable
    def message(self, message, thread_id=None):
        return_value =  helpers.Messager(
            self._session
        ).send(self.username, message,
                       self.authcode, thread_id)
        self.refresh(reload=False)
        return return_value

    @util.cached_property
    def attractiveness(self):
        from .attractiveness_finder import AttractivenessFinder
        return AttractivenessFinder(self._session)(self.username)

    def rate(self, rating):
        parameters = {
            'voterid': self._current_user_id,
            'target_userid': self.id,
            'type': 'vote',
            'cf': 'profile2',
            'target_objectid': 0,
            'vote_type': 'personality',
            'score': rating,
        }
        headers = {
            'accept': 'text/javascript, text/html, application/xml, '
            'text/xml, */*',
            'accept-encoding': 'gzip,deflate',
            'accept-language': 'en-US,en;q=0.8',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.okcupid.com',
            'x-prototype-version': 1.7,
            'x-requested-with': 'XMLHttpRequest',
        }
        response = self._session.okc_post('vote_handler', data=parameters,
                                          headers=headers)
        response_json = response.json()
        log_function = log.info if response_json.get('status', False) \
                       else log.error
        log_function(simplejson.dumps({'rate_response': response_json,
                                       'sent_parameters': parameters,
                                       'headers': dict(self._session.headers)}))
        self.refresh(reload=False)

    def __eq__(self, other):
        self.username.lower() == other.username.lower()

    def __repr__(self):
        return 'Profile("{0}")'.format(self.username)
