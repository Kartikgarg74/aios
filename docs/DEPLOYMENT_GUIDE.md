# AIOS Deployment Guide

## Overview

This guide provides instructions for deploying the AIOS (AI Operating System) in various environments, from development to production. AIOS uses a microservices architecture with multiple MCP (Model Context Protocol) servers that need to be deployed and configured correctly.

## System Requirements

### Minimum Requirements

- **CPU**: 4 cores
- **RAM**: 2GB (minimum), 4GB (recommended)
- **Storage**: 10GB available space
- **Operating System**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- **Network**: Broadband internet connection

### Software Requirements

- Python 3.8 or higher
- Node.js 16+ and npm
- Docker (for containerized deployment)
- Kubernetes (for production deployment)

## Deployment Options

### 1. Local Development Deployment

For development and testing purposes:

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd aios_2gb
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the orchestrator service**
   ```bash
   uvicorn orchestrator_service:app --host 0.0.0.0 --port 9000
   ```

4. **Start individual MCP servers**
   ```bash
   uvicorn browser_server:app --host 0.0.0.0 --port 8001
   uvicorn system_operations_server:app --host 0.0.0.0 --port 8002
   # Start other servers as needed
   ```

### 2. Docker Deployment

For more isolated and reproducible deployments:

1. **Build Docker images**
   ```bash
   docker build -t aios/orchestrator -f Dockerfile.orchestrator .
   docker build -t aios/browser-server -f Dockerfile.browser .
   # Build other server images
   ```

2. **Run containers**
   ```bash
   docker run -d -p 9000:9000 --name orchestrator aios/orchestrator
   docker run -d -p 8001:8001 --name browser-server aios/browser-server
   # Run other server containers
   ```

3. **Using Docker Compose**
   ```bash
   docker-compose up -d
   ```

### 3. Kubernetes Deployment

For production environments with high availability and scalability:

1. **Apply Kubernetes manifests**
   ```bash
   kubectl apply -f kubernetes/namespace.yaml
   kubectl apply -f kubernetes/orchestrator.yaml
   kubectl apply -f kubernetes/browser-server.yaml
   # Apply other server manifests
   ```

2. **Verify deployment**
   ```bash
   kubectl get pods -n aios
   kubectl get services -n aios
   ```

## Configuration

### Environment Variables

Configure the following environment variables for each service:

- `AIOS_ENV`: Environment (development, staging, production)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `REDIS_URL`: URL for Redis connection
- `API_KEY`: API key for external services
- `JWT_SECRET`: Secret for JWT token generation

### Configuration Files

Main configuration files:

- `config/ai_os_config.py`: Core system configuration
- `config/logging_config.py`: Logging configuration
- `config/security_config.py`: Security settings

## Scaling Guidelines

### Horizontal Scaling

AIOS components can be horizontally scaled based on load:

1. **Orchestrator Service**: Deploy multiple instances behind a load balancer
2. **MCP Servers**: Scale individual servers based on specific workload patterns

### Resource Allocation

Recommended resource allocation per component:

| Component | CPU | Memory | Instances |
|-----------|-----|--------|----------|
| Orchestrator | 1 core | 500MB | 2-3 |
| Browser Server | 0.5 core | 300MB | 1-2 |
| System Ops Server | 0.5 core | 200MB | 1-2 |
| Python Server | 0.5 core | 300MB | 1-2 |
| Communication Server | 0.5 core | 200MB | 1 |
| IDE Server | 0.5 core | 200MB | 1 |
| Voice/UI Server | 0.5 core | 300MB | 1 |

### Load Balancing

Implement load balancing for high-traffic deployments:

- Use Nginx or HAProxy for HTTP load balancing
- Configure Kubernetes Ingress for cloud deployments
- Implement Redis for session management across instances

## Monitoring and Maintenance

### Health Monitoring

1. **Health Endpoints**: Each service exposes a `/health` endpoint
2. **Metrics Collection**: Use Prometheus for metrics collection
3. **Dashboards**: Set up Grafana dashboards for visualization

### Logging

1. **Centralized Logging**: Configure ELK stack or similar
2. **Log Rotation**: Implement log rotation to manage disk space
3. **Alert Configuration**: Set up alerts for critical errors

### Backup Procedures

1. **Database Backups**: Schedule regular Redis backups
2. **Configuration Backups**: Version control for configuration files
3. **Disaster Recovery**: Document recovery procedures

## Security Considerations

### Network Security

1. **Firewall Rules**: Restrict access to service ports
2. **TLS/SSL**: Configure HTTPS for all external endpoints
3. **Network Policies**: Implement Kubernetes network policies

### Authentication

1. **API Key Management**: Rotate API keys regularly
2. **JWT Configuration**: Set appropriate token expiration
3. **Rate Limiting**: Implement rate limiting for API endpoints

## Troubleshooting

### Common Issues

1. **Service Connection Failures**
   - Check network connectivity
   - Verify service is running
   - Check port configurations

2. **Performance Degradation**
   - Monitor resource usage
   - Check for memory leaks
   - Analyze logs for bottlenecks

3. **Authentication Errors**
   - Verify API keys are valid
   - Check JWT token expiration
   - Ensure proper permissions

## Upgrade Procedures

### Rolling Updates

1. **Backup current state**
2. **Update one service at a time**
3. **Verify health after each update**
4. **Roll back if issues are detected**

### Version Compatibility

Maintain compatibility between components:

- Orchestrator and MCP servers should use compatible versions
- Document API changes between versions
- Provide migration scripts for major updates

## Support Resources

- **Documentation**: Refer to the full documentation set
- **Issue Tracker**: Report issues on the project repository
- **Community Forum**: Discuss deployment challenges with the community