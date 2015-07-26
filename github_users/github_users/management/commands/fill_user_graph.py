from django.core.management.base import BaseCommand, CommandError
from ...models import GitHubUser


class Command(BaseCommand):
    help = "Import a user and their followers to a given depth from GitHub."

    def add_arguments(self, parser):
        parser.add_argument('login', type=str)
        parser.add_argument('depth', nargs='?', default=3, type=int)

    def handle(self, *args, **options):
        users = GitHubUser.objects.filter(login=options['login'])
        if users.exists():
            user = users.get()
        else:
            user = GitHubUser(login=options['login']).populate_from_github()

        user.fill_follow_graph(depth=options['depth'])
