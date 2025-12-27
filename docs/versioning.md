# Versioning
- Application API versioning is explained

# URL Versioning
- In this application we support URL versioning, where we support 3 types of url
1. Without prefix (Ex: `http(s)://<APP_HOST>/api/{endpoint}`)
2. With version prefix (Ex: `http(s)://<APP_HOST>/api/v1/{endpoint}`)
3. With latest prefix (Ex: `http(s)://<APP_HOST>/latest/api/{endpoint}`)

## Handle versioning
- **Router** assigned to:
    - `type 1`: is being used in existing applications
    - `type 3`: is lastest stable version deployed

# Links:
[Fastapi-versioning-ref](https://medium.com/arionkoder-engineering/fastapi-versioning-e9f86ace52ca)