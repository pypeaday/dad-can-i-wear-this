build:
  docker context use default
  docker build -t registry.paynepride.com/dad-can-i-wear:latest .

push:
  docker context use default
  just build
  docker push registry.paynepride.com/dad-can-i-wear:latest

up:
  docker context use default
  docker compose up --build