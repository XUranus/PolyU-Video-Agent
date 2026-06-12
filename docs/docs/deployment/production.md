---
id: production-checklist
title: 生产环境清单
sidebar_label: 生产清单
---

# 生产环境部署清单

在将 LectureMind 部署到生产环境之前，请逐项检查以下清单，确保系统安全、稳定、可维护。

## 部署前检查清单

### 安全配置

- [ ] **SECRET_KEY 已设置且唯一**

  默认的 `insecure dev key` 绝不能在生产环境使用。生成一个随机密钥：

  ```bash
  python -c "import secrets; print(secrets.token_hex(50))"
  ```

  将输出设置到 `.env` 中：

  ```bash
  SECRET_KEY=a1b2c3d4e5f6...（50 字节十六进制字符串）
  ```

- [ ] **DEBUG=False**

  调试模式会暴露详细的错误堆栈和内部路径，必须关闭：

  ```bash
  DEBUG=False
  ```

- [ ] **CORS 限制为你的域名**

  不要使用 `*` 作为 CORS 来源，只允许你的前端域名：

  ```bash
  CORS_ALLOWED_ORIGINS=https://your-domain.com
  ```

- [ ] **ALLOWED_HOSTS 限制为你的域名**

  ```bash
  ALLOWED_HOSTS=your-domain.com,www.your-domain.com
  ```

- [ ] **API 认证已启用**（规划中）

  当前版本的 API 端点不需要认证。如果面向公网部署，建议通过反向代理（nginx/Caddy）添加基础认证或 IP 白名单。

### 数据库

- [ ] **考虑使用 PostgreSQL 替代 SQLite**（推荐）

  SQLite 适合开发和小规模部署，但在并发写入场景下性能有限。对于生产环境，推荐迁移到 PostgreSQL：

  ```bash
  # 安装 PostgreSQL 适配器
  pip install psycopg2-binary

  # 在 .env 中配置数据库连接
  # 注意：需要修改 settings.py 支持 PostgreSQL
  DATABASE_URL=postgres://user:password@localhost:5432/lecturemind
  ```

  如果继续使用 SQLite，确保：
  - 数据库文件所在卷有足够空间
  - 定期备份 `db.sqlite3` 文件

### 网络和 HTTPS

- [ ] **通过反向代理配置 HTTPS**

  不要让 Django 直接暴露在公网上。使用 nginx 或 Caddy 作为反向代理：

  **nginx 配置示例**：

  ```nginx
  server {
      listen 80;
      server_name your-domain.com;
      return 301 https://$host$request_uri;
  }

  server {
      listen 443 ssl http2;
      server_name your-domain.com;

      ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

      # 前端
      location / {
          proxy_pass http://localhost:3000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
      }

      # 后端 API
      location /api/ {
          proxy_pass http://localhost:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-Proto $scheme;
      }

      # 媒体文件
      location /media/ {
          alias /data/media/;
          expires 30d;
          add_header Cache-Control "public, immutable";
      }

      # 文件上传大小限制
      client_max_body_size 2G;
  }
  ```

  **Caddy 配置示例**（自动 HTTPS）：

  ```
  your-domain.com {
      reverse_proxy /api/* localhost:8000
      reverse_proxy /* localhost:3000

      header {
          Strict-Transport-Security "max-age=31536000"
      }
  }
  ```

### 文件和存储

- [ ] **文件上传大小限制已配置**

  视频文件通常较大，需要在反向代理中配置上传限制：

  ```nginx
  # nginx
  client_max_body_size 2G;
  ```

  Django 默认不限制上传大小，但建议在应用层设置：

  ```python
  # settings.py
  DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
  FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
  ```

- [ ] **存储空间规划**

  每个视频处理后大约需要以下存储空间：

  | 内容 | 大小估算 |
  |---|---|
  | 原始视频 | 取决于上传文件 |
  | HLS 切片 | 约为原始视频的 1.5-2 倍 |
  | WAV 音频 | 约为视频时长 × 160KB/秒 |
  | 缩略图 | 每张约 20-50KB（200px）+ 200-500KB（1920px） |
  | ChromaDB 向量 | 每个知识条约 1-2KB |

  **建议**：为每个视频预留 3-5 倍原始文件大小的存储空间。

### 日志和监控

- [ ] **日志轮转已配置**

  长期运行会产生大量日志。配置日志轮转避免磁盘占满：

  ```bash
  # 在 .env 中设置日志目录
  LOG_DIR=/var/log/lecturemind
  ```

  使用 logrotate（如果日志在宿主机上）：

  ```
  /var/log/lecturemind/*.log {
      daily
      rotate 14
      compress
      delaycompress
      missingok
      notifempty
      create 640 appuser appuser
  }
  ```

- [ ] **监控服务状态**

  使用 Docker 健康检查监控服务状态：

  ```bash
  # 检查容器健康状态
  docker compose ps

  # 检查后端 API 健康
  curl -f http://localhost:8000/api/health/ || echo "Backend unhealthy!"
  ```

### 备份策略

- [ ] **数据库备份**

  ```bash
  # SQLite 备份（Docker 环境）
  docker compose exec web cp /data/db.sqlite3 /data/db.sqlite3.bak
  docker cp lecturemind-web-1:/data/db.sqlite3.bak ./backups/db-$(date +%Y%m%d).sqlite3

  # PostgreSQL 备份
  pg_dump -U postgres lecturemind > ./backups/db-$(date +%Y%m%d).sql
  ```

- [ ] **媒体文件备份**

  ```bash
  # 备份媒体目录
  docker cp lecturemind-web-1:/data/media ./backups/media-$(date +%Y%m%d)

  # 或者使用 rsync 同步到远程存储
  rsync -avz /data/media/ backup-server:/backups/lecturemind/media/
  ```

