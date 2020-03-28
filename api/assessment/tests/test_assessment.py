import pytest
import uuid

from rest_framework import status
from rest_framework.reverse import reverse

from api.assessment.models import Assessment
from api.barriers.models import BarrierInstance
from api.barriers.tests.test_utils import TestUtils
from api.core.test_utils import APITestMixin, create_test_user
from api.interactions.models import Document

pytestmark = [
    pytest.mark.django_db
]


class TestAssessment(APITestMixin):
    @pytest.fixture
    def setup_barrier(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "status_summary": "some status summary",
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK
        return instance.id

    def test_no_assessment(self, setup_barrier):
        instance_id = setup_barrier
        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_assessment_no_fields(self, setup_barrier):
        instance_id = setup_barrier

        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={}
        )

        assert add_response.status_code == status.HTTP_201_CREATED

    def test_add_economic_assessment_no_docs(self, setup_barrier):
        instance_id = setup_barrier

        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={
                "impact": "MEDIUMHIGH",
                "explanation": "sample assessment notes"
            }
        )

        assert add_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] == "MEDIUMHIGH"
        assert int_response.data["explanation"] == "sample assessment notes"
        assert int_response.data["documents"] == []
        assert int_response.data["value_to_economy"] is None
        assert int_response.data["import_market_size"] is None
        assert int_response.data["commercial_value"] is None
        assert int_response.data["export_value"] is None

        url = reverse("assessment-history", kwargs={"pk": instance_id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barrier_id"] == str(instance_id)
        assert len(response.data["history"]) == 1
        assert response.data["history"][0]["field"] == "impact"
        assert response.data["history"][0]["old_value"] is None
        assert response.data["history"][0]["new_value"] == "MEDIUMHIGH"


    def test_add_assessment_with_document(self, setup_barrier):
        instance_id = setup_barrier

        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id = docs_list_report_response.data["id"]

        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={
                "impact": "MEDIUMHIGH",
                "explanation": "sample assessment notes",
                "documents": [document_id],
            }
        )

        assert add_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] == "MEDIUMHIGH"
        assert int_response.data["explanation"] == "sample assessment notes"
        assert int_response.data["documents"] is not None
        assert len(int_response.data["documents"]) == 1
        assert int_response.data["documents"][0]["id"] == uuid.UUID(document_id)
        assert int_response.data["value_to_economy"] is None
        assert int_response.data["import_market_size"] is None
        assert int_response.data["commercial_value"] is None
        assert int_response.data["export_value"] is None

    def test_add_assessment_with_multiple_documents(self, setup_barrier):
        instance_id = setup_barrier

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

        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={
                "impact": "MEDIUMHIGH",
                "explanation": "sample assessment notes",
                "documents": [somefile_id, otherfile_id],
            }
        )
        assert add_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] == "MEDIUMHIGH"
        assert int_response.data["explanation"] == "sample assessment notes"
        assert int_response.data["documents"] is not None
        assert len(int_response.data["documents"]) == 2
        assert int_response.data["documents"][0]["id"] == uuid.UUID(somefile_id)
        assert int_response.data["documents"][1]["id"] == uuid.UUID(otherfile_id)
        assert int_response.data["value_to_economy"] is None
        assert int_response.data["import_market_size"] is None
        assert int_response.data["commercial_value"] is None
        assert int_response.data["export_value"] is None

    def test_add_value_to_uk_economy(self, setup_barrier):
        instance_id = setup_barrier

        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={
                "value_to_economy": 1500000,
            }
        )

        assert add_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] is None
        assert int_response.data["explanation"] is None
        assert int_response.data["documents"] == []
        assert int_response.data["value_to_economy"] == 1500000
        assert int_response.data["import_market_size"] is None
        assert int_response.data["commercial_value"] is None
        assert int_response.data["export_value"] is None

    def test_add_import_market_size(self, setup_barrier):
        instance_id = setup_barrier

        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={
                "import_market_size": 1500000,
            }
        )

        assert add_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] is None
        assert int_response.data["explanation"] is None
        assert int_response.data["documents"] == []
        assert int_response.data["value_to_economy"] is None
        assert int_response.data["import_market_size"] == 1500000
        assert int_response.data["commercial_value"] is None
        assert int_response.data["export_value"] is None

    def test_add_value_of_currently_affected_uk_exports(self, setup_barrier):
        instance_id = setup_barrier

        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={
                "export_value": 1500000,
            }
        )

        assert add_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] is None
        assert int_response.data["explanation"] is None
        assert int_response.data["documents"] == []
        assert int_response.data["value_to_economy"] is None
        assert int_response.data["import_market_size"] is None
        assert int_response.data["commercial_value"] is None
        assert int_response.data["export_value"] == 1500000

    def test_add_commercial_value(self, setup_barrier):
        instance_id = setup_barrier

        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={
                "commercial_value": 1500000,
            }
        )

        assert add_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] is None
        assert int_response.data["explanation"] is None
        assert int_response.data["documents"] == []
        assert int_response.data["value_to_economy"] is None
        assert int_response.data["import_market_size"] is None
        assert int_response.data["commercial_value"] == 1500000
        assert int_response.data["export_value"] is None

    def test_add_eco_assessment_edit_add_rest(self, setup_barrier):
        instance_id = setup_barrier

        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id = docs_list_report_response.data["id"]

        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={
                "impact": "MEDIUMHIGH",
                "explanation": "sample assessment notes",
                "documents": [document_id],
            }
        )
        assert add_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] == "MEDIUMHIGH"
        assert int_response.data["explanation"] == "sample assessment notes"
        assert int_response.data["documents"] is not None
        assert len(int_response.data["documents"]) == 1
        assert int_response.data["documents"][0]["id"] == uuid.UUID(document_id)
        assert int_response.data["value_to_economy"] is None
        assert int_response.data["import_market_size"] is None
        assert int_response.data["commercial_value"] is None
        assert int_response.data["export_value"] is None

        edit_response = self.api_client.patch(
            assessment_url, format="json", data={
                "value_to_economy": 1500000,
                "import_market_size": 1500000,
                "commercial_value": 1500000,
                "export_value": 1500000,
            }
        )
        assert edit_response.status_code == status.HTTP_200_OK
        assert edit_response.data["impact"] == "MEDIUMHIGH"
        assert edit_response.data["explanation"] == "sample assessment notes"
        assert edit_response.data["documents"] is not None
        assert len(edit_response.data["documents"]) == 1
        assert edit_response.data["documents"][0]["id"] == uuid.UUID(document_id)
        assert edit_response.data["value_to_economy"] == 1500000
        assert edit_response.data["import_market_size"] == 1500000
        assert edit_response.data["commercial_value"] == 1500000
        assert edit_response.data["export_value"] == 1500000

    def test_add_assessment_with_document_edit_clear_doc(self, setup_barrier):
        instance_id = setup_barrier

        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        somefile_id = docs_list_report_response.data["id"]

        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={
                "impact": "MEDIUMHIGH",
                "explanation": "sample assessment notes",
                "documents": [somefile_id],
            }
        )
        assert add_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] == "MEDIUMHIGH"
        assert int_response.data["explanation"] == "sample assessment notes"
        assert int_response.data["documents"] is not None
        assert len(int_response.data["documents"]) == 1
        assert int_response.data["documents"][0]["id"] == uuid.UUID(somefile_id)
        assert int_response.data["value_to_economy"] is None
        assert int_response.data["import_market_size"] is None
        assert int_response.data["commercial_value"] is None
        assert int_response.data["export_value"] is None

        edit_response = self.api_client.patch(
            assessment_url, format="json", data={
                "value_to_economy": 1500000,
                "import_market_size": 1500000,
                "commercial_value": 1500000,
                "export_value": 1500000,
            }
        )
        assert edit_response.status_code == status.HTTP_200_OK
        assert edit_response.data["impact"] == "MEDIUMHIGH"
        assert edit_response.data["explanation"] == "sample assessment notes"
        assert edit_response.data["documents"] is not None
        assert len(edit_response.data["documents"]) == 1
        assert edit_response.data["documents"][0]["id"] == uuid.UUID(somefile_id)
        assert edit_response.data["value_to_economy"] == 1500000
        assert edit_response.data["import_market_size"] == 1500000
        assert edit_response.data["commercial_value"] == 1500000
        assert edit_response.data["export_value"] == 1500000

        edit_doc_response = self.api_client.patch(
            assessment_url, format="json", data={"documents": []}
        )
        assert edit_doc_response.status_code == status.HTTP_200_OK
        assert edit_doc_response.data["impact"] == "MEDIUMHIGH"
        assert edit_doc_response.data["explanation"] == "sample assessment notes"
        assert edit_doc_response.data["documents"] == []
        assert edit_doc_response.data["value_to_economy"] == 1500000
        assert edit_doc_response.data["import_market_size"] == 1500000
        assert edit_doc_response.data["commercial_value"] == 1500000
        assert edit_doc_response.data["export_value"] == 1500000

    def test_add_assessment_with_multiple_documents_remove_one(self, setup_barrier):
        instance_id = setup_barrier

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

        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={
                "impact": "MEDIUMHIGH",
                "explanation": "sample assessment notes",
                "documents": [somefile_id, otherfile_id],
            }
        )
        assert add_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] == "MEDIUMHIGH"
        assert int_response.data["explanation"] == "sample assessment notes"
        assert int_response.data["documents"] is not None
        assert len(int_response.data["documents"]) == 2
        assert int_response.data["documents"][0]["id"] == uuid.UUID(somefile_id)
        assert int_response.data["documents"][1]["id"] == uuid.UUID(otherfile_id)
        assert int_response.data["value_to_economy"] is None
        assert int_response.data["import_market_size"] is None
        assert int_response.data["commercial_value"] is None
        assert int_response.data["export_value"] is None

        edit_doc_response = self.api_client.patch(
            assessment_url, format="json", data={"documents": [otherfile_id]}
        )
        assert edit_doc_response.status_code == status.HTTP_200_OK
        assert edit_doc_response.data["impact"] == "MEDIUMHIGH"
        assert edit_doc_response.data["explanation"] == "sample assessment notes"
        assert edit_doc_response.data["documents"] is not None
        assert len(edit_doc_response.data["documents"]) == 1
        assert edit_doc_response.data["documents"][0]["id"] == uuid.UUID(otherfile_id)

    def test_add_assessment_with_one_documents_replace(self, setup_barrier):
        instance_id = setup_barrier

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

        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={
                "impact": "MEDIUMHIGH",
                "explanation": "sample assessment notes",
                "documents": [somefile_id],
            }
        )
        assert add_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] == "MEDIUMHIGH"
        assert int_response.data["explanation"] == "sample assessment notes"
        assert int_response.data["documents"] is not None
        assert len(int_response.data["documents"]) == 1
        assert int_response.data["documents"][0]["id"] == uuid.UUID(somefile_id)
        assert int_response.data["value_to_economy"] is None
        assert int_response.data["import_market_size"] is None
        assert int_response.data["commercial_value"] is None
        assert int_response.data["export_value"] is None

        edit_doc_response = self.api_client.patch(
            assessment_url, format="json", data={"documents": [otherfile_id]}
        )
        assert edit_doc_response.status_code == status.HTTP_200_OK
        assert edit_doc_response.data["impact"] == "MEDIUMHIGH"
        assert edit_doc_response.data["explanation"] == "sample assessment notes"
        assert edit_doc_response.data["documents"] is not None
        assert len(edit_doc_response.data["documents"]) == 1
        assert edit_doc_response.data["documents"][0]["id"] == uuid.UUID(otherfile_id)

    def test_add_assessment_with_document_check_deleting_document(self, setup_barrier):
        """
        Test add assessment with a document
        Attempt to delete the document while it was attached
        to assessment
        It shouldn't be allowed, expect 400
        """
        instance_id = setup_barrier
        docs_list_url = reverse("barrier-documents")
        docs_list_report_response = self.api_client.post(
            docs_list_url, format="json", data={"original_filename": "somefile.pdf"}
        )

        assert docs_list_report_response.status_code == status.HTTP_201_CREATED
        document_id = docs_list_report_response.data["id"]

        get_url = reverse("get-barrier", kwargs={"pk": instance_id})
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        assessment_url = reverse("get-assessment", kwargs={"pk": instance_id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={
                "impact": "MEDIUMHIGH",
                "explanation": "sample assessment notes",
                "documents": [document_id],
            }
        )
        assert add_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] == "MEDIUMHIGH"
        assert int_response.data["explanation"] == "sample assessment notes"
        assert int_response.data["documents"] is not None
        assert len(int_response.data["documents"]) == 1
        assert int_response.data["documents"][0]["id"] == uuid.UUID(document_id)
        assert int_response.data["value_to_economy"] is None
        assert int_response.data["import_market_size"] is None
        assert int_response.data["commercial_value"] is None
        assert int_response.data["export_value"] is None

        get_doc_url = reverse(
            "barrier-document-item",
            kwargs={"entity_document_pk": document_id}
        )
        get_doc_response = self.api_client.get(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_200_OK

        get_doc_response = self.api_client.delete(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_400_BAD_REQUEST

        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] == "MEDIUMHIGH"
        assert int_response.data["explanation"] == "sample assessment notes"
        assert int_response.data["documents"] is not None
        assert len(int_response.data["documents"]) == 1
        assert int_response.data["documents"][0]["id"] == uuid.UUID(document_id)

        get_doc_response = self.api_client.get(get_doc_url)
        assert get_doc_response.status_code == status.HTTP_200_OK

        doc = Document.objects.get(id=document_id)
        assert doc.detached is False
