import json

from django.core.urlresolvers import reverse
from django.test import TestCase

from .models import GitHubUser


class UserRelationsTestCase(TestCase):
    """
    A few regression tests for ``users_within_distance()``
    """
    fixtures = ['test_data.json']

    def setUp(self):
        self.root_user = GitHubUser.objects.get(login='breadjc')

    def test_distance_1(self):
        within_1 = self.root_user.users_within_distance(1)
        self.assertEqual(within_1.count(), 3)

    def test_distance_2(self):
        within_2 = self.root_user.users_within_distance(2)
        self.assertEqual(within_2.count(), 7)

    def test_distance_3(self):
        within_3 = self.root_user.users_within_distance(3)
        self.assertEqual(within_3.count(), 63)


class UserApiTestCase(TestCase):
    """
    A few tests for the API
    """
    fixtures = ['test_data.json']

    def setUp(self):
        self.root_user = GitHubUser.objects.get(login='breadjc')
        self.user_list = reverse('api_dispatch_list', kwargs={'resource_name': 'user'})

    def test_user_list(self):
        resp = self.client.get("%s?order_by=num_following" % self.user_list)
        data = json.loads(resp.content)
        self.assertEqual(data['meta']['total_count'], 64)
        logins = [o['login'] for o in data['objects']]
        self.assertTrue('matthewcburke' in logins)

    def test_followers(self):
        resp = self.client.get("%s?followers=%d" % (self.user_list, self.root_user.pk))
        data = json.loads(resp.content)
        self.assertEqual(data['meta']['total_count'], 3)
        logins = [o['login'] for o in data['objects']]
        self.assertTrue('matthewcburke' in logins)

    def test_within(self):
        mb = GitHubUser.objects.get(login='matthewcburke')
        uri = reverse('api_user_within', kwargs={'resource_name': 'user', 'pk': mb.pk,
                                                 'distance': 3})
        resp = self.client.get(uri)
        data = json.loads(resp.content)
        self.assertEqual(data['meta']['total_count'], 7)
