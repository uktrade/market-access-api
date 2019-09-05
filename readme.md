# Market Access API

Market Access API provides an API into Market Access frontend clients.

## Installation with Docker

Market Access API uses Docker compose to setup and run all the necessary components. The docker-compose.yml file provided is meant to be used for running tests and development.

## Native installation (without Docker)

Dependencies:

-   Python 3.7
-   PostgreSQL 10
-   redis 3.2

1.  Clone the repository:

    ```shell
    git clone https://github.com/uktrade/market-access-api
    cd market-access-api
    ```

2.  Install Python 3.7.
    
    [See this guide](https://docs.python-guide.org/starting/installation/) for detailed instructions for different platforms.

3.  Create and activate the virtualenv:

    ```shell
    python3.7 -m venv env
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

8. Populate the database:

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