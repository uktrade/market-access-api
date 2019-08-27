# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.conf import settings

from rest_framework import status
from rest_framework.response import Response

from api.interactions.models import Document


def admin_override(request):
    """This view is to redirect the admin page to SSO for authentication."""

    user = request.user
    if user.is_authenticated and user.is_staff and user.is_active:
        return redirect(settings.LOGIN_REDIRECT_URL)
    elif not user.is_authenticated:
        return redirect("authbroker:login")
    else:
        return HttpResponse("Forbidden", status=403)

class BaseMultiDocumentUploadableView:
    serializer = None

    def _fix_edit_documents(self, parent):
        if "documents" in self.request.data:
            docs_in_req = self.request.data.get("documents", None)
            docs_to_add = []
            if docs_in_req:
                docs_to_add = [get_object_or_404(Document, pk=id) for id in docs_in_req]
            docs_to_detach = list(set(parent.documents.all()) - set(docs_to_add))
            if serializer.is_valid():
                serializer.save(documents=docs_to_add, modified_by=self.request.user)
                for doc in docs_to_detach:
                    parent.documents.remove(doc)
                    doc.detached = True
                    doc.save()
                return Response(data=serializer.data, status=status.HTTP_200_OK)
        else:
            if serializer.is_valid():
                serializer.save(modified_by=self.request.user)
                return Response(data=serializer.data, status=status.HTTP_200_OK)
