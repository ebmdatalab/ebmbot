import csv
import json
from unittest.mock import patch

from workspace.techsupport.jobs import report_rota


@patch("workspace.techsupport.jobs.TechSupportRotaReporter.get_rota_data_from_sheet")
def test_rota_report_on_monday(get_rota_data_from_sheet, freezer):
    freezer.move_to("2023-07-24")
    with open("tests/workspace/tech-support-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {"text": {"text": "Tech support rota", "type": "plain_text"}, "type": "header"},
        {
            "text": {
                "text": "Primary tech support this week (24 Jul-28 Jul): Iain (secondary: Peter, Steve)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "text": {
                "text": "Primary tech support next week (31 Jul-04 Aug): Ben (secondary: Becky)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://docs.google.com/spreadsheets/d/1q6EzPQ9iG9Rb-VoYvylObhsJBckXuQdt3Y_pOGysxG8|Open rota spreadsheet>",
            },
        },
    ]


@patch("workspace.techsupport.jobs.TechSupportRotaReporter.get_rota_data_from_sheet")
def test_rota_report_on_tuesday(get_rota_data_from_sheet, freezer):
    freezer.move_to("2023-07-25")
    with open("tests/workspace/tech-support-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {"text": {"text": "Tech support rota", "type": "plain_text"}, "type": "header"},
        {
            "text": {
                "text": "Primary tech support this week (24 Jul-28 Jul): Iain (secondary: Peter, Steve)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "text": {
                "text": "Primary tech support next week (31 Jul-04 Aug): Ben (secondary: Becky)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://docs.google.com/spreadsheets/d/1q6EzPQ9iG9Rb-VoYvylObhsJBckXuQdt3Y_pOGysxG8|Open rota spreadsheet>",
            },
        },
    ]


@patch("workspace.techsupport.jobs.TechSupportRotaReporter.get_rota_data_from_sheet")
def test_rota_report_with_no_future_dates(get_rota_data_from_sheet, freezer):
    freezer.move_to("2024-01-08")
    with open("tests/workspace/tech-support-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {"text": {"text": "Tech support rota", "type": "plain_text"}, "type": "header"},
        {
            "text": {
                "text": "No rota data found for this week",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "text": {
                "text": "No rota data found for next week",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://docs.google.com/spreadsheets/d/1q6EzPQ9iG9Rb-VoYvylObhsJBckXuQdt3Y_pOGysxG8|Open rota spreadsheet>",
            },
        },
    ]
