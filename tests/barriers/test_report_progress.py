from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.core.test_utils import APITestMixin
from tests.barriers.factories import MinReportFactory


class ProblemStatus:
    AFFECTING_SINGLE = 1
    AFFECTING_MULTIPLE = 2


class BarrierStatus:
    UNFINISHED = 0
    OPEN_PENDING_ACTION = 1
    OPEN_IN_PROGRESS = 2
    RESOLVED_IN_PART = 3
    RESOLVED_IN_FULL = 4
    DORMANT = 5
    ARCHIVED = 6
    UNKNOWN = 7


class TradeDirections:
    EXPORT = 1
    IMPORT = 2


class BaseReportTestCase(APITestMixin, APITestCase):
    STAGE_1 = "1.1"
    STAGE_2 = "1.2"
    STAGE_3 = "1.3"
    STAGE_4 = "1.4"
    STAGE_5 = "1.5"

    IN_PROGRESS = "IN PROGRESS"
    NOT_STARTED = "NOT STARTED"
    COMPLETED = "COMPLETED"

    def _stage(self, response, code):
        return [d for d in response.data["progress"] if d["stage_code"] == code][0]

    def _stage_status(self, response, code):
        return self._stage(response, code).get("status_desc")

    def _patch_report(self, report, payload):
        url = reverse("get-report", kwargs={"pk": report.id})
        self.api_client.put(url, format="json", data=payload)
        report.refresh_from_db()

    def _get_report(self, report):
        url = reverse("get-report", kwargs={"pk": report.id})
        return self.api_client.get(url)

    def _submit_report(self, report):
        url = reverse("submit-report", kwargs={"pk": report.id})
        return self.api_client.put(url)


