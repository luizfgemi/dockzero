# Docker Dashboard

FastAPI application for inspecting local Docker containers, viewing simple metrics, and triggering start, stop, and restart actions from the browser.

[![Build and Publish](https://github.com/luizfgemi/dockzero/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/luizfgemi/dockzero/actions/workflows/docker-publish.yml)
[![Docker Image Version](https://img.shields.io/docker/v/luizfgemi/dockzero?sort=semver&logo=docker)](https://hub.docker.com/r/luizfgemi/dockzero)
[![Docker Image Size](https://img.shields.io/docker/image-size/luizfgemi/dockzero/latest?logo=docker)](https://hub.docker.com/r/luizfgemi/dockzero)
[![Docker Pulls](https://img.shields.io/docker/pulls/luizfgemi/dockzero?logo=docker)](https://hub.docker.com/r/luizfgemi/dockzero)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Run

```bash
docker-compose up
```

The interface will be available at `http://localhost:7070`. To run without Docker, install the dependencies from `app/requirements.txt` and start `uvicorn app.main:app --host 0.0.0.0 --port 7070` from the repository root.

## Environment variables

You can override the defaults below by exporting the variables before launching the service.

- `LINK_SCHEME` (default `http`): scheme used to build external links for mapped ports.
- `LINK_HOST` (default `localhost`): host used when building external links.
- `APP_TITLE` (default `Docker Dashboard`): title displayed on the web UI and HTML metadata.
- `AUTO_REFRESH_SECONDS` (default `10`): polling interval for the dashboard list.
- `LOG_REFRESH_SECONDS` (default `5`): polling interval for the logs page.
- `LOG_DEFAULT_TAIL` (default `200`): default number of log lines returned.
- `LOG_MAX_TAIL` (default `5000`): maximum number of log lines allowed per request.
- `WSL_DISTRO` (default `Ubuntu`): WSL distribution inserted in the helper exec command.
- `EXEC_SHELL` (default `bash`): shell used in the helper exec command.
- `ACTION_DELAY_SECONDS` (default `0.1`): delay after start/stop/restart to let state settle before refreshing.
