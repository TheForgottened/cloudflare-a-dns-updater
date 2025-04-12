# Cloudflare A DNS Updater

Automatically updates DNS records of type A in Cloudflare.

## Running locally

Check `.env.example` to see which environment variables are needed.

```shell
uv run main.py
```

Or, if you want to use Docker:

```shell
docker compose up --build --force-recreate
```

## Prepare dev environment

With the power of UV, setting up the dev environment is a piece of cake!

```shell
uv sync --all-groups
uv run pre-commit install
```
