# Nginx Troubleshooting Guide for Agentic Framework

This guide covers common nginx-related issues and their solutions for the Agentic Framework application.

## Quick Checklist

### Backend Configuration Changes
When making changes to the backend that affect main.py or routes:

1. **Configuration Import**: Use `from src.core.config import app_config` instead of `settings` to avoid naming conflicts
2. **Settings Router**: Import settings router as `from src.api.routers import settings as settings_router`
3. **Rebuild containers**: Always rebuild after significant changes: `docker-compose down && docker-compose up --build`
4. **Check logs**: Monitor backend logs: `docker logs agentic_backend -f`
5. **Remove default nginx config**: Ensure only custom config is used (handled automatically in docker-compose)

## Common Issues and Solutions

### 1. Python Import Naming Conflicts

**Issue**: `AttributeError: module 'src.api.routers.settings' has no attribute 'environment'`

**Cause**: Naming conflict between `src.api.routers.settings` module and `src.core.config.settings` object.

**Solution**: Use `app_config` instead of `settings` for configuration:
```python
# CORRECT
from src.core.config import app_config
from src.api.routers import settings as settings_router

if app_config.environment == 'development':
    # ...
```

**Files to update when this occurs:**
- `src/api/main.py`
- `src/core/config.py` 
- `src/database/connection.py`
- Any other files importing `settings` from `src.core.config`

### 2. Login/Authentication Issues

**Issue**: 404 errors on `/api/auth/login-json` or authentication endpoints

**Common Causes:**
- Nginx default config interfering with custom config
- Incorrect routing in nginx.conf
- Backend not starting due to import errors

**Solutions:**

a) Remove default nginx config (automatically handled):
```bash
docker exec agentic_nginx rm -f /etc/nginx/conf.d/default.conf
docker exec agentic_nginx nginx -s reload
```

b) Check nginx routing configuration in `nginx/nginx.conf`:
```nginx
location ~ ^/api/auth/ {
    # Correct regex pattern for auth routes
    proxy_pass http://backend;
    # ... other config
}
```

### 3. Adding New Backend Endpoints

When adding new endpoints to the backend:

1. **Add to nginx config** if the endpoint needs special handling
2. **Update CORS settings** if needed
3. **Test endpoint directly** first: `curl http://localhost:8000/api/your-endpoint`
4. **Test through nginx**: `curl http://localhost:8080/api/your-endpoint`

Example nginx location block for new endpoints:
```nginx
location /api/your-new-endpoint {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 4. CORS Issues

**Issue**: Cross-origin requests failing from frontend

**Solution**: Ensure CORS headers are properly configured in `nginx/nginx.conf`:

```nginx
# Add CORS headers for API requests
add_header Access-Control-Allow-Origin $http_origin always;
add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
add_header Access-Control-Allow-Headers "Accept, Accept-Language, Content-Language, Content-Type, Authorization" always;
add_header Access-Control-Allow-Credentials true always;
add_header Access-Control-Max-Age 3600 always;

# Handle preflight requests
if ($request_method = 'OPTIONS') {
    return 204;
}
```

### 5. Frontend Routing Issues

**Issue**: React routes returning 404 when accessed directly

**Solution**: Ensure `try_files` directive in frontend nginx config:
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### 6. Rate Limiting Issues

If you encounter 429 (Too Many Requests) errors, check the rate limiting configuration:

```nginx
# In nginx.conf
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;

location ~ ^/api/auth/(login|register) {
    limit_req zone=auth burst=10 nodelay;
    # ... rest of config
}
```

## Testing Commands

### Check if nginx is working:
```bash
curl -I http://localhost:8080
```

### Test backend directly (bypass nginx):
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/auth/login-json
```

### Test through nginx:
```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/auth/login-json
```

### Check nginx configuration:
```bash
docker exec agentic_nginx nginx -t
```

### View nginx logs:
```bash
docker logs agentic_nginx -f
```

### View backend logs:
```bash
docker logs agentic_backend -f
```

## Common HTTP Status Codes

- **404**: Route not found (check nginx location blocks)
- **502**: Backend unavailable (check if backend container is running)
- **503**: Service temporarily unavailable
- **429**: Too many requests (rate limiting)
- **500**: Internal server error (check backend logs)

## When to Rebuild Containers

Rebuild containers (`docker-compose down && docker-compose up --build`) when:

1. **Python code changes** that affect imports or application startup
2. **Requirements.txt changes** (new dependencies)
3. **Dockerfile changes**
4. **Nginx configuration changes** (nginx.conf)
5. **Environment variable changes** that affect application behavior

## Debugging Steps

1. **Check container status**: `docker-compose ps`
2. **View all logs**: `docker-compose logs`
3. **Test backend directly**: Bypass nginx to isolate issues
4. **Check nginx config**: `docker exec agentic_nginx nginx -t`
5. **Verify routes**: Check that nginx location blocks match your endpoints
6. **Monitor real-time logs**: Use `-f` flag to follow logs as requests come in 