import logging
import re

from lxml import html
import simplejson

from . import util
from . import helpers
from .session import Session
from .xpath import xpb


log = logging.getLogger(__name__)


class PhotoUploader(object):
    """Upload photos to okcupid.com."""

    _uri = 'ajaxuploader'

    def __init__(self, session=None, user_id=None, authcode=None):
        self._session = session or Session.login()
        if user_id:
            self._user_id = user_id
        if authcode:
            self._authcode = authcode

    @util.cached_property
    def _photo_tree(self):
        return html.fromstring(self._session.okc_get(
            u'profile/{0}/photos#upload'.format(self._session.log_in_name)
        ).content)

    @util.cached_property
    def _authcode(self):
        return helpers.get_authcode(self._photo_tree)

    @util.cached_property
    def _user_id(self):
        return helpers.get_current_user_id(self._photo_tree)

    def upload(self, incoming):
        if isinstance(incoming, Info):
            return self.upload_from_info(incoming)
        elif hasattr(incoming, 'read'):
            return self.upload_file(incoming)
        return self.upload_by_filename(incoming)

    def upload_from_info(self, info):
        response = self._session.get(info.jpg_uri, stream=True)
        return self.upload_file(response.raw)

    def upload_by_filename(self, filename):
        with open(filename, 'rb') as file_object:
            _, extension = filename.rsplit('.')
            return self.upload_file(file_object, image_type=extension)

    def upload_file(self, file_object, image_type='jpeg'):
        files = {'file': ('my_photo.jpg', file_object,
                          'image/{0}'.format(image_type), {'Expires': '0'})}
        response = self._session.okc_post(self._uri, files=files)
        response_script_text = xpb.script.get_text_(
            html.fromstring(response.content)
        )
        return self._get_response_json(response_script_text)

    def _get_response_json(self, response_text):
        start = response_text.find('res =') + 5
        end = response_text.find('};') + 1
        response_text = response_text[start:end]
        log.info(simplejson.dumps({'photo_upload_response': response_text}))
        return simplejson.loads(response_text)

    def _confirm_parameters(self, pic_id, thumb_nail_left=None, thumb_nail_top=None,
                            thumb_nail_right=None, thumb_nail_bottom=None,
                            caption='', height=None, width=None):
        return {
            'userid': self._user_id,
            'albumid': 0,
            'authcode': self._authcode,
            'okc_api': 1,
            'picid': pic_id,
            'picture.add_ajax': 1,
            'use_new_upload': 1,
            'caption': caption,
            'height': height,
            'width': width,
            'tn_upper_left_x': thumb_nail_left or 0,
            'tn_upper_left_y': thumb_nail_top or 0,
            'tn_lower_right_x': thumb_nail_right or width,
            'tn_lower_right_y': thumb_nail_bottom or height
        }

    def confirm(self, pic_id, **kwargs):
        return self._session.okc_get(
            'photoupload', params=self._confirm_parameters(pic_id, **kwargs)
        )

    def upload_and_confirm(self, incoming, **kwargs):
        """Upload the file to okcupid and confirm, among other things, its
        thumbnail position.

        :param incoming: A filepath string, :class:`.Info` object or
                         a file like object to upload to okcupid.com.
                         If an info object is provided, its thumbnail
                         positioning will be used by default.
        :param caption: The caption to add to the photo.
        :param thumb_nail_left: For thumb nail positioning.
        :param thumb_nail_top: For thumb nail positioning.
        :param thumb_nail_right: For thumb nail positioning.
        :param thumb_nail_bottom: For thumb nail positioning.
        """
        response_dict = self.upload(incoming)
        if 'error' in response_dict:
            log.warning('Failed to upload photo')
            return response_dict
        if isinstance(incoming, Info):
            kwargs.setdefault('thumb_nail_left', incoming.thumb_nail_left)
            kwargs.setdefault('thumb_nail_top', incoming.thumb_nail_top)
            kwargs.setdefault('thumb_nail_right', incoming.thumb_nail_right)
            kwargs.setdefault('thumb_nail_bottom', incoming.thumb_nail_bottom)
        kwargs['height'] = response_dict.get('height')
        kwargs['width'] = response_dict.get('width')
        self.confirm(response_dict['id'], **kwargs)
        return response_dict

    def delete(self, photo_id, album_id=0):
        """Delete a photo from the logged in users account.

        :param photo_id: The okcupid id of the photo to delete.
        :param album_id: The album from which to delete the photo.
        """
        if isinstance(photo_id, Info):
            photo_id = photo_id.id
        return self._session.okc_post('photoupload', data={
            'albumid': album_id,
            'picid': photo_id,
            'authcode': self._authcode,
            'picture.delete_ajax': 1
        })


class Info(object):
    """Represent a photo that appears on a okcupid.com user's profile."""

    base_uri = "https://k0.okccdn.com/php/load_okc_image.php/images/"

    cdn_re = re.compile("http(?P<was_secure>s?)://.*okccdn.com.*images/"
                        "[0-9]*x[0-9]*/[0-9]*x[0-9]*/"
                        "(?P<tnl>[0-9]*?)x(?P<tnt>[0-9]*?)/"
                        "(?P<tnr>[0-9]*)x(?P<tnb>[0-9]*)/0/"
                        "(?P<id>[0-9]*).(:?webp|jpeg)\?v=\d+")

    @classmethod
    def from_cdn_uri(cls, cdn_uri):
        match = cls.cdn_re.match(cdn_uri)
        return cls(match.group('id'), match.group('tnl'), match.group('tnt'),
                   match.group('tnr'), match.group('tnb'))

    def __init__(self, photo_id, tnl, tnt, tnr, tnb):
        self.id = int(photo_id)
        #: The horizontal position of the left side of this photo's thumbnail.
        self.thumb_nail_left = int(tnl)
        #: The vertical position of the top side of this photo's thumbnail.
        self.thumb_nail_top = int(tnt)
        #: The horizontal position of the right side of this photo's thumbnail.
        self.thumb_nail_right = int(tnr)
        #: The vertical position of the bottom side of this photo's thumbnail.
        self.thumb_nail_bottom = int(tnb)

    @property
    def jpg_uri(self):
        """
        :returns: A uri from which this photo can be downloaded in jpg format.
        """
        return '{0}{1}.jpg'.format(self.base_uri, self.id)

    def __repr__(self):
        return 'photo.{0}({1}, {2}, {3}, {4}, {5})'.format(
            type(self).__name__,
            self.id,
            self.thumb_nail_left,
            self.thumb_nail_top,
            self.thumb_nail_right,
            self.thumb_nail_bottom
        )
