"""
raw_config defines which jobs may be run, and how they can be invoked via
Slack.

It is a dict with one key per namespace, each of which maps to a dict with keys:

    * "jobs": a dict mapping a job_type to a further dict with keys:
        * "run_args_template": template of bash command to be run
        * "report_stdout": optional, whether the stdout of the command is
            reported to Slack
        * "report_success": optional, whether the success of the command is
            reported to Slack
    * "slack": a list of dicts with keys:
        * "command": Slack command which starts the given job
        * "help: help text to display to the user
        * "type": one of "schedule_job", "cancel_job", "schedule_suppression",
            "cancel_suppression"
        * "job_type": the type of the job to be scheduled/supppressed,
            corresponding to an entry in the "jobs" dict
        * "delay_seconds": optional, the delay between the command being issued
            and the job being run
    * "fabfile": optional, the URL of a fabfile which is required to run
        commands in the namespace
"""


import re
from operator import itemgetter

# fmt: off
raw_config = {
    "test": {
        "jobs": {
            "read_poem": {
                "run_args_template": "cat poem",
                "report_stdout": True,
            },
        },
        "slack": [
            {
                "command": "read poem",
                "help": "read a poem",
                "type": "schedule_job",
                "job_type": "read_poem",
                "delay_seconds": 1,
            },
        ],
    },
    "fdaaa": {
        "fabfile": "https://raw.githubusercontent.com/ebmdatalab/clinicaltrials-act-tracker/master/fabfile.py",
        "jobs": {
            "deploy": {
                "run_args_template": "fab update:live",
            },
        },
        "slack": [
            {
                "command": "deploy",
                "help": "copy staging data to live site",
                "type": "schedule_job",
                "job_type": "deploy",
            },
        ],
    },
    "oc": {
        "fabfile": "https://raw.githubusercontent.com/opensafely/opencodelists/master/fabfile.py",
        "jobs": {
            "deploy": {
                "run_args_template": "fab deploy",
                "report_success": True,
            },
        },
        "slack": [
            {
                "command": "deploy",
                "help": "deploy to production after a 60s delay",
                "type": "schedule_job",
                "job_type": "deploy",
            },
        ],
    },
    "op": {
        "fabfile": "https://raw.githubusercontent.com/ebmdatalab/openprescribing/master/fabfile.py",
        "jobs": {
            "deploy": {
                "run_args_template": "fab deploy:production",
                "report_success": False,
            },
            "deploy_staging": {
                "run_args_template": "fab deploy:staging,branch={branch_name}"
            },
            "cache_clear": {
                "run_args_template": "fab clear_cloudflare"
            },
            "ncso_import": {
                "run_args_template": "fab call_management_command:fetch_and_import_ncso_concessions,production"
            },
            "ncso_report": {
                "run_args_template": "fab --hide=running,stdout,status call_management_command:summarise_ncso_concessions,production",
                "report_stdout": True,
            },
            "ncso_reconcile": {
                "run_args_template": "fab --hide=running,stdout,status call_management_command:reconcile_ncso_concession,production,{concession_id},{vmpp_id}",
                "report_stdout": True,
            },
            "ncso_send_alerts": {
                "run_args_template": "fab --hide=running,stdout,status call_management_command:send_ncso_concessions_alerts,production",
                "report_stdout": True,
            },
            "import_measure_definition": {
                "run_args_template": "fab --hide=running,stdout,status call_management_command:import_measures,--definition-only,{measure_id},production",
                "report_stdout": True,
            },
            "recalculate_measure": {
                "run_args_template": "fab --hide=running,stdout,status call_management_command:import_measures,{measure_id},production",
                "report_stdout": True,
            },
        },
        "slack": [{
            "command": "deploy",
            "help": "deploy to production after a 60s delay",
            "type": "schedule_job",
            "job_type": "deploy",
            "delay_seconds": 60,
        }, {
            "command": "deploy now",
            "help": "deploy to production immediately",
            "type": "schedule_job",
            "job_type": "deploy",
        }, {
            "command": "deploy cancel",
            "help": "cancel any pending production deploy",
            "type": "cancel_job",
            "job_type": "deploy",
        }, {
            "command": "deploy suppress from [start_at] to [end_at]",
            "help": "suppress production deploys between these times today (times in UTC)",
            "type": "schedule_suppression",
            "job_type": "deploy",
        }, {
            "command": "deploy suppress cancel",
            "help": "cancel suppression of production deploys",
            "type": "cancel_suppression",
            "job_type": "deploy",
        }, {
            "command": "deploy staging [branch_name]",
            "help": "deploy branch [branch_name] to staging immediately",
            "type": "schedule_job",
            "job_type": "deploy_staging",
        }, {
            "command": "cache clear",
            "help": "clear Cloudflare cache",
            "type": "schedule_job",
            "job_type": "cache_clear",
        }, {
            "command": "ncso import",
            "help": "import NCSO concessions",
            "type": "schedule_job",
            "job_type": "ncso_import",
        }, {
            "command": "ncso report",
            "help": "show NCSO concession summary",
            "type": "schedule_job",
            "job_type": "ncso_report",
        }, {
            "command": "ncso reconcile concession [concession_id] against vmpp [vmpp_id]",
            "help": "show NCSO concession summary",
            "type": "schedule_job",
            "job_type": "ncso_reconcile",
        }, {
            "command": "ncso send alerts",
            "help": "send alerts for NCSO concessions",
            "type": "schedule_job",
            "job_type": "ncso_send_alerts",
        }, {
            "command": "measures import [measure_id]",
            "help": "import measure definition",
            "type": "schedule_job",
            "job_type": "import_measure_definition",
        }, {
            "command": "measures recalculate [measure_id]",
            "help": "recalculate measure values",
            "type": "schedule_job",
            "job_type": "recalculate_measure",
        }],
    },
}
# fmt: on


def build_config(raw_config):
    """Convert raw_config into something that's easier to work with.

    See test_job_configs for an example.
    """

    config = {"jobs": {}, "slack": [], "help": {}, "fabfiles": {}}

    for namespace in raw_config:
        helps = []

        for job_type, job_config in raw_config[namespace]["jobs"].items():
            job_config["report_stdout"] = job_config.get("report_stdout", False)
            job_config["report_success"] = job_config.get("report_success", True)
            namespaced_job_type = f"{namespace}_{job_type}"
            validate_job_config(namespaced_job_type, job_config)
            config["jobs"][namespaced_job_type] = job_config

        for slack_config in raw_config[namespace]["slack"]:
            command = f"{namespace} {slack_config['command']}"
            slack_config["command"] = command
            slack_config["job_type"] = f"{namespace}_{slack_config['job_type']}"
            slack_config["regex"] = build_regex_from_command(command)
            slack_config["template_params"] = get_template_params(command)
            slack_config["delay_seconds"] = slack_config.get("delay_seconds", 0)

            validate_slack_config(slack_config)
            config["slack"].append(slack_config)

            helps.append([command, slack_config["help"]])

        config["help"][namespace] = sorted(helps)

        if "fabfile" in raw_config[namespace]:
            config["fabfiles"][namespace] = raw_config[namespace]["fabfile"]

    config["slack"] = sorted(config["slack"], key=itemgetter("command"))

    for slack_config in config["slack"]:
        if slack_config["job_type"] not in config["jobs"]:
            msg = f"Slack command {slack_config['command']} references unknown job type {slack_config['job_type']}"
            raise RuntimeError(msg)

    return config


def build_regex_from_command(command):
    """Convert Slack command into regex that matches command.

    >>> build_pattern_from_command("say [greeting] to [name]")
    re.compile("^say (.+?) to (.+?)$")
    """

    pattern = "^" + re.sub(r"\[\w+\]", r"(.+?)", command) + "$"
    return re.compile(pattern)


def get_template_params(command):
    """Extract parameters from Slack command.

    >>> get_template_params("say [greeting] to [name]")
    ["greeting", "name"]
    """

    return re.findall(r"\[(\w+)\]", command)


def validate_job_config(job_type, job_config):
    """Validate that job_config contains expected keys."""

    expected_keys = {"run_args_template", "report_stdout", "report_success"}

    if missing_keys := (expected_keys - job_config.keys()):
        msg = f"Job {job_type} is missing keys {missing_keys}"
        raise RuntimeError(msg)

    if extra_keys := (job_config.keys() - expected_keys):
        msg = f"Job {job_type} has extra keys {extra_keys}"
        raise RuntimeError(msg)


def validate_slack_config(slack_config):
    """Validate that slack_config contains expected keys."""

    expected_keys = {
        "command",
        "help",
        "type",
        "job_type",
        "regex",
        "template_params",
        "delay_seconds",
    }

    command = slack_config["command"]

    if missing_keys := (expected_keys - slack_config.keys()):
        msg = f"Slack command `{command}` is missing keys {missing_keys}"
        raise RuntimeError(msg)

    if extra_keys := (slack_config.keys() - expected_keys):
        msg = f"Slack command `{command}` has extra keys {extra_keys}"
        raise RuntimeError(msg)


config = build_config(raw_config)
