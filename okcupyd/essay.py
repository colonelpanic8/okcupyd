from . import util
from . import helpers
from .xpath import xpb


class Essays(object):
    """Interface to reading and writing essays."""

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
                        self._profile.profile_tree
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
    #: A list of the attribute names that are used to store the text of
    #: of essays on instances of this class.
    essay_names = ['self_summary', 'my_life', 'good_at', 'people_first_notice',
                   'favorites', 'six_things', 'think_about', 'friday_night',
                   'private_admission', 'message_me_if']

    def __init__(self, profile):
        """:param profile: A :class:`.Profile`"""
        self._profile = profile
        self._short_name_to_title = {}

    @property
    def short_name_to_title(self):
        for i in self: pass # Make sure that all essays names have been retrieved
        return self._short_name_to_title

    @util.cached_property
    def _essays(self):
        return self._essays_xpb.one_(self._profile.profile_tree)

    def _submit_essay(self, essay_id, essay_body):
        self._profile.authcode_post('profileedit2', data={
            "essay_id": essay_id,
            "essay_body": essay_body,
            "okc_api": 1
        })
        self.refresh()

    def refresh(self):
        self._profile.refresh()
        util.cached_property.bust_caches(self)

    def __iter__(self):
        for essay_name in self.essay_names:
            yield getattr(self, essay_name)


Essays._init_essay_properties()
