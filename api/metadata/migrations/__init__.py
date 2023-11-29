from django.contrib.auth import get_user_model
import datetime

def remove_tag_wrapper(tag_title):
    """Remove a tag from all barriers and saved searches."""
    def remove_tag(apps, schema_editor):
        SavedSearch = apps.get_model("user", "SavedSearch")
        BarrierTag = apps.get_model("metadata", "BarrierTag")
        Barrier = apps.get_model("barriers", "Barrier")
        HistoricalBarrier = apps.get_model("barriers", "HistoricalBarrier")

        tag_object = BarrierTag.objects.get(title=tag_title)

        # removing the tag from any barriers, we need to create new historical records to reflect this
        # change in the database
        for barrier in Barrier.objects.filter(tags=tag_object):
            barrier.tags.remove(tag_object)
            try:
                historical_instance = HistoricalBarrier.objects.filter(id=barrier.pk).latest()
                historical_instance.pk = None
                historical_instance.save()
                # this new tags_cache will just contain the previous list of tags, minus the one we just removed
                historical_instance.tags_cache = list(barrier.tags.values_list("id", flat=True))
                # setting the history_date to be 1 second after the previous historical record so it counts as a new one
                historical_instance.history_date = datetime.timedelta(seconds=1) + historical_instance.history_date
                historical_instance.save()
            except HistoricalBarrier.DoesNotExist:
                pass

        # removing the tag from any saved searches
        saved_searches = SavedSearch.objects.filter(
            filters__tags__contains=tag_object.id
        )
        for search in saved_searches:
            search.filters["tags"].remove(tag_object.id)
            search.save()


        # now archiving the tag all-together
        tag_object.archived = True
        tag_object.save()

    return remove_tag
