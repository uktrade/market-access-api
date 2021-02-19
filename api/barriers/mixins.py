class BarrierRelatedMixin:
    """
    For use by models which are related to a barrier.

    Updates the related barrier's modified_on and modified_by on save.
    """

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.barrier.skip_history_when_saving = True
        self.barrier.modified_on = self.modified_on
        self.barrier.modified_by = self.modified_by
        self.barrier.save()
        del self.barrier.skip_history_when_saving
