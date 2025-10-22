# Docker Dashboard

FastAPI application for inspecting local Docker containers, viewing simple metrics, and triggering start, stop, and restart actions from the browser.

[![Build and Publish](https://github.com/luizfgemi/dockzero/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/luizfgemi/dockzero/actions/workflows/docker-publish.yml)
[![Docker Image Version](https://img.shields.io/docker/v/luizfgemi/dockzero?sort=semver&logo=docker)](https://hub.docker.com/r/luizfgemi/dockzero)
[![Docker Image Size](https://img.shields.io/docker/image-size/luizfgemi/dockzero/latest?logo=docker)](https://hub.docker.com/r/luizfgemi/dockzero)
[![Docker Pulls](https://img.shields.io/docker/pulls/luizfgemi/dockzero?logo=docker)](https://hub.docker.com/r/luizfgemi/dockzero)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Run

```bash
docker pull luizfgemi/dockzero:latest

docker run -d \
-p 7070:7070 \
-v /var/run/docker.sock:/var/run/docker.sock \
luizfgemi/dockzero:latest
```

## Docker Compose:
```yaml
services:
  dockzero:
    image: luizfgemi/dockzero:latest
    container_name: dockzero
    restart: unless-stopped
    ports:
      - "7070:7070"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      LINK_SCHEME: http
      LINK_HOST: localhost
      APP_TITLE: Docker Dashboard
      AUTO_REFRESH_SECONDS: 10
      LOG_REFRESH_SECONDS: 5
      LOG_DEFAULT_TAIL: 200
      LOG_MAX_TAIL: 5000
      WSL_DISTRO: Ubuntu
      EXEC_SHELL: bash
      ACTION_DELAY_SECONDS: 0.1
```

All variables can be omitted to use their default values.

---

## Environment variables

You can override the defaults below by exporting the variables before launching the service.

| Variable               | Default            | Description                                                           |
| ---------------------- | ------------------ | --------------------------------------------------------------------- |
| `LINK_SCHEME`          | `http`             | Scheme used to build external links for mapped ports.                 |
| `LINK_HOST`            | `localhost`        | Host used when building external links.                               |
| `APP_TITLE`            | `Docker Dashboard` | Title displayed on the web UI and HTML metadata.                      |
| `AUTO_REFRESH_SECONDS` | `10`               | Polling interval for the dashboard list.                              |
| `LOG_REFRESH_SECONDS`  | `5`                | Polling interval for the logs page.                                   |
| `LOG_DEFAULT_TAIL`     | `200`              | Default number of log lines returned.                                 |
| `LOG_MAX_TAIL`         | `5000`             | Maximum number of log lines allowed per request.                      |
| `WSL_DISTRO`           | `Ubuntu`           | WSL distribution inserted in the helper exec command.                 |
| `EXEC_SHELL`           | `bash`             | Shell used in the helper exec command.                                |
| `ACTION_DELAY_SECONDS` | `0.1`              | Delay after start/stop/restart to let state settle before refreshing. |

---

## Links

* **Docker Hub:** [hub.docker.com/r/luizfgemi/dockzero](https://hub.docker.com/r/luizfgemi/dockzero)
* **GitHub Repository:** [github.com/luizfgemi/docker-dashboard](https://github.com/luizfgemi/dockzero)

---

## License

MIT © 2025
