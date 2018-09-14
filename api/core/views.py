# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings


def admin_override(request):
    """This view is to redirect the admin page to SSO for authentication."""

    user = request.user
    if user.is_authenticated and user.is_staff and user.is_active:
        return redirect(settings.LOGIN_REDIRECT_URL)
    elif not user.is_authenticated:
        return redirect('authbroker:login')
    else:
        return HttpResponse('Forbidden', status=403)
