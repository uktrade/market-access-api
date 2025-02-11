# Market Access API


Market Access API provides an API into Market Access frontend clients.

## Installation with Docker (preferred)

Market Access API uses Docker compose to setup and run all the necessary components. The docker-compose.yml file provided is meant to be used for running tests and development.

#### Prerequisites
1. Install `docker` & `docker compose` - https://docs.docker.com/install/
2. Add the following to your `hosts` file:

        # Market Access API
        127.0.0.1               api.market-access.local

        # Mock SSO
        127.0.0.1               mocksso
3. Clone the repository:
    ```shell
    git clone https://github.com/uktrade/market-access-api
    cd market-access-api
    ```
4. Copy the env file - `cp docker-compose.local-template.env docker-compose.env`
5. Set values for the env file variables indicated `<<CHECK_VAULT>>`, set `FAKE_METADATA` to `True`
6. Set `MOCK_SSO_EMAIL_USER_ID` in docker-compose.yml to the email you will use as superuser in Install step 3
7. Update Makefile so `django-run` command uses port `0:8883`

#### Install
1. Build the images and spin up the containers by running - `docker-compose up --build`
2. Set up git hooks by running - `make git-hooks`
3. Enter bash within the django container using `docker-compose exec web bash`
4. Initialise DB by running the migrations using `./manage.py migrate`
5. Then create a superuser `py3 manage.py dmas_createsuperuser --email your@email.here` then `exit` the container
6. To start the dev server run - `make django-run`
7. The API is now accessible via http://api.market-access.local:8880

#### Running in detached mode
The installation steps above will require 2 terminal windows to be open to run the processes.
If desired this can be reduced to 0 via the following commands:
1. Start the containers in detached mode - `docker-compose up -d`
2. Start django in detached mode - `make django-run-detached`
3. The API is now accessible via http://api.market-access.local:8880

Now even if you closed your terminal, the server would be still running.

#### Make commands
There's a set of make commands that you can utilize straight away. \
To list all available commands with help text type `make help` in terminal and hit `Enter`.

-----

## Native installation (without Docker)

Dependencies:

-   Python 3.9
-   PostgreSQL 10
-   redis 3.2

1.  Clone the repository:

    ```shell
    git clone https://github.com/uktrade/market-access-api
    cd market-access-api
    ```

