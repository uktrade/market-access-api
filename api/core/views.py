# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings

# Create your views here.

# This view is to redirect the admin page to SSO for authentication.
def admin_override(request):
    if not request.user.is_authenticated:
    # redirect to SSO
        return redirect('authbroker:login')
    elif not request.user.is_staff and not request.user.is_superuser:
        return HttpResponse('Access Denied')
    else:
        return redirect('/admin/')
