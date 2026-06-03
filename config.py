import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB
MONGO_URI  = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB   = os.getenv("MONGO_DB",  "pulseops")

# LLM
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT")
LLM_API_KEY  = os.getenv("LLM_API_KEY")
LLM_MODEL    = os.getenv("LLM_MODEL")

# Jenkins
JENKINS_URL   = os.getenv("JENKINS_URL")
JENKINS_USER  = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")

# Confluence
CONFLUENCE_URL   = os.getenv("CONFLUENCE_URL")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN")

# ServiceNow
SNOW_URL              = os.getenv("SNOW_URL")
SNOW_USER             = os.getenv("SNOW_USER")
SNOW_PASSWORD         = os.getenv("SNOW_PASSWORD")
SNOW_ASSIGNMENT_GROUP = os.getenv("SNOW_ASSIGNMENT_GROUP")

# Teams
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

# Git
GIT_TOKEN    = os.getenv("GIT_TOKEN")
GIT_BASE_URL = os.getenv("GIT_BASE_URL")
