import os

structure = [
    "api-service/app/",
    "api-service/tests/",
    "api-service/requirements.txt",
    "api-service/Dockerfile",
    "api-service/README.md",

    "rag-service/app/",
    "rag-service/tests/",
    "rag-service/requirements.txt",
    "rag-service/Dockerfile",
    "rag-service/README.md",

    "ocr-service/app/",
    "ocr-service/tests/",
    "ocr-service/requirements.txt",
    "ocr-service/Dockerfile",
    "ocr-service/README.md",

    "llm-service/app/",
    "llm-service/tests/",
    "llm-service/requirements.txt",
    "llm-service/Dockerfile",
    "llm-service/README.md",

    "db-service/app/",
    "db-service/tests/",
    "db-service/requirements.txt",
    "db-service/Dockerfile",
    "db-service/README.md",

    "frontend/public/",
    "frontend/src/",
    "frontend/tests/",
    "frontend/package.json",
    "frontend/vite.config.js",
    "frontend/Dockerfile",
    "frontend/README.md",

    "k8s/api-service.yaml",
    "k8s/rag-service.yaml",
    "k8s/ocr-service.yaml",
    "k8s/llm-service.yaml",
    "k8s/db-service.yaml",
    "k8s/frontend.yaml",
    "k8s/ingress.yaml",
    "k8s/configmap.yaml",

    ".github/workflows/ci-cd.yml",

    "docker-compose.yml",
    "README.md",
    "scripts/deploy.sh"
]

for path in structure:
    if path.endswith('/'):
        os.makedirs(path, exist_ok=True)
    else:
        dir_name = os.path.dirname(path)
        if dir_name != '':
            os.makedirs(dir_name, exist_ok=True)
        with open(path, 'w') as f:
            pass

print("Project structure created in current directory successfully.")
