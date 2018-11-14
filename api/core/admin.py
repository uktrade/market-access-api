# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

class BaseModelAdminMixin:
    """
    Mixin for ModelAdmins which adds extra functionalities.
    Useful when the model extends core.BaseModel

    It updates created_by and modified_by automatically from the logged in user.

    It also adds support for descriptive versions of created_on/by and modified_on/by,
    using only two admin "fields": 'created' and 'modified'.
    To use them just add 'created' and 'modified' to `readonly_fields` and `fields`
    instead of created_on/by and modified_on/by.
    """

    def _get_description_for_timed_event(self, event_on, event_by):
        text_parts = []
        if event_on:
            text_parts.extend((
                f'on {date_filter(event_on)}',
                f'at {time_filter(event_on)}',
            ))
        if event_by:
            adviser_admin_url = get_change_link(event_by)
            text_parts.append(f'by {adviser_admin_url}')

        return mark_safe(' '.join(text_parts) or '-')

    def created(self, obj):
        """:returns: created on/by details."""
        return self._get_description_for_timed_event(obj.created_on, obj.created_by)

    def modified(self, obj):
        """:returns: modified on/by details."""
        return self._get_description_for_timed_event(obj.modified_on, obj.modified_by)

    def save_model(self, request, obj, form, change):
        """
        Populate created_by/modified_by from the logged in user.
        """
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user

        super().save_model(request, obj, form, change)
