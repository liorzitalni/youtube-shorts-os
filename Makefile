# YouTube Shorts OS — Common Operations
# Usage: make <target>
# Requires: GNU Make + Python venv at .venv/

PYTHON = .venv/Scripts/python
PYTEST = .venv/Scripts/pytest

.PHONY: setup verify test demo dashboard produce upload analytics research scheduler

## First-time setup
setup:
	python -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) scripts/setup.py

## Check all API keys
verify:
	$(PYTHON) scripts/verify_apis.py

## Run test suite
test:
	$(PYTEST) tests/ -v

## Run full demo pipeline (idea -> video, no upload)
demo:
	$(PYTHON) scripts/demo_pipeline.py

## Start Streamlit dashboard
dashboard:
	.venv/Scripts/streamlit run modules/dashboard/app.py

## Run daily production (ideas -> scripts -> TTS -> render -> metadata)
produce:
	$(PYTHON) scripts/run_pipeline.py produce

## Upload approved videos to YouTube
upload:
	$(PYTHON) scripts/run_pipeline.py upload

## Ingest YouTube Analytics
analytics:
	$(PYTHON) scripts/run_pipeline.py analytics

## Scrape competitor channels
research:
	$(PYTHON) scripts/run_pipeline.py research

## Start the cron scheduler daemon
scheduler:
	$(PYTHON) scripts/run_pipeline.py scheduler

## Set up YouTube OAuth2 (one-time)
youtube-auth:
	$(PYTHON) scripts/setup_youtube_auth.py

## Generate new ideas only
ideas:
	$(PYTHON) scripts/run_pipeline.py generate-ideas
