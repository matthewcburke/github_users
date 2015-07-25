import datetime
import copy
import pytz

from django.db import models

from .github_user_api import GitHubUserApi


class GitHubObject(models.Model):
    e_tag = models.CharField(max_length=32, null=True, blank=True)
    last_retrieved = models.DateTimeField()

    class Meta:
        abstract = True


class GitHubUser(GitHubObject):
    """
    Model a GitHub user with particular interest in followers and users being followed.
    """
    github_id = models.IntegerField(unique=True)
    login = models.CharField(max_length=39, unique=True)
    followers = models.ManyToManyField('self', related_name='following', symmetrical=False)
    num_followers = models.IntegerField(null=True, blank=True)
    num_following = models.IntegerField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super(GitHubUser, self).__init__(*args, **kwargs)
        self.api = GitHubUserApi()

    def __unicode__(self):
        return self.login

    def populate_from_github(self):
        api_resp = self.api.get_user(self.login)
        if api_resp['status'] == 200:
            self.github_id = api_resp['json']['id']
            self.e_tag = api_resp['etag']
            self.num_followers = api_resp['json']['followers']
            self.num_following = api_resp['json']['following']
            self.last_retrieved = datetime.datetime.now(tz=pytz.UTC)
        elif api_resp['status'] == 304:
            pass
        elif api_resp['status'] == 404:
            pass
        else:
            pass
        return self

    def populate_followers(self):
        follower_data = self.api.get_user_followers(self.login)['json']
        for user in follower_data:
            follower, created = GitHubUser.objects.get_or_create(
                github_id=user['id'],
                login=user['login'],
                defaults={'last_retrieved': datetime.datetime.now(tz=pytz.UTC)}
            )
            if follower not in self.followers.all():
                self.followers.add(follower)

    def populate_following(self):
        following_data = self.api.get_user_following(self.login)['json']
        for user in following_data:
            following, created = GitHubUser.objects.get_or_create(
                github_id=user['id'],
                login=user['login'],
                defaults={'last_retrieved': datetime.datetime.now(tz=pytz.UTC)}
            )
            if following not in self.following.all():
                self.following.add(following)

    def fill_follow_graph(self, depth=3, parents=None):
        """
        Get followers and followees recursively to the given depth.

        ``parents`` is used by the recursive calls to avoid following
        graph cycles.
        """
        if depth <= 0:
            return

        if parents is None:
            parents = []

        parents.append(self)

        self.populate_followers()
        self.populate_following()

        for follower in self.followers.all():
            # start with the original list of parents each time.
            calling_parents = copy.copy(parents)
            if follower in calling_parents:
                continue
            follower = follower.populate_from_github()
            follower.save()
            follower.fill_followering_graph(depth=depth - 1, parents=calling_parents)

        for followee in self.following.all():
            # start with the original list of parents each time.
            calling_parents = copy.copy(parents)
            if followee in calling_parents:
                continue
            followee = followee.populate_from_github()
            followee.save()
            followee.fill_followering_graph(depth=depth - 1, parents=calling_parents)