- [ ] **自动化备份脚本**

  ```bash
  #!/bin/bash
  # backup.sh — 每日备份脚本
  BACKUP_DIR="/backups/lecturemind/$(date +%Y%m%d)"
  mkdir -p "$BACKUP_DIR"

  # 备份数据库
  docker cp lecturemind-web-1:/data/db.sqlite3 "$BACKUP_DIR/db.sqlite3"

  # 备份媒体（可选，如果空间有限可以只备份数据库）
  # docker cp lecturemind-web-1:/data/media "$BACKUP_DIR/media"

  # 清理 30 天前的备份
  find /backups/lecturemind/ -maxdepth 1 -mtime +30 -exec rm -rf {} \;

  echo "Backup completed: $BACKUP_DIR"
  ```

  添加到 crontab：

  ```bash
  # 每天凌晨 3 点执行备份
  0 3 * * * /path/to/backup.sh >> /var/log/lecturemind-backup.log 2>&1
  ```

### Docker 资源限制

- [ ] **配置容器资源限制**

  在 `docker-compose.yml` 中为每个服务设置资源限制，防止单个服务耗尽系统资源：

  ```yaml
  deploy:
    resources:
      limits:
        memory: 4G    # 根据实际负载调整
        cpus: '2.0'   # 根据 CPU 核数调整
      reservations:
        memory: 512M
  ```

  **资源建议**：

  | 服务 | 最小内存 | 推荐内存 | CPU |
  |---|---|---|---|
  | web | 1GB | 4GB | 1-2 核 |
  | worker | 2GB | 4GB | 1-2 核 |
  | frontend | 256MB | 512MB | 0.5 核 |

## 性能优化

### 后端优化

1. **Gunicorn Worker 数量**

   默认使用 2 个 worker。根据 CPU 核数调整：

   ```bash
   # 在 docker-entrypoint.sh 中调整
   gunicorn videoapp.wsgi:application \
     --workers $(( $(nproc) * 2 + 1 )) \
     --bind 0.0.0.0:8000 \
     --timeout 300
   ```

2. **数据库连接池**

   对于 PostgreSQL，使用连接池减少连接开销：

   ```python
   # settings.py
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'CONN_MAX_AGE': 600,  # 持久连接
       }
   }
   ```

3. **缓存配置**

   使用 Redis 缓存频繁访问的数据：

   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django_redis.cache.RedisCache',
           'LOCATION': 'redis://redis:6379/1',
       }
   }
   ```

### 前端优化

1. **nginx 缓存头**

   静态资源设置长期缓存：

   ```nginx
   location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2)$ {
       expires 1y;
       add_header Cache-Control "public, immutable";
   }
   ```

2. **gzip 压缩**

   确保 nginx 启用了 gzip：

   ```nginx
   gzip on;
   gzip_types text/plain text/css application/json application/javascript text/xml;
   gzip_min_length 1024;
   ```

## 日志管理

### 日志级别配置

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'lecturemind.log'),
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'LectureMind': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 关键日志监控

关注以下日志模式：

```bash
# 错误日志
docker compose logs web 2>&1 | grep -i "error\|exception\|traceback"

# 任务失败
docker compose logs worker 2>&1 | grep -i "failed\|error"

# 健康检查失败
docker compose logs web 2>&1 | grep -i "health"
```

## 安全加固

### 容器安全

1. **使用非 root 用户运行**

   Dockerfile 已配置 `appuser`（UID 1001）运行应用，无需额外操作。

2. **只读文件系统**（高级）

   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G
   # 只读根文件系统（需要 tmpfs 挂载临时目录）
   read_only: true
   tmpfs:
     - /tmp
   ```

3. **限制容器能力**

   ```yaml
   cap_drop:
     - ALL
   cap_add:
     - NET_BIND_SERVICE  # 仅在需要绑定低端口时添加
   ```

### 网络安全

1. **防火墙规则**

   只暴露必要端口：

   ```bash
   # 只允许 80（HTTP）和 443（HTTPS）
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw deny 8000/tcp   # 不直接暴露后端
   ufw deny 3000/tcp   # 不直接暴露前端
   ```

2. **Docker 网络隔离**

   默认的 Docker Compose 网络已经提供了服务间隔离。外部只能通过映射端口访问 `web` 和 `frontend`。

### 数据安全

1. **文件权限**

   ```bash
   # .env 文件只允许 owner 读写
   chmod 600 .env
   ```

2. **敏感数据加密**

   在 Docker 中，密钥通过 `env_file` 注入，不会烘焙到镜像中。

## 扩展考虑

### 水平扩展

当前架构中，`web` 和 `worker` 共享同一个 SQLite 数据库和文件系统卷，这限制了水平扩展能力。如果需要扩展：

1. **迁移到 PostgreSQL**：支持多实例并发访问
2. **使用对象存储**：将媒体文件存储到 COS/S3/OSS，而非本地卷
3. **分离 Worker**：可以运行多个 worker 实例处理任务队列

### 垂直扩展

最简单的扩展方式是增加单机资源：

```yaml
# 增加 worker 的资源限制
worker:
  deploy:
    resources:
      limits:
        memory: 8G    # 增加内存
        cpus: '4.0'   # 增加 CPU
```

### 使用外部服务

| 组件 | 当前方案 | 扩展方案 |
|---|---|---|
| 数据库 | SQLite | PostgreSQL |
| 向量数据库 | ChromaDB（本地） | ChromaDB Server / Qdrant / Milvus |
| 对象存储 | 腾讯云 COS | 已使用外部服务 |
| 缓存 | 无 | Redis |
| 消息队列 | SQLite 轮询 | Celery + Redis/RabbitMQ |
