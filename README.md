# Github public api crawler

A programming exercise.

### The Requirements

>Pick a starting point and using Github's public /users json API crawl and
>discover up to 3 degrees of nearby users via the followers edge.

>For example, from https://api.github.com/users/pauladam we can follow and
>discover this users followers at
>https://api.github.com/users/pauladam/followers

>In Django, create a users model to store these users as well as the necessary
>data to reconstruct the graph of these users and their relations.

>Build a simple API (via tastypie or other) to support some common queries of
>this data such as,

>  - Show all users
>  - Show users related to a given user
>  - Show users all users relating to a given user by n degrees where n is a given input parameter. (/users/pauladam/within-degree?n=2)

>Add support for a filtering / sorting by a few basic fields (location,
>followers / following, company).

>### GitHub Documentation

>  - https://developer.github.com/guides/getting-started/

## Installation

In a fresh virtualenv:

```bash
git clone https://github.com/matthewcburke/github_users.git
cd github_users
pip install -r requirements.txt
cd github_users
python manage.py migrate
# crawl GitHub to get some user data
python manage.py fill_user_graph matthewcburke
python manage.py runserver
```

## Browse The API

- `localhost:8000/api/user/`: will list all users, 20 per page.
- `localhost:8000/api/user/<primary key>/` will give a detail view of the given user. This will
  include uri's for all of this user's followers and all users that this user is following.
- `localhost:8000/api/user/<primary key>/within/<distance>/`: will list all users within the given
  distance of the given user. Use distance = 1 to list all of the users that this user is related
  to.
- `http://localhost:8000/api/user/?following=<primary key>`: one can also apply filters to the user list
  endpoint. Available fields to filter on:
  - `following`
  - `followers`
  - `num_followers`
  - `num_following`
  - `location`
  - `company`
- `localhost:8000/api/user/?order_by=-num_followers`: use the order_by parameter for ordering the
  results. One may order by `id`, `github_id`, `login`, `num_followers`, `num_following`,
  `location` and `company`.