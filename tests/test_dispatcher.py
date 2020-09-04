import os
import shutil
from unittest.mock import Mock

import pytest
from slackbot.slackclient import SlackClient

from ebmbot import scheduler, settings, webserver
from ebmbot.dispatcher import JobDispatcher, run_once

from .assertions import assert_slack_client_sends_messages
from .job_configs import config
from .time_helpers import T0, TS, T

# Make sure all tests run when datetime.now() returning T0
pytestmark = pytest.mark.freeze_time(T0)


@pytest.fixture(autouse=True)
def remove_logs_dir():
    shutil.rmtree(settings.LOGS_DIR, ignore_errors=True)


def test_run_once():
    # Because this mock gets used in a subprocess (I think) we can't actually
    # get any information out of it about how it was used.
    slack_client = Mock()

    scheduler.schedule_suppression("test_good_job", T(-15), T(-5))
    scheduler.schedule_suppression("test_bad_job", T(-15), T(-5))
    scheduler.schedule_suppression("test_really_bad_job", T(-5), T(5))

    scheduler.schedule_job("test_good_job", {}, "channel", TS, 0)
    scheduler.schedule_job("test_bad_job", {}, "channel", TS, 0)
    scheduler.schedule_job("test_really_bad_job", {}, "channel", TS, 0)

    processes = run_once(slack_client, config)

    for p in processes:
        p.join()

    assert os.path.exists(build_log_dir("test_good_job"))
    assert os.path.exists(build_log_dir("test_bad_job"))
    assert not os.path.exists(build_log_dir("test_really_bad_job"))


def test_job_success_with_unsafe_shell_args():
    log_dir = build_log_dir("test_paramaterised_job_2")

    scheduler.schedule_job(
        "test_paramaterised_job_2", {"thing_to_echo": "<poem>"}, "channel", TS, 0
    )
    job = scheduler.reserve_job()
    with assert_slack_client_sends_messages(
        web_api=[("logs", "about to start"), ("channel", "succeeded")]
    ):
        do_job(job)
    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "<poem>\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success():
    log_dir = build_log_dir("test_good_job")

    scheduler.schedule_job("test_good_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    with assert_slack_client_sends_messages(
        web_api=[("logs", "about to start"), ("channel", "succeeded")]
    ):
        do_job(job)

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success_with_parameterised_args():
    log_dir = build_log_dir("test_paramaterised_job")

    scheduler.schedule_job("test_paramaterised_job", {"path": "poem"}, "channel", TS, 0)
    job = scheduler.reserve_job()

    with assert_slack_client_sends_messages(
        web_api=[("logs", "about to start"), ("channel", "succeeded")]
    ):
        do_job(job)

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success_and_report():
    log_dir = build_log_dir("test_reported_job")

    scheduler.schedule_job("test_reported_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    with assert_slack_client_sends_messages(
        web_api=[("logs", "about to start"), ("channel", "the owl")]
    ):
        do_job(job)

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success_with_no_report():
    log_dir = build_log_dir("test_unreported_job")

    scheduler.schedule_job("test_unreported_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    with assert_slack_client_sends_messages(web_api=[("logs", "about to start")]):
        do_job(job)

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_failure():
    log_dir = build_log_dir("test_bad_job")

    scheduler.schedule_job("test_bad_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    with assert_slack_client_sends_messages(
        web_api=[("logs", "about to start"), ("channel", "failed")]
    ):
        do_job(job)

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == ""

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == "cat: no-poem: No such file or directory\n"


def test_job_failure_when_command_not_found():
    log_dir = build_log_dir("test_really_bad_job")

    scheduler.schedule_job("test_really_bad_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    with assert_slack_client_sends_messages(
        web_api=[("logs", "about to start"), ("channel", "failed")]
    ):
        do_job(job)

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == ""

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read().endswith("not found\n")


def test_job_with_callback():
    log_dir = build_log_dir("test_job_to_test_callback")

    scheduler.schedule_job("test_job_to_test_callback", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    with assert_slack_client_sends_messages(
        web_api=[("logs", "about to start"), ("channel", "succeeded")]
    ):
        do_job(job)

    with open(os.path.join(log_dir, "stdout")) as f:
        url = f.read().strip()

    client = webserver.app.test_client()
    with assert_slack_client_sends_messages(web_api=[("channel", "Job done", TS)]):
        rsp = client.post(url, data='{"message": "Job done"}')
        assert rsp.status_code == 200


def do_job(job):
    slack_client = SlackClient("api_token", connect=False)
    job_dispatcher = JobDispatcher(slack_client, job, config)
    job_dispatcher.do_job()


def build_log_dir(job_type_with_namespace):
    return os.path.join(
        settings.LOGS_DIR, job_type_with_namespace, T0.strftime("%Y%m%d-%H%M%S")
    )
