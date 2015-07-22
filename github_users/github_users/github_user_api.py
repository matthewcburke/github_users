import requests

from django.conf import settings
from django.core.cache import cache


class GitHubUserApi(object):
    """
    Provide a simple way to query the GitHub user endpoint and get follower and following
    information.
    """
    HOST = 'https://api.github.com/'

    def __init__(self):
        self.token = settings.GITHUB_ACCESS_TOKEN 

    def _populate_headers(self, endpoint):
        """
        Create and return a headers dict.

        Populate it with and auth token if we found one in the settings.
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
        if header_key in response.headers:
            cache_key = 'e_tag-%s' % endpoint
            cache.set(cache_key, response.headers[header_key].lstrip('W/'))

    def get_user(self, username):
        user_endpoint = 'users/%s' % username
        headers = self._populate_headers(user_endpoint)
        response = requests.get(''.join([self.HOST, user_endpoint]),
                                headers=headers)
        self._cache_etag(response, user_endpoint)
        return response

    def get_user_followers(self, username, follower_endpoint=None):
        if follower_endpoint is None:
            follower_endpoint = 'users/%s/followers' % username
        headers = self._populate_headers(follower_endpoint)
        response = requests.get(''.join([self.HOST, follower_endpoint]),
                                headers=headers)
        self._cache_etag(response, follower_endpoint)
        return response

    def get_user_following(self, username):
        following_endpoint = 'users/%s/following' % username
        headers = self._populate_headers(following_endpoint)
        response = requests.get(''.join([self.HOST, following_endpoint]),
                                headers=headers)
        self._cache_etag(response, following_endpoint)
        return response