2.  Install Python 3.9

    [See this guide](https://docs.python-guide.org/starting/installation/) for detailed instructions for different platforms.

3.  Create and activate the virtualenv:

    ```shell
    python3.9 -m venv env
    source env/bin/activate
    pip install -U pip
    ```

4.  Install the dependencies:

    ```shell
    pip install -r requirements.txt
    ```

5.  Create an `.env` settings file (it’s gitignored by default):

    ```shell
    cp config/sample.env .env
    ```
The user authentication is handled by the [DIT SSO](https://github.com/uktrade/staff-sso) where a token is stored and used for introspection of user and other end points. You can run a [mock-sso](https://github.com/uktrade/mock-sso) client to run the app near a produciton mode without the hastle of logging in. Configure your `.env` file accordingly.

There are some machine to machine APIs that are called on the backend and we use [Hawk](https://github.com/hueniverse/hawk) to secure those calls. You can share Hawk Key and ID with frontend to work in hawk mode. Alternatively, in dev mode, you can turn off Hawk using the `.env` settings.

6.  Create the db. By default, the dev version uses postgres:

    ```shell
    psql -p5432
    create database market_access;
    ```
7. Make sure you have redis running locally and that the REDIS_BASE_URL in your `.env` is up-to-date.

8. Apply migrations:

    ```shell
    ./manage.py migrate
    ```

9.  Create a superuser:

    ```shell
    ./manage.py createsuperuser
    ```

8. Start the server:

    ```shell
    ./manage.py runserver
    ```

9. Start celery:

    ```shell
    celery worker -A config -l info -Q celery,long-running -B
    ```

    Note that in production the long-running queue is run in a separate worker with the
    `-O fair --prefetch-multiplier 1` arguments for better fairness when long-running tasks
    are running or pending execution.

To run the tests:

```shell
pytest .
```

To run the linter:

```shell
flake8
```

## Granting access to the front end

The [internal front end](https://github.com/uktrade/market-access-frontend) uses single sign-on. You should configure backend API as follows to use with the front end:

* `SSO_ENABLED`: `True`
* `RESOURCE_SERVER_INTROSPECTION_URL`: URL of the [RFC 7662](https://tools.ietf.org/html/rfc7662) introspection endpoint (should be the same server the front end is using). This is provided by a [Staff SSO](https://github.com/uktrade/staff-sso) instance.
* `RESOURCE_SERVER_AUTH_TOKEN`: Access token for the introspection server.
* `RESOURCE_SERVER_USER_INFO_URL`: URL of SSO endpoint to retreive logged in user information based on token provided in the header
* `RESOURCE_SERVER_USER_INTROSPECT_URL`: URL of SSO endpoint to retrieve user information based on query param

django-oauth-toolkit will create a user corresponding to the token if one does not already exist.

## Machine to machine Hawk authentication between frontend and backend

In general, [Hawk](https://github.com/hueniverse/hawk) authentication hashing the HTTP payload and `Content-Type` header, and using a nonce.

There are some machine to machine APIs that are called on the backend and we use [Hawk](https://github.com/hueniverse/hawk) to secure those calls. You can share Hawk Key and ID with frontend to work in hawk mode.

## Deployment

Market Access API can run on any Heroku-style platform. Configuration is performed via the following environment variables:


| Variable name | Required                                                                                         | Description                                                                                                                                |
| ------------- |--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| `ALLOWED_ADMIN_IPS` | No                                                                                               | IP addresses (comma-separated) that can access the admin site when RESTRICT_ADMIN is True.                                                 |
| `AV_V2_SERVICE_URL` | Yes                                                                                              | URL for ClamAV V2 service. If not configured, virus scanning will fail.                                                                    |
| `AWS_ACCESS_KEY_ID` | No                                                                                               | Used as part of [boto3 auto-configuration](http://boto3.readthedocs.io/en/latest/guide/configuration.html#configuring-credentials).        |
| `AWS_DEFAULT_REGION` | No                                                                                               | [Default region used by boto3.](http://boto3.readthedocs.io/en/latest/guide/configuration.html#environment-variable-configuration)         |
| `AWS_SECRET_ACCESS_KEY` | No                                                                                               | Used as part of [boto3 auto-configuration](http://boto3.readthedocs.io/en/latest/guide/configuration.html#configuring-credentials).        |
| `CELERY_TASK_ALWAYS_EAGER` | No                                                                                               | Can be set to True when running the app locally to run Celery tasks started from the web process synchronously. Not for use in production. |
| `DATABASE_URL`  | Yes                                                                                              | PostgreSQL server URL (with embedded credentials).                                                                                         |
| `DEBUG`  | Yes                                                                                              | Whether Django's debug mode should be enabled.                                                                                             |
| `SECRET_KEY`  | Yes                                                                                              |                                                                                                                                            |
| `SENTRY_DSN`  | Yes                                                                                              |                                                                                                                                            |
| `DEFAULT_BUCKET`  | Yes                                                                                              | S3 bucket for object storage.                                                                                                              |
| `DH_METADATA_URL` | Yes                                                                                              | Data Hub metadata URL for shared metadata.                                                                                                 |
| `HAWK_KEY` | Yes                                                                                              | Hawk Key to be shared with other party to authenticate with API.                                                                           |
| `HAWK_ID` | Yes                                                                                              | Hawk ID to be shared with other party to authenticate with API.                                                                            |
| `REDIS_BASE_URL`  | Yes                                                                                              | redis base URL for Celery functioning                                                                                                      |
| `RESOURCE_SERVER_INTROSPECTION_URL` | If SSO enabled                                                                                   | RFC 7662 token introspection URL used for signle sign-on                                                                                   |
| `RESOURCE_SERVER_AUTH_TOKEN` | If SSO enabled                                                                                   | Access token for RFC 7662 token introspection server                                                                                       |
| `RESOURCE_SERVER_USER_INFO_URL` | URL of SSO endpoint to retreive logged in user information based on token provided in the header |
| `RESOURCE_SERVER_USER_INTROSPECT_URL` | URL of SSO endpoint to retrieve user information based on query param                            |
| `RESTRICT_ADMIN` | No                                                                                               | Whether to restrict access to the admin site by IP address.                                                                                |
| `SSO_ENABLED` | Yes                                                                                              | Whether single sign-on via RFC 7662 token introspection is enabled                                                                         |
| `VCAP_SERVICES` | No                                                                                               | Set by GOV.UK PaaS when using their backing services. Contains connection details for Postgres, Redis etc.                                 |

## Test Coverage

Testing code coverage is automatically ran as part of the CircleCI build and sent to [codecov.io](https://codecov.io/gh/uktrade/market-access-api).
You can run the tests locally and generate a coverage report by running:

With docker:
```docker compose run --rm web coverage run -m pytest tests && coverage term```

Or for local builds:
```poetry run coverage run -m pytest tests && poetry run coverage term```

## Swagger Endpoint Documentation

API has auto-generated swagger documentation providing all of the information needed to easily make a request to each endpoint.
This can be accessed in UAT, development and local environments.
Local access must have SSO turned off in the env file.

URLS, replace base URL where appropriate:
```http://api.market-access.local:8880/redoc/```
```http://api.market-access.local:8880/swagger-ui/```
