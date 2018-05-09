# Market Access API

Market Access API provides an API into Market Access frontend clients.

## Installation with Docker

Market Access API uses Docker compose to setup and run all the necessary components. The docker-compose.yml file provided is meant to be used for running tests and development.

## Native installation (without Docker)

Dependencies:

-   Python 3.6.x
-   PostgreSQL 9.6

1.  Clone the repository:

    ```shell
    git clone https://github.com/uktrade/market-access-api
    cd market-access-api
    ```

2.  Install `virtualenv` if you don’t have it already:

    ```shell
    pip install virtualenv
    ```

3.  Create and activate the virtualenv:

    ```shell
    virtualenv --python=python3 env
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

6.  Create the db. By default, the dev version uses postgres:

    ```shell
    psql -p5432
    create database market_access;
    ```

7.  Create a superuser:

    ```shell
    ./manage.py createsuperuser
    ```
    
8. Start the server:

    ```shell
    ./manage.py runserver
    ```

To run the tests:

```shell
pytest .
```

To run the linter:

```shell
flake8
```