class TestReportProgress(BaseReportTestCase):

    def test_zero_progress(self):
        report = MinReportFactory()
        url = reverse("get-report", kwargs={"pk": report.id})
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert not response.data["progress"]

    def test_report_progress__stage_1(self):
        """
        Add to test_parameters to check the status of Stage 1 after patching
        the report (draft barrier) with the payload provided in the case.

        Hints:
         - provide a case number to each item so it's easy to spot which one failed
         - increment test cases by 10 so it'll be easier to add an extra item in between cases

         Reports can only be submitted if ALL stages are COMPLETED!
        """
        test_parameters = (
            {
                "case": 0,
                "payload": {
                    "term": ProblemStatus.AFFECTING_SINGLE,
                },
                "expected_status": self.IN_PROGRESS
            },
            {
                "case": 10,
                "hint": "It remains NOT_STARTED because UNFINISHED is the default for status.",
                "payload": {
                    "status": BarrierStatus.UNFINISHED,
                },
                "expected_status": self.NOT_STARTED
            },
            {
                "case": 11,
                "payload": {
                    "term": ProblemStatus.AFFECTING_SINGLE,
                    "status": BarrierStatus.UNFINISHED,
                },
                "expected_status": self.IN_PROGRESS
            },
            {
                "case": 20,
                "hints": "Cannot get COMPLETED without problem_status.",
                "payload": {
                    "term": None,
                    "status": BarrierStatus.OPEN_PENDING_ACTION,
                },
                "expected_status": self.IN_PROGRESS
            },
            {
                "case": 30,
                "payload": {
                    "term": ProblemStatus.AFFECTING_SINGLE,
                    "status": BarrierStatus.OPEN_PENDING_ACTION,
                },
                "expected_status": self.COMPLETED
            },
            {
                "case": 40,
                "hints": "Cannot get COMPLETED without status_date and status_summary.",
                "payload": {
                    "term": ProblemStatus.AFFECTING_MULTIPLE,
                    "status": BarrierStatus.RESOLVED_IN_FULL,
                },
                "expected_status": self.IN_PROGRESS
            },
            {
                "case": 50,
                "hints": "Cannot get COMPLETED without status_summary.",
                "payload": {
                    "term": ProblemStatus.AFFECTING_SINGLE,
                    "status": BarrierStatus.RESOLVED_IN_FULL,
                    "status_date": "2020-02-02",
                },
                "expected_status": self.IN_PROGRESS
            },
            {
                "case": 60,
                "payload": {
                    "term": ProblemStatus.AFFECTING_SINGLE,
                    "status": BarrierStatus.RESOLVED_IN_FULL,
                    "status_date": "2020-02-02",
                    "status_summary": "wibble wobble"
                },
                "expected_status": self.COMPLETED
            },
        )

        for tp in test_parameters:
            with self.subTest(tp=tp):
                report = MinReportFactory()
                self._patch_report(report, tp["payload"])

                response = self._get_report(report)

                assert status.HTTP_200_OK == response.status_code
                assert tp["expected_status"] == self._stage_status(response, self.STAGE_1), \
                    f"Failed at case {tp['case']}\n" \
                    f"Expected Stage 1 to be {tp['expected_status']}\n" \
                    f"Payload used {tp['payload']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_2), f"Case {tp['case']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_3), f"Case {tp['case']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_4), f"Case {tp['case']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_5), f"Case {tp['case']}"

                r = self._submit_report(report)
                assert status.HTTP_400_BAD_REQUEST == r.status_code, f"Case {tp['case']}"

    def test_report_progress__stage_2(self):
        """
        Add to test_parameters to check the status of Stage 2 after patching
        the report (draft barrier) with the payload provided in the case.
        Hints:
         - provide a case number to each item so it's easy to spot which one failed
         - increment test cases by 10 so it'll be easier to add an extra item in between cases
        """
        test_parameters = (
            {
                "case": 0,
                "payload": {
                    "country": "82756b9a-5d95-e211-a939-e4115bead28a",
                },
                "expected_status": self.IN_PROGRESS
            },
            {
                "case": 10,
                "payload": {
                    "country": "82756b9a-5d95-e211-a939-e4115bead28a",
                    "trade_direction": TradeDirections.EXPORT
                },
                "expected_status": self.COMPLETED
            },
        )

        for tp in test_parameters:
            with self.subTest(tp=tp):
                report = MinReportFactory()
                self._patch_report(report, tp["payload"])

                response = self._get_report(report)

                assert status.HTTP_200_OK == response.status_code
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_1), f"Case {tp['case']}"
                assert tp["expected_status"] == self._stage_status(response, self.STAGE_2), \
                    f"Failed at case {tp['case']}\n" \
                    f"Expected Stage 2 to be {tp['expected_status']}\n" \
                    f"Payload used {tp['payload']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_3), f"Case {tp['case']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_4), f"Case {tp['case']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_5), f"Case {tp['case']}"

                r = self._submit_report(report)
                assert status.HTTP_400_BAD_REQUEST == r.status_code, f"Case {tp['case']}"

    def test_report_progress__stage_3(self):
        """
        Add to test_parameters to check the status of Stage 3 after patching
        the report (draft barrier) with the payload provided in the case.
        Hints:
         - provide a case number to each item so it's easy to spot which one failed
         - increment test cases by 10 so it'll be easier to add an extra item in between cases
        """
        test_parameters = (
            {
                "case": 0,
                "payload": {
                    "sectors_affected": True,
                },
                "expected_status": self.COMPLETED
            },
            {
                "case": 10,
                "payload": {
                    "sectors_affected": False,
                },
                "expected_status": self.COMPLETED
            },
            {
                "case": 20,
                "payload": {
                    "sectors_affected": True,
                    "sectors": [
                        "af959812-6095-e211-a939-e4115bead28a",
                        "9538cecc-5f95-e211-a939-e4115bead28a",
                    ],
                },
                "expected_status": self.COMPLETED
            },
            {
                "case": 30,
                "payload": {
                    "sectors_affected": True,
                    "all_sectors": True,
                    "sectors": [],
                },
                "expected_status": self.COMPLETED
            },
        )

        for tp in test_parameters:
            with self.subTest(tp=tp):
                report = MinReportFactory()
                self._patch_report(report, tp["payload"])

                response = self._get_report(report)

                assert status.HTTP_200_OK == response.status_code
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_1), f"Case {tp['case']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_2), f"Case {tp['case']}"
                assert tp["expected_status"] == self._stage_status(response, self.STAGE_3), \
                    f"Failed at case {tp['case']}\n" \
                    f"Expected Stage 3 to be {tp['expected_status']}\n" \
                    f"Payload used {tp['payload']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_4), f"Case {tp['case']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_5), f"Case {tp['case']}"

                r = self._submit_report(report)
                assert status.HTTP_400_BAD_REQUEST == r.status_code, f"Case {tp['case']}"

    def test_report_progress__stage_4(self):
        """
        Add to test_parameters to check the status of Stage 4 after patching
        the report (draft barrier) with the payload provided in the case.
        Hints:
         - provide a case number to each item so it's easy to spot which one failed
         - increment test cases by 10 so it'll be easier to add an extra item in between cases
        """
        test_parameters = (
            {
                "case": 0,
                "payload": {
                    "product": "wibble",
                },
                "expected_status": self.IN_PROGRESS
            },
            {
                "case": 10,
                "payload": {
                    "source": "GOVT",
                },
                "expected_status": self.IN_PROGRESS
            },
            {
                "case": 20,
                "payload": {
                    "source": "OTHER",
                },
                "expected_status": self.IN_PROGRESS
            },
            {
                "case": 30,
                "payload": {
                    "title": "Wibble wobble",
                },
                "expected_status": self.IN_PROGRESS
            },
            {
                "case": 40,
                "payload": {
                    "product": "Wibble",
                    "source": "OTHER",
                    "title": "WOBBLE!",
                },
                "expected_status": self.IN_PROGRESS
            },
            {
                "case": 50,
                "payload": {
                    "product": "Wibble",
                    "source": "OTHER",
                    "other_source": "happy happy",
                    "title": "WOBBLE!",
                },
                "expected_status": self.COMPLETED
            },
            {
                "case": 50,
                "payload": {
                    "product": "Wibble",
                    "source": "GOVT",
                    "title": "Yarp",
                },
                "expected_status": self.COMPLETED
            },
        )

        for tp in test_parameters:
            with self.subTest(tp=tp):
                report = MinReportFactory()
                self._patch_report(report, tp["payload"])

                response = self._get_report(report)

                assert status.HTTP_200_OK == response.status_code
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_1), f"Case {tp['case']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_2), f"Case {tp['case']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_3), f"Case {tp['case']}"
                assert tp["expected_status"] == self._stage_status(response, self.STAGE_4), \
                    f"Failed at case {tp['case']}\n" \
                    f"Expected Stage 4 to be {tp['expected_status']}\n" \
                    f"Payload used {tp['payload']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_5), f"Case {tp['case']}"

                r = self._submit_report(report)
                assert status.HTTP_400_BAD_REQUEST == r.status_code, f"Case {tp['case']}"

    def test_report_progress__stage_5(self):
        """
        Add to test_parameters to check the status of Stage 5 after patching
        the report (draft barrier) with the payload provided in the case.
        Hints:
         - provide a case number to each item so it's easy to spot which one failed
         - increment test cases by 10 so it'll be easier to add an extra item in between cases
        """
        test_parameters = (
            {
                "case": 0,
                "payload": {
                    "summary": "Summary by Mary Sum.",
                },
                "expected_status": self.COMPLETED
            },
        )

        for tp in test_parameters:
            with self.subTest(tp=tp):
                report = MinReportFactory()
                self._patch_report(report, tp["payload"])

                response = self._get_report(report)

                assert status.HTTP_200_OK == response.status_code
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_1), f"Case {tp['case']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_2), f"Case {tp['case']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_3), f"Case {tp['case']}"
                assert self.NOT_STARTED == self._stage_status(response, self.STAGE_4), f"Case {tp['case']}"
                assert tp["expected_status"] == self._stage_status(response, self.STAGE_5), \
                    f"Failed at case {tp['case']}\n" \
                    f"Expected Stage 5 to be {tp['expected_status']}\n" \
                    f"Payload used {tp['payload']}"

                r = self._submit_report(report)
                assert status.HTTP_400_BAD_REQUEST == r.status_code, f"Case {tp['case']}"

    def test_report_progress__all_stages_completed(self):
        """
        Add to test_parameters to check that all stages are COMPLETED after patching
        the report (draft barrier) with the payload provided in the case.
        Hints:
         - provide a case number to each item so it's easy to spot which one failed
         - increment test cases by 10 so it'll be easier to add an extra item in between cases
        """
        test_parameters = (
            {
                "case": 0,
                "payload": {
                    "term": ProblemStatus.AFFECTING_MULTIPLE,
                    "status": BarrierStatus.OPEN_PENDING_ACTION,
                    "country": "82756b9a-5d95-e211-a939-e4115bead28a",
                    "trade_direction": TradeDirections.IMPORT,
                    "sectors_affected": True,
                    "all_sectors": True,
                    "sectors": [],
                    "product": "Some product",
                    "source": "GOVT",
                    "title": "Some title",
                    "summary": "Some summary",
                },
            },
            {
                "case": 10,
                "payload": {
                    "term": ProblemStatus.AFFECTING_SINGLE,
                    "status": BarrierStatus.RESOLVED_IN_FULL,
                    "status_date": "2020-02-02",
                    "status_summary": "wibble wobble",
                    "country": "82756b9a-5d95-e211-a939-e4115bead28a",
                    "trade_direction": TradeDirections.EXPORT,
                    "sectors_affected": True,
                    "sectors": [
                        "af959812-6095-e211-a939-e4115bead28a",
                        "9538cecc-5f95-e211-a939-e4115bead28a",
                    ],
                    "product": "Some product",
                    "source": "OTHER",
                    "other_source": "Other source",
                    "title": "Some title",
                    "summary": "Some summary by Mary Sum.",
                },
            },
        )

        for tp in test_parameters:
            with self.subTest(tp=tp):
                report = MinReportFactory()
                self._patch_report(report, tp["payload"])

                response = self._get_report(report)

                assert status.HTTP_200_OK == response.status_code
                assert self.COMPLETED == self._stage_status(response, self.STAGE_1), f"Case {tp['case']}"
                assert self.COMPLETED == self._stage_status(response, self.STAGE_2), f"Case {tp['case']}"
                assert self.COMPLETED == self._stage_status(response, self.STAGE_3), f"Case {tp['case']}"
                assert self.COMPLETED == self._stage_status(response, self.STAGE_4), f"Case {tp['case']}"
                assert self.COMPLETED == self._stage_status(response, self.STAGE_5), f"Case {tp['case']}"

                r = self._submit_report(report)
                assert status.HTTP_200_OK == r.status_code, f"Case {tp['case']}"
