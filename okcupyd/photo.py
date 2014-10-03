import logging
import re

from lxml import html
import simplejson

from . import util
from . import helpers
from .session import Session
from .xpath import xpb


log = logging.getLogger(__name__)


@util.n_partialable
class PhotoUploader(object):

    _uri = 'ajaxuploader'

    def __init__(self, session=None, user_id=None, authcode=None):
        self._session = session or Session.login()
        if not (user_id and authcode):
            photo_tree = html.fromstring(self._session.okc_get(
                'profile/{0}/photos#upload'.format(self._session.log_in_name)
            ).content)
        self._authcode = authcode or helpers.get_authcode(photo_tree)
        self._user_id = user_id or helpers.get_current_user_id(photo_tree)

    @property
    def pic_id(self):
        return self._response_dict['id']

    @property
    def height(self):
        return self._response_dict['height']

    @property
    def width(self):
        return self._response_dict['width']

    def upload(self, incoming):
        if isinstance(incoming, Info):
            return self.upload_from_info(incoming)
        if hasattr(incoming, 'read'):
            return self.upload_file(incoming)
        return self.upload_by_filename(incoming)

    def upload_from_info(self, info):
        response = self._session.get(info.jpg_uri, stream=True)
        self.upload_file(response.raw)

    def upload_by_filename(self, filename):
        with open(filename, 'rb') as file_object:
            self.upload(file_object)

    def upload_file(self, file_object):
        files = {'file': ('my_photo.jpg', file_object,
                          'image/jpeg', {'Expires': '0'})}
        response = self._session.okc_post(self._uri, files=files)
        response_script_text = xpb.script.get_text_(
            html.fromstring(response.content)
        )
        self._response_dict = self._get_response_json(response_script_text)
        return self._response_dict

    def _get_response_json(self, response_text):
        start = response_text.find('res =') + 5
        end = response_text.find('};') + 1
        response_text = response_text[start:end]
        log.info(simplejson.dumps({'photo_upload_response': response_text}))
        return simplejson.loads(response_text)

    def _confirm_parameters(self, thumb_nail_left=None, thumb_nail_top=None,
                            thumb_nail_right=None, thumb_nail_bottom=None):
        return {
            'userid': self._user_id,
            'albumid': 0,
            'authcode': self._authcode,
            'okc_api': 1,
            'picid': self.pic_id,
            'picture.add_ajax': 1,
            'use_new_upload': 1,
            'caption': '',
            'height': self.height,
            'width': self.width,
            'tn_upper_left_x': thumb_nail_left or 0,
            'tn_upper_left_y': thumb_nail_top or 0,
            'tn_lower_right_x': thumb_nail_right or self.width,
            'tn_lower_right_y': thumb_nail_bottom or self.height
        }

    def confirm(self, **kwargs):
        return self._session.okc_get('photoupload',
                                     params=self._confirm_parameters(**kwargs))

    def upload_and_confirm(self, incoming, **kwargs):
        self.upload(incoming)
        if isinstance(incoming, Info):
            kwargs.setdefault('thumb_nail_left', incoming.thumb_nail_left)
            kwargs.setdefault('thumb_nail_top', incoming.thumb_nail_top)
            kwargs.setdefault('thumb_nail_right', incoming.thumb_nail_right)
            kwargs.setdefault('thumb_nail_bottom', incoming.thumb_nail_bottom)
        self.confirm(**kwargs)
        return self._response_dict


class Info(object):

    base_uri = "http://k0.okccdn.com/php/load_okc_image.php/images/"

    cdn_re = re.compile("http://.*okccdn.com.*images/"
                        "[0-9]*x[0-9]*/[0-9]*x[0-9]*/"
                        "(?P<tnl>[0-9]*?)x(?P<tnt>[0-9]*?)/"
                        "(?P<tnr>[0-9]*)x(?P<tnb>[0-9]*)/0/"
                        "(?P<id>[0-9]*).webp\?v=2")

    @classmethod
    def from_cdn_uri(cls, cdn_uri):
        match = cls.cdn_re.match(cdn_uri)
        return cls(match.group('id'), match.group('tnl'), match.group('tnt'),
            match.group('tnr'), match.group('tnb'))

    def __init__(self, photo_id, tnl, tnt, tnr, tnb):
        self.id = photo_id
        self.thumb_nail_left = int(tnl)
        self.thumb_nail_top = int(tnt)
        self.thumb_nail_right = int(tnr)
        self.thumb_nail_bottom = int(tnb)

    @property
    def jpg_uri(self):
        return '{0}{1}.jpg'.format(self.base_uri, self.id)

    def __repr__(self):
        return 'photo.{0}({1}, {2}, {3}, {4}, {5})'.format(type(self).__name__, self.id,
                                         self.thumb_nail_left,
                                         self.thumb_nail_top,
                                         self.thumb_nail_right,
                                         self.thumb_nail_bottom)
