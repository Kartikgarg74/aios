# AIOS Quick Reference Guide

## System Overview

AIOS (AI Operating System) is a modular AI-powered environment with multiple MCP (Model Context Protocol) servers working together to provide various capabilities.

## Key Components

| Component | Port | Description |
|-----------|------|-------------|
| Orchestrator | 9000 | Central API gateway and load balancer |
| Browser Server | 8001 | Web automation and browser control |
| Python Server | 8000 | Python code execution and analysis |
| System Ops Server | 8002 | File system and process management |
| Communication Server | 8003 | WhatsApp, email, and phone integration |
| IDE Server | 8004 | VS Code and development tools |
| GitHub Actions Server | 8005 | Repository management and CI/CD |
| Voice/UI Server | 8006 | Speech recognition and GUI automation |

## Common Commands

### Starting Services

```bash
# Start orchestrator
uvicorn orchestrator_service:app --host 0.0.0.0 --port 9000

# Start MCP server
uvicorn browser_server:app --host 0.0.0.0 --port 8001
```

### Docker Commands

```bash
# Start all services
docker-compose up -d

# Check service logs
docker logs orchestrator

# Stop all services
docker-compose down
```

### Kubernetes Commands

```bash
# Deploy services
kubectl apply -f kubernetes/

# Check pod status
kubectl get pods -n aios

# View service logs
kubectl logs -n aios deployment/orchestrator
```

## API Endpoints

### Orchestrator Service (Port 9000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| /token | POST | Generate JWT token |
| /register_server | POST | Register MCP server |
| /command | POST | Execute command |
| /system/status | GET | Get system status |

### Example API Requests

#### Authentication

```bash
curl -X POST http://localhost:9000/token \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'
```

#### Execute Command

```bash
curl -X POST http://localhost:9000/command \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{"server": "browser", "command": "search", "params": {"query": "AIOS documentation"}}'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|--------|
| AIOS_ENV | Environment (development, staging, production) | development |
| LOG_LEVEL | Logging level | INFO |
| REDIS_URL | Redis connection URL | redis://localhost:6379 |
| API_KEY | External API key | - |
| JWT_SECRET | JWT token secret | - |

### Configuration Files

| File | Description |
|------|-------------|
| config/ai_os_config.py | Core system configuration |
| config/logging_config.py | Logging configuration |
| config/security_config.py | Security settings |

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Service connection failure | Check if service is running and port is accessible |
| Authentication error | Verify API key or JWT token is valid |
| High memory usage | Check for memory leaks or increase resource limits |
| Slow response time | Monitor CPU usage and optimize resource-intensive operations |

### Diagnostic Commands

```bash
# Check service health
curl http://localhost:9000/health

# View system resources
curl http://localhost:9000/system/status

# Check logs
tail -f logs/orchestrator.log
```

## Resource Optimization

### Memory Optimization

- Use memory pooling for frequently allocated objects
- Implement lazy loading for resource-intensive components
- Set appropriate cache sizes and TTLs

### CPU Optimization

- Use worker pools for parallel processing
- Implement priority task queues
- Apply CPU throttling for background tasks

## Security Best Practices

- Rotate API keys regularly
- Use HTTPS for all external endpoints
- Implement rate limiting for API endpoints
- Configure appropriate JWT token expiration
- Restrict access to service ports with firewall rules

## Support Resources

- **User Guide**: Complete user documentation
- **Developer Guide**: API and architecture documentation
- **Deployment Guide**: Deployment and scaling instructions
- **Architecture Diagrams**: Visual system representation