from pathlib import Path

from environs import Env


env = Env()
env.read_env()

APPLICATION_ROOT = Path(__file__).resolve().parent.parent

# A directory that jobs can write to; in production, this is a volume
# that is mounted into the dokku app and is owned by the non-root docker user
WRITEABLE_DIR = env.path("WRITEABLE_DIR", default=APPLICATION_ROOT)

DB_PATH = env.path("DB_PATH", default=WRITEABLE_DIR / "ebmbot.db")

# location of job workspaces that live in this repo
WORKSPACE_DIR = env.path("WORKSPACE_DIR", default=APPLICATION_ROOT / "workspace")

# location of a writeable workspace directory for jobs that need to  create their
# namespace folder. This applies to fabric jobs (which fetch a fabfile from GitHub)
# and to jobs that don't depend on any existing files.
# In production, we want this to be a location in a
# mounted volume in the dokku app, which the docker user has write access
# to, and not a location that only exists in the container
WRITEABLE_WORKSPACE_DIR = env.path(
    "WRITEABLE_WORKSPACE_DIR", default=WRITEABLE_DIR / "workspace"
)

LOGS_DIR = env.path("LOGS_DIR")
# An alias for logs dir; this is just used for reporting the host location of logs
# in slack, where the log dir is a mounted volume
HOST_LOGS_DIR = env.path("HOST_LOGS_DIR", LOGS_DIR)
SLACK_LOGS_CHANNEL = env.str("SLACK_LOGS_CHANNEL")
SLACK_BENNETT_ADMINS_CHANNEL = env.str("SLACK_BENNETT_ADMINS_CHANNEL")
SLACK_TECH_SUPPORT_CHANNEL = env.str("SLACK_TECH_SUPPORT_CHANNEL")
SLACK_BOT_TOKEN = env.str("SLACK_BOT_TOKEN")
SLACK_BOT_USER_TOKEN = env.str("SLACK_USER_TOKEN")
SLACK_APP_TOKEN = env.str("SLACK_APP_TOKEN")
SLACK_SIGNING_SECRET = env.str("SLACK_SIGNING_SECRET")
SLACK_APP_USERNAME = env.str("SLACK_APP_USERNAME")

# Path to file created when the bot starts up. In production, this should be
# a path to a file in the mounted volume
BOT_CHECK_FILE = env.path(
    "BOT_CHECK_FILE", default=APPLICATION_ROOT / ".bot_startup_check"
)

# Should match "Payload URL" from
# https://github.com/ebmdatalab/openprescribing/settings/hooks/85994427
WEBHOOK_ORIGIN = env.str("WEBHOOK_ORIGIN")

# "Secret" from https://github.com/ebmdatalab/openprescribing/settings/hooks/85994427
GITHUB_WEBHOOK_SECRET = env.str("GITHUB_WEBHOOK_SECRET").encode("ascii")

# Path to credentials of gdrive@ebmdatalab.iam.gserviceaccount.com GCP service account
GCP_CREDENTIALS_PATH = env.path("GCP_CREDENTIALS_PATH")

# A secret that we generate ourselves
EBMBOT_WEBHOOK_SECRET = env.str("EBMBOT_WEBHOOK_SECRET").encode("ascii")

# TTL in seconds for webhook token
EBMBOT_WEBHOOK_TOKEN_TTL = 60 * 60
