import logging

from lxml import html
import simplejson

from . import util
from . import helpers
from .session import Session
from .xpath import xpb


log = logging.getLogger(__name__)


@util.n_partialable
class PhotoUploader(object):

    _uri = 'https://www.okcupid.com/ajaxuploader'

    def __init__(self, filename, session=None, user_id=None, authcode=None):
        self._session = session or Session.login()
        self._filename = filename
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

    def upload(self):
        with open(self._filename, 'rb') as file_object:
            files = {'file': (self._filename, file_object,
                              'image/jpeg', {'Expires': '0'})}
            response = self._session.post(self._uri, files=files)
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

    @property
    def _confirm_parameters(self):
        return {
            'userid': self._user_id,
            'albumid': 0,
            'authcode': self._authcode,
            'okc_api': 1,
            'picid': self.pic_id,
            'picture.add_ajax': 1,
            'use_new_upload': 1,
            'caption': 1,
            'height': self.height,
            'width': self.width,
        }

    def confirm(self):
        return self._session.okc_get('photoupload',
                                     params=self._confirm_parameters)

    def upload_and_confirm(self):
        self.upload()
        self.confirm()
        return self._response_dict
