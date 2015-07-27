# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GitHubUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('e_tag', models.CharField(max_length=32, null=True, blank=True)),
                ('last_retrieved', models.DateTimeField()),
                ('last_checked', models.DateTimeField()),
                ('github_id', models.IntegerField(unique=True)),
                ('login', models.CharField(unique=True, max_length=39)),
                ('num_followers', models.IntegerField(null=True, blank=True)),
                ('followers_etag', models.CharField(max_length=32, null=True, blank=True)),
                ('followers_url', models.URLField(null=True, blank=True)),
                ('num_following', models.IntegerField(null=True, blank=True)),
                ('following_etag', models.CharField(max_length=32, null=True, blank=True)),
                ('following_url', models.URLField(null=True, blank=True)),
                ('company', models.CharField(max_length=200, null=True, blank=True)),
                ('location', models.CharField(max_length=200, null=True, blank=True)),
                ('followers', models.ManyToManyField(related_name='following', to='github_users.GitHubUser')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
