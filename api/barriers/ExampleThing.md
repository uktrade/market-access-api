# Example of adding a new model to DMAS

This example demonstrates adding a new model to the DMAS API that is related to the core `Barrier` model, presenting it in the API,
and showing it in the barrier detail page on the front end.

The relevant code is contained in the `example/new-model` branches:
* [API branch](https://github.com/uktrade/market-access-api/tree/example/new-model)
* [Front end branch](https://github.com/uktrade/market-access-python-frontend/tree/example/new-model)

The commits have been kept small and are in the order described below, so will help to illustrate the process.

Although this is quite a small example, it touches on a number of the most important aspects of the DMAS code base
and its core principles of operation.

## API side

1. Add the model class. In the API app, this is standard Django stuff:
   1. Define the class in models.py.
      1. Subclassing `BaseModel` gives the model creation and modification tracking fields.
      2. Subclassing `FullyArchivableMixin` provides support for archiving instances of the model.
   2. `./manage.py makemigrations barriers`
   3. `./manage.py migrate barriers`
      1. [Related commit on GitHub](https://github.com/uktrade/market-access-api/commit/819ce2197acf9c4afd0a8e23d789e9ccb6f096a9)

2. Add the model to the API endpoint serialiser
   1. Create a test for the new thing being in the API response somewhere appropriate; in this case, we add our test class to `tests/test_barrier_details.py`.
      1. [Related commit on GitHub](https://github.com/uktrade/market-access-api/commit/b7f44087a0e302a222f1c8c9ca76601c1b79a141)
   2. Run the new test and see it fail.
   3. Add the new field to `api.barriers.serializers.barriers.BarrierDetailSerializer.Meta.fields`.
      1. [Related commit on GitHub](https://github.com/uktrade/market-access-api/commit/97e998dbd94bad002cbf791af091bc8b4622a2eb)
   4. Run the new test again; it should now pass.

3. Check if it's working _as expected_ (spoiler: it isn't):
   1. Create a test for the thing having the correct values for its attribute(s).
      1. [Related commit on GitHub](https://github.com/uktrade/market-access-api/commit/c049af57514d4d76415416c41e6121d626e3508c)
   2. Run the new test and see it fail; the default serialisation is just a list of `pk` values.

4. Define appropriate subclasses of `Field` and `Serializer` in order to correctly represent the new model in the API response:
   1. The serializer should be defined in an appropriate place; for convenience, we'll add `api.barriers.serializers.example_thing`, but a related object class will often be defined in its own app (e.g. action plans) and in that case, that app should be given a `serializers` module. As these are related models, we subclass `ModelSerializer`.
   2. The field uses the serializer, and it is also defined in `api.barriers.serializers.example_thing`. As this field represents a one-to-many relationship, we subclass `ListField`.
      1. [Related commit on GitHub](https://github.com/uktrade/market-access-api/commit/c8556a872d24c7eb079ff8ac48bbaf5d9161cf24)
   3. The field is then added to the `BarrierSerializerBase` mixin.
      1. [Related commit on GitHub](https://github.com/uktrade/market-access-api/commit/d4ecd8efa6318de38f59e4e57eecb9f25c06fa25)
   4. Run the tests again; they should now pass.

5. To support further experimentation, add the `ExampleThing` model to the Django Admin app, which by default can be accessed at http://localhost:8880/admin/ once you've added a superuser to log in as (see Readme.md).
   1. [Related commit on GitHub](https://github.com/uktrade/market-access-api/commit/4df392803d22821bdfb309c0fcae94542011eed9)

## Front end

As the front end has no direct connection to the database, it cannot use Django models.
Instead, it uses the `utils.models.APIModel` class to provide access to the members of the dictionaries returned (as JSON) by API calls.

In this case, the new objects will be present as the `example_things` attribute of a `Barrier` object, so can be used immediately.

To illustrate this, they have been added to the `barrier_detail.html` template.
Go to the model's admin page of the API server at http://localhost:8880/admin/barriers/examplething/, and add some things to a barrier.
Viewing the barrier's detail page on the front end should show you them, just below the modification date.

[Related commit on GitHub](https://github.com/uktrade/market-access-python-frontend/commit/240c0d287bb9462278631fa9e9bd5bd10838f8bc)

## Additional things to look at

Looking at how the following aspects of the app work will be informative:

* Search filters - these involve DRF filtering on the API side and React components on the front end, so are a good lead to follow to see the integration between the two sides
* Front end pseudo-models - although for a simple example like this we can get the data straight into a template without any further work, creating a subclass of `APIModel` and initialising it for each item allows more complex behaviour to be added. Example usages can be found in `barriers.models` and elsewhere.
* Including the objects in the Data Workspace and CSV serialisers.
