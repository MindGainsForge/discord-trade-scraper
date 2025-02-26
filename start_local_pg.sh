#!/bin/bash

docker run --rm --name postgres \
  -e POSTGRES_USER=mindgains \
  -e POSTGRES_PASSWORD=mindgains \
  -e POSTGRES_DB=mindgains \
  --tmpfs /var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:latest
