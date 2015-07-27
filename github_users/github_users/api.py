from django.conf.urls import url

from tastypie import fields
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.utils import trailing_slash

from .models import GitHubUser


class GitHubUserResource(ModelResource):
    followers = fields.ToManyField('self', 'followers', use_in='detail')
    following = fields.ToManyField('self', 'following', use_in='detail')

    class Meta:
        queryset = GitHubUser.objects.all()
        resource_name = 'user'
        fields = ['id', 'github_id', 'login', 'num_following',
                  'num_followers', 'location', 'company']
        filtering = {
            'login': ALL,
            'num_followers': ALL,
            'num_following': ALL,
            'location': ALL,
            'company': ALL,
            'followers': ALL_WITH_RELATIONS,
            'following': ALL_WITH_RELATIONS,
            'distance': []
        }

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<%s>.*?)/within/(?P<distance>\d+)%s$" % (
                self._meta.resource_name,
                self._meta.detail_uri_name,
                trailing_slash()
            ), self.wrap_view('within'), name="api_user_within"),
        ]

    def within(self, request, **kwargs):
        """
        Expose the distance method on the custom manager via an instance.

        There is almost definitely a better way to do this. This method is
        duplicating a bunch of code in the get_list() method.
        """
        self.method_check(request, allowed=['get'])
        basic_bundle = self.build_bundle(request=request)
        distance = kwargs.pop('distance')
        user = self.cached_obj_get(bundle=basic_bundle,
                                   **self.remove_api_resource_names(kwargs))
        # Access our custom manager method to get the appropriate queryset
        objects = user.users_within_distance(int(distance))

        sorted_objects = self.apply_sorting(objects, options=request.GET)

        paginator = self._meta.paginator_class(request.GET, sorted_objects,
                                               resource_uri=self.get_resource_uri(),
                                               limit=self._meta.limit,
                                               max_limit=self._meta.max_limit,
                                               collection_name=self._meta.collection_name)
        to_be_serialized = paginator.page()

        # Dehydrate the bundles in preparation for serialization.
        bundles = []

        for obj in to_be_serialized[self._meta.collection_name]:
            bundle = self.build_bundle(obj=obj, request=request)
            bundles.append(self.full_dehydrate(bundle, for_list=True))

        to_be_serialized[self._meta.collection_name] = bundles
        to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)
        return self.create_response(request, to_be_serialized)

