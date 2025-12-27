# Docker

This folder contains Docker-related scripts and configuration. 

## Local
Note: Make sure you have corrent env configurations

```
cd docker/deploy
docker compose --env-file ../../.env up --build
sudo docker compose --env-file ../../.env down
```