import json
import uuid

import pytest
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from api.core.test_utils import APITestMixin
from api.interactions.models import Document
from tests.barriers.factories import ReportFactory


class TestListInteractions(APITestMixin, APITestCase):
    def _submit_report(self, report):
        url = reverse("submit-report", kwargs={"pk": report.id})
        return self.api_client.put(url, format="json", data={})

    def setUp(self):
        # NULL next_steps_summary as that creates an interaction when the report is submitted
        self.report = ReportFactory(next_steps_summary="")

    def test_no_interactions(self):
        """Test there are no barrier interactions using list"""
        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        response = self.api_client.get(interactions_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_add_interactions_no_pin(self):
        """Test there is one interaction without pinning"""
        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url, format="json", data={"text": "sample interaction notes"}
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is False
        assert int_response.data["results"][0]["is_active"] is True

    def test_add_interactions_pinned(self):
        """Test there are one interaction with pinning"""
        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={"text": "sample interaction notes", "pinned": True},
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is True
        assert int_response.data["results"][0]["is_active"] is True

    def test_add_interactions_multiple(self):
        """Test multiple interactions for barrier"""
        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url, format="json", data={"text": "first interaction notes"}
        )
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1

        add_int_response = self.api_client.post(
            interactions_url, format="json", data={"text": "second interaction notes"}
        )
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 2

    def test_add_interactions_multiple_mixed_pinning(self):
        """Test multiple interactions with mixed pinning"""
        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url, format="json", data={"text": "first interaction notes"}
        )
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={"text": "second interaction notes", "pinned": True},
        )
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 2

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={"text": "third interaction notes", "pinned": False},
        )
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 3

    def test_get_interaction(self):
        """Test retreiving an interaction"""
        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url, format="json", data={"text": "sample interaction notes"}
        )
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is False
        assert int_response.data["results"][0]["is_active"] is True

        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True

    def test_edit_interaction(self):
        """Test editing an interaction"""
        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url, format="json", data={"text": "sample interaction notes"}
        )
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is False
        assert int_response.data["results"][0]["is_active"] is True

        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True

        edit_int_response = self.api_client.put(
            get_interaction_url,
            format="json",
            data={"text": "edited interaction notes"},
        )
        assert edit_int_response.status_code == status.HTTP_200_OK

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "edited interaction notes"

    def test_edit_interaction_pin_it(self):
        """Test edit interaction with pinning"""
        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url, format="json", data={"text": "sample interaction notes"}
        )
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is False
        assert int_response.data["results"][0]["is_active"] is True

        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True

        edit_int_response = self.api_client.put(
            get_interaction_url, format="json", data={"pinned": True}
        )
        assert edit_int_response.status_code == status.HTTP_200_OK

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["pinned"] is True

    def test_edit_interaction_unpin_it(self):
        """Test edit interaction un pin it"""
        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={"text": "sample interaction notes", "pinned": True},
        )
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is True
        assert int_response.data["results"][0]["is_active"] is True

        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is True
        assert get_int_response.data["is_active"] is True

        edit_int_response = self.api_client.put(
            get_interaction_url, format="json", data={"pinned": False}
        )
        assert edit_int_response.status_code == status.HTTP_200_OK

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["pinned"] is False

    def test_add_document(self):
        """Test add a new document, ready to be attached to an interaction"""
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        assert docs_list_report_response.data["original_filename"] == "somefile.pdf"
        assert docs_list_report_response.data["id"] is not None
        assert docs_list_report_response.data["size"] is None
        assert docs_list_report_response.data["mime_type"] == ""
        assert docs_list_report_response.data["url"] is not None
        assert docs_list_report_response.data["status"] == "not_virus_scanned"
        assert docs_list_report_response.data["signed_upload_url"] is not None

    def test_add_document_with_size(self):
        """Test add a document with size"""
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url,
            format="json",
            data={"original_filename": "somefile.pdf", "size": 2},
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        assert docs_list_report_response.data["original_filename"] == "somefile.pdf"
        assert docs_list_report_response.data["id"] is not None
        assert docs_list_report_response.data["size"] == 2
        assert docs_list_report_response.data["mime_type"] == ""
        assert docs_list_report_response.data["url"] is not None
        assert docs_list_report_response.data["status"] == "not_virus_scanned"
        assert docs_list_report_response.data["signed_upload_url"] is not None

    @pytest.mark.skip(
        reason="it was not being picked up by the runner due to the leading _"
    )
    def test_add_document_with__size_mime_type(self):
        """Test add a document with size and mime type"""
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url,
            format="json",
            data={"original_filename": "somefile.pdf", "size": 2, "mine_type": "mime"},
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        assert docs_list_report_response.data["original_filename"] == "somefile.pdf"
        assert docs_list_report_response.data["id"] is not None
        assert docs_list_report_response.data["size"] == 2
        assert docs_list_report_response.data["mime_type"] == "mime"
        assert docs_list_report_response.data["url"] is not None
        assert docs_list_report_response.data["status"] == "not_virus_scanned"
        assert docs_list_report_response.data["signed_upload_url"] is not None

    def test_add_interactions_with_document(self):
        """Test add interaction with a document"""
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id = docs_list_report_response.data["id"]

        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={"text": "sample interaction notes", "documents": [document_id]},
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert get_int_response.data["documents"] is not None
        assert get_int_response.data["documents"][0]["id"] == uuid.UUID(document_id)

    def test_add_interactions_with_clear_documents(self):
        """Test add interaction with documents and edit to clear them"""
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id = docs_list_report_response.data["id"]

        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={"text": "sample interaction notes", "documents": [document_id]},
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert get_int_response.data["documents"] is not None
        assert get_int_response.data["documents"][0]["id"] == uuid.UUID(document_id)

        edit_int_response = self.api_client.put(
            get_interaction_url, format="json", data={"documents": []}
        )
        assert edit_int_response.status_code == status.HTTP_200_OK

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["documents"] == []

    def test_add_interactions_change_document(self):
        """Test add interaction with document and edit to change document"""
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        somefile_id = docs_list_report_response.data["id"]

        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "anotherfile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        anotherfile_id = docs_list_report_response.data["id"]

        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={"text": "sample interaction notes", "documents": [somefile_id]},
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert get_int_response.data["documents"] is not None
        assert get_int_response.data["documents"][0]["id"] == uuid.UUID(somefile_id)

        edit_int_response = self.api_client.put(
            get_interaction_url, format="json", data={"documents": [anotherfile_id]}
        )
        assert edit_int_response.status_code == status.HTTP_200_OK

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["documents"][0]["id"] == uuid.UUID(anotherfile_id)

    def test_add_interactions_with_multiple_documents(self):
        """Test add an interaction with multiple documents"""
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        somefile_id = docs_list_report_response.data["id"]

        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "otherfile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        otherfile_id = docs_list_report_response.data["id"]

        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={
                "text": "sample interaction notes",
                "documents": [somefile_id, otherfile_id],
            },
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert get_int_response.data["documents"] is not None
        assert get_int_response.data["documents"][0]["id"] == uuid.UUID(somefile_id)
        assert get_int_response.data["documents"][1]["id"] == uuid.UUID(otherfile_id)

    def test_add_interactions_change_multiple_documents(self):
        """Test add an interaction with multiple documents and change them to be different"""
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "file1.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        file1_id = docs_list_report_response.data["id"]

        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "file2.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        file2_id = docs_list_report_response.data["id"]

        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "file3.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        file3_id = docs_list_report_response.data["id"]

        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "file4.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        file4_id = docs_list_report_response.data["id"]

        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={
                "text": "sample interaction notes",
                "documents": [file1_id, file2_id],
            },
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert get_int_response.data["documents"] is not None
        assert get_int_response.data["documents"][0]["id"] == uuid.UUID(file1_id)
        assert get_int_response.data["documents"][1]["id"] == uuid.UUID(file2_id)

        edit_int_response = self.api_client.put(
            get_interaction_url, format="json", data={"documents": [file3_id, file4_id]}
        )
        assert edit_int_response.status_code == status.HTTP_200_OK

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["documents"][0]["id"] == uuid.UUID(file3_id)
        assert get_int_response.data["documents"][1]["id"] == uuid.UUID(file4_id)

    def test_add_interactions_change_add_another_document(self):
        """Test add interaction with a document and edit to add one more document"""
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "file1.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        file1_id = docs_list_report_response.data["id"]

        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "file2.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        file2_id = docs_list_report_response.data["id"]

        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "file3.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        file3_id = docs_list_report_response.data["id"]

        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "file4.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        file4_id = docs_list_report_response.data["id"]

        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={
                "text": "sample interaction notes",
                "documents": [file1_id, file2_id],
            },
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert get_int_response.data["documents"] is not None
        assert get_int_response.data["documents"][0]["id"] == uuid.UUID(file1_id)
        assert get_int_response.data["documents"][1]["id"] == uuid.UUID(file2_id)

        edit_int_response = self.api_client.put(
            get_interaction_url,
            format="json",
            data={"documents": [file1_id, file2_id, file3_id, file4_id]},
        )
        assert edit_int_response.status_code == status.HTTP_200_OK

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["documents"][0]["id"] == uuid.UUID(file1_id)
        assert get_int_response.data["documents"][1]["id"] == uuid.UUID(file2_id)
        assert get_int_response.data["documents"][2]["id"] == uuid.UUID(file3_id)
        assert get_int_response.data["documents"][3]["id"] == uuid.UUID(file4_id)

    def test_archive_interaction(self):
        """Test archiving an interaction"""
        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url, format="json", data={"text": "sample interaction notes"}
        )
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is False
        assert int_response.data["results"][0]["is_active"] is True

        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True

        delete_int_response = self.api_client.delete(get_interaction_url)
        assert delete_int_response.status_code == status.HTTP_204_NO_CONTENT

        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_404_NOT_FOUND

    def test_archive_edited_interaction(self):
        """Test archiving an edited interaction"""
        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url, format="json", data={"text": "sample interaction notes"}
        )
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is False
        assert int_response.data["results"][0]["is_active"] is True

        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True

        edit_int_response = self.api_client.put(
            get_interaction_url,
            format="json",
            data={"text": "edited interaction notes"},
        )
        assert edit_int_response.status_code == status.HTTP_200_OK

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "edited interaction notes"

        delete_int_response = self.api_client.delete(get_interaction_url)
        assert delete_int_response.status_code == status.HTTP_204_NO_CONTENT

        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_404_NOT_FOUND

    def test_archive_interactions_with_document(self):
        """Test archive interaction with a document"""
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id = docs_list_report_response.data["id"]

        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={"text": "sample interaction notes", "documents": [document_id]},
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert get_int_response.data["documents"] is not None
        assert get_int_response.data["documents"][0]["id"] == uuid.UUID(document_id)

        delete_int_response = self.api_client.delete(get_interaction_url)
        assert delete_int_response.status_code == status.HTTP_204_NO_CONTENT

        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_interactions_null_document(self):
        """Test there is one interaction without pinning"""
        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        json_string = u'{"text": "sample interaction notes", "documents":null}'
        add_int_response = self.api_client.post(
            interactions_url, format="json", data=json.loads(json_string)
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is False
        assert int_response.data["results"][0]["is_active"] is True

    def test_add_interactions_with_edit_text_clear_documents_with_null(self):
        """Test add interaction with documents and edit to clear them"""
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id = docs_list_report_response.data["id"]

        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={"text": "sample interaction notes", "documents": [document_id]},
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert get_int_response.data["documents"] is not None
        assert get_int_response.data["documents"][0]["id"] == uuid.UUID(document_id)

        json_string = u'{"text": "edited sample interaction notes", "documents":null}'
        edit_int_response = self.api_client.put(
            get_interaction_url, format="json", data=json.loads(json_string)
        )
        assert edit_int_response.status_code == status.HTTP_200_OK

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "edited sample interaction notes"
        assert get_int_response.data["documents"] == []

    def test_add_interactions_with_clear_documents_with_null(self):
        """Test add interaction with documents and edit to clear them"""
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id = docs_list_report_response.data["id"]

        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={"text": "sample interaction notes", "documents": [document_id]},
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert get_int_response.data["documents"] is not None
        assert get_int_response.data["documents"][0]["id"] == uuid.UUID(document_id)

        json_string = u'{"documents":null}'
        edit_int_response = self.api_client.put(
            get_interaction_url, format="json", data=json.loads(json_string)
        )
        assert edit_int_response.status_code == status.HTTP_200_OK

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["documents"] == []

    def test_add_interactions_with_document_check_deleting_document(self):
        """
        Test add interaction with a document
        Attempt to delete the document while it was attached
        to an interaction
        It shouldn't be allowed, expect 400
        """
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id = docs_list_report_response.data["id"]

        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={"text": "sample interaction notes", "documents": [document_id]},
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert len(get_int_response.data["documents"]) > 0
        assert get_int_response.data["documents"][0]["id"] == uuid.UUID(document_id)

        get_doc_url = reverse(
            "barrier-document-item", kwargs={"entity_document_pk": document_id}
        )
        get_doc_response = self.api_client.get(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_200_OK

        get_doc_response = self.api_client.delete(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_400_BAD_REQUEST

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert len(get_int_response.data["documents"]) == 1

        get_doc_response = self.api_client.get(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_200_OK

        doc = Document.objects.get(id=document_id)
        assert doc.detached is False

    def test_check_deleting_document_when_not_attached_to_interaction(self):
        """
        Test deleting a document when it was not attached to an interaction
        It should be deleted fully
        """
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id = docs_list_report_response.data["id"]

        get_doc_url = reverse(
            "barrier-document-item", kwargs={"entity_document_pk": document_id}
        )
        get_doc_response = self.api_client.get(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_200_OK

        get_doc_response = self.api_client.delete(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_204_NO_CONTENT

        get_doc_response = self.api_client.get(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_404_NOT_FOUND

    def test_edit_interaction_remove_a_document_check_detach(self):
        """
        Test add interaction with two documents
        edit interaction, remove one of them
        check if that document is now detached and the other is not
        """
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile1.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id_1 = docs_list_report_response.data["id"]

        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile2.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id_2 = docs_list_report_response.data["id"]

        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={
                "text": "sample interaction notes",
                "documents": [document_id_1, document_id_2],
            },
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert len(get_int_response.data["documents"]) == 2

        get_doc_url = reverse(
            "barrier-document-item", kwargs={"entity_document_pk": document_id_1}
        )
        get_doc_response = self.api_client.get(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_200_OK

        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert len(get_int_response.data["documents"]) == 2

        get_doc_response = self.api_client.get(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_200_OK

        doc = Document.objects.get(id=document_id_1)
        assert doc.detached is False

        doc = Document.objects.get(id=document_id_2)
        assert doc.detached is False

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert len(get_int_response.data["documents"]) == 2

        int_id = int_response.data["results"][0]["id"]

        json_string = u'{"documents":null}'
        edit_int_response = self.api_client.put(
            get_interaction_url,
            format="json",
            data={"documents": [document_id_1]},
        )
        assert edit_int_response.status_code == status.HTTP_200_OK

        doc = Document.objects.get(id=document_id_1)
        assert doc.detached is False

        doc = Document.objects.get(id=document_id_2)
        assert doc.detached is True

    def test_delete_detached_document(self):
        """
        Test add interaction with a document
        Attempt to delete a detached document
        It should not be deleted
        """
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile1.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id_1 = docs_list_report_response.data["id"]

        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile2.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id_2 = docs_list_report_response.data["id"]

        response = self._submit_report(self.report)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": self.report.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(
            interactions_url,
            format="json",
            data={
                "text": "sample interaction notes",
                "documents": [document_id_1, document_id_2],
            },
        )

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert len(get_int_response.data["documents"]) == 2

        get_doc_url = reverse(
            "barrier-document-item", kwargs={"entity_document_pk": document_id_1}
        )
        get_doc_response = self.api_client.get(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_200_OK

        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert len(get_int_response.data["documents"]) == 2

        get_doc_response = self.api_client.get(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_200_OK

        doc = Document.objects.get(id=document_id_1)
        assert doc.detached is False

        doc = Document.objects.get(id=document_id_2)
        assert doc.detached is False

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True
        assert len(get_int_response.data["documents"]) == 2

        int_id = int_response.data["results"][0]["id"]

        json_string = u'{"documents":null}'
        edit_int_response = self.api_client.put(
            get_interaction_url,
            format="json",
            data={"documents": [document_id_1]},
        )
        assert edit_int_response.status_code == status.HTTP_200_OK

        doc = Document.objects.get(id=document_id_1)
        assert doc.detached is False

        doc = Document.objects.get(id=document_id_2)
        assert doc.detached is True

        get_doc_url = reverse(
            "barrier-document-item", kwargs={"entity_document_pk": document_id_2}
        )
        get_doc_response = self.api_client.get(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_200_OK

        get_doc_response = self.api_client.delete(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_204_NO_CONTENT

        get_doc_response = self.api_client.get(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_200_OK
