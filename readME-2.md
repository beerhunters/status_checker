# ✅ 1. Подготовка сервера
## Установить Docker:
```
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
```

## Добавляем GPG ключ
```
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

## Добавляем репозиторий
```
echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

## Установка docker
```
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io
```
### Установить Docker Compose:
```
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

# ✅ 2. Подготовка проекта на сервере
Клонировать из git-репозитория:
```
git clone https://github.com/your/project.git
```

# ✅ 3. Настроить .env файл
Создай .env в корне проекта (рядом с docker-compose.yml):
```
DB_USER=postgres
DB_PASSWORD=mysecretpassword
DB_NAME=monitoring_bot

LOG_LEVEL=INFO
```

Важно: если проект использует дополнительные переменные (например, токен бота, API ключи) — их также нужно внести в .env.
# 3.1. Login Docker
```docker login```

# ✅ 4. Запуск контейнеров
Из корня проекта:
```
docker-compose up -d --build
```
Флаги:

-d — запуск в фоне

--build — пересобирает образы