"""
TODO:
- Handle paginated responses
- Handle rate limiting
"""
import logging
import requests

from django.conf import settings
from django.core.cache import cache


log = logging.getLogger(__name__)


class GitHubUserApi(object):
    """
    Provide a simple way to query the GitHub user endpoint and get
    follower and following information.
    """
    HOST = 'https://api.github.com'

    def __init__(self):
        self.token = settings.GITHUB_ACCESS_TOKEN 

    def _populate_headers(self, endpoint):
        """
        Create and return a headers dict.

        Populate it with and auth token if we found one in the
        settings.
        Populate headers with the etag if it is available.
        """
        headers = {}
        if self.token is not None:
            headers['Authorization'] = 'token %s' % self.token

        e_tag = cache.get('e_tag-%s' % endpoint)
        if e_tag is not None:
            headers['If-None-Match'] = '%s' % e_tag
        return headers

    @staticmethod
    def _cache_etag(response, endpoint):
        """
        Cache the etag for a given endpoint for use in future queries.
        """
        header_key = 'etag'
        if response is not None and header_key in response.headers:
            cache_key = 'e_tag-%s' % endpoint
            cache.set(cache_key,
                      response.headers[header_key].lstrip('W/'))

    def _get(self, endpoint, headers):
        try:
            return requests.get(''.join([self.HOST, endpoint]), headers=headers)
        except requests.exceptions.RequestException as e:
            log.exception("Exception while getting '%s': %s" % (endpoint, e))

    @staticmethod
    def _repackage_response(response):
        """
        Repackage the response into a dictionary, so that clients
        don't need to worry about error handling and interacting with
        headers.
        """
        if response is not None:
            try:
                json_data = response.json()
            except ValueError:
                json_data = []

            resp_dict = {
                'status': response.status_code,
                'etag': response.headers.get('etag', '').lstrip('W/'),
                'json': json_data
            }
        else:
            resp_dict = {'status': None, 'etag': None, 'json': []}

        return resp_dict

    def get_user(self, username):
        user_endpoint = '/users/%s' % username
        headers = self._populate_headers(user_endpoint)
        response = self._get(user_endpoint, headers)

        self._cache_etag(response, user_endpoint)
        return self._repackage_response(response)

    def get_user_followers(self, username, follower_endpoint=None):
        if follower_endpoint is None:
            follower_endpoint = '/users/%s/followers' % username
        headers = self._populate_headers(follower_endpoint)
        response = self._get(follower_endpoint, headers)
        self._cache_etag(response, follower_endpoint)
        return self._repackage_response(response)

    def get_user_following(self, username):
        following_endpoint = '/users/%s/following' % username
        headers = self._populate_headers(following_endpoint)
        response = self._get(following_endpoint, headers)
        self._cache_etag(response, following_endpoint)
        return self._repackage_response(response)
