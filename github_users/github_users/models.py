import datetime
import copy
import pytz
import requests

from django.db import models

from .github_user_api import GitHubUserApi


class GitHubObject(models.Model):
    e_tag = models.CharField(max_length=32, null=True, blank=True)
    last_retrieved = models.DateTimeField()

    class Meta:
        abstract = True


class FollowManager(models.Manager):
    def distance(self, root_user, distance=1, follow_qs=None, depth=1, *args, **kwargs):
        """
        Return a queryset of GitHubUsers who are a given distance from the root_user along
        the followers edges.

        We are accomplishing this by recursively building up sub-queries.

        Note that this method will follow cycles in the graph.

        :param distance: The distance between users on the graph
        :param follow_qs: The queryset to modify. Should only be passed by a recursive call.
        :param depth: Used internally to track depth of recursion.
                      Should only be passed by a recursive call.
        :return: a queryset
        """
        if follow_qs is None:
            follow_qs = self.get_queryset()

        if depth > distance:
            # end recursion
            return follow_qs.filter(*args, **kwargs)
        elif depth == 1:
            follower_or_following = (models.Q(following=root_user) |
                                     models.Q(followers=root_user))
        else:
            follower_or_following = (models.Q(followers__in=follow_qs) |
                                     models.Q(following__in=follow_qs))

        qs = self.get_queryset().filter(follower_or_following)
        return self.distance(follow_qs=qs, depth=depth + 1, distance=distance,
                             root_user=root_user).distinct()


class GitHubUser(GitHubObject):
    """
    Model a GitHub user with particular interest in followers and users being followed.
    """
    github_id = models.IntegerField(unique=True)
    login = models.CharField(max_length=39, unique=True)
    followers = models.ManyToManyField('self', related_name='following', symmetrical=False)
    num_followers = models.IntegerField(null=True, blank=True)
    num_following = models.IntegerField(null=True, blank=True)

    objects = models.Manager()
    follow_relations = FollowManager()

    def __init__(self, *args, **kwargs):
        super(GitHubUser, self).__init__(*args, **kwargs)
        self.api = GitHubUserApi()

    def __unicode__(self):
        return self.login

    def populate_from_github(self, save=True):
        api_resp = self.api.get_user(self.login)
        if api_resp['status'] == requests.codes.ok:
            self.github_id = api_resp['json']['id']
            self.e_tag = api_resp['etag']
            self.num_followers = api_resp['json']['followers']
            self.num_following = api_resp['json']['following']
            self.last_retrieved = datetime.datetime.now(tz=pytz.UTC)
        else:
            save = False

        if save:
            self.save()
        return self

    def populate_followers(self):
        api_resp = self.api.get_user_followers(self.login)
        if api_resp['status'] == requests.codes.ok:
            follower_data = api_resp['json']
        else:
            follower_data = []

        for user in follower_data:
            follower, created = GitHubUser.objects.get_or_create(
                github_id=user['id'],
                login=user['login'],
                defaults={'last_retrieved': datetime.datetime.now(tz=pytz.UTC)}
            )
            if follower not in self.followers.all():
                self.followers.add(follower)

    def populate_following(self):
        api_resp = self.api.get_user_following(self.login)
        if api_resp['status'] == requests.codes.ok:
            following_data = api_resp['json']
        else:
            following_data = []

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
            follower.fill_follow_graph(depth=depth - 1, parents=calling_parents)

        for followee in self.following.all():
            # start with the original list of parents each time.
            calling_parents = copy.copy(parents)
            if followee in calling_parents:
                continue
            followee = followee.populate_from_github()
            followee.fill_follow_graph(depth=depth - 1, parents=calling_parents)

    def users_at_distance(self, distance):
        """
        Return a queryset of all users at a given distance from self. Note that
        this method follows cycles in the graph.
        """
        return GitHubUser.follow_relations.distance(root_user=self, distance=distance)

    def users_within_distance(self, distance):
        """
        Return a queryset of all the users within the given distance to self.
        """
        assert distance > 0
        # Build up a queryset that includes all of the related  users within a given distance
        qs = self.users_at_distance(1)
        for i in range(2, distance + 1):
            qs = qs | self.users_at_distance(i)

        return qs.exclude(pk=self.pk)
