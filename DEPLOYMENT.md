# Deployment Guide

## Overview

This guide covers deployment options for the Australian Postcodes MCP Server, with FastMCP Cloud as the recommended production deployment method.

## Prerequisites

- Python 3.9 or higher
- Git
- GitHub account (for FastMCP Cloud)
- FastMCP CLI installed (`pip install fastmcp`)

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/australian-postcodes-mcp.git
cd australian-postcodes-mcp
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
# Download and import postcode data
python src/utils/data_loader.py

# Verify database creation
ls -la data/postcodes.db
```

### 5. Test Locally

```bash
# Run development server
fastmcp dev src/server.py

# Or run directly
python src/server.py
```

### 6. Test with Claude Desktop

Add to Claude Desktop configuration (`~/.config/claude/config.json`):

```json
{
  "mcpServers": {
    "australian-postcodes": {
      "command": "python",
      "args": ["/absolute/path/to/src/server.py"]
    }
  }
}
```

## FastMCP Cloud Deployment (Recommended)

### 1. Prepare Repository

Ensure your GitHub repository has:

```
australian-postcodes-mcp/
├── src/
│   └── server.py          # Main server file
├── data/
│   └── postcodes.db       # Pre-populated database
├── requirements.txt       # Python dependencies
├── README.md
└── .env.example          # Environment variables template
```

### 2. Create FastMCP Cloud Account

1. Visit [fastmcp.cloud](https://fastmcp.cloud)
2. Sign in with GitHub
3. Authorize FastMCP Cloud

### 3. Connect Repository

1. Click "New Server"
2. Select your repository: `australian-postcodes-mcp`
3. Configure deployment settings:
   - **Entry Point**: `src/server.py`
   - **Python Version**: `3.11`
   - **Server Name**: `australian-postcodes`

### 4. Configure Environment Variables

In FastMCP Cloud dashboard:

```env
SERVER_NAME=australian-postcodes
SERVER_VERSION=1.0.0
LOG_LEVEL=INFO
DATA_UPDATE_URL=https://raw.githubusercontent.com/matthewproctor/australianpostcodes/refs/heads/master/australian_postcodes.csv
FUZZY_THRESHOLD=0.8
MAX_SUGGESTIONS=5
```

### 5. Deploy

1. Click "Deploy"
2. Wait for build to complete (~2-3 minutes)
3. Copy the server URL provided

### 6. Test Deployment

```bash
# Test with curl
curl -X POST https://your-server.fastmcp.cloud/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### 7. Add to Claude Desktop

Update Claude Desktop configuration:

```json
{
  "mcpServers": {
    "australian-postcodes": {
      "command": "npx",
      "args": ["@fastmcp/client", "https://your-server.fastmcp.cloud"]
    }
  }
}
```

## Docker Deployment (Alternative)

### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY data/ ./data/

# Initialize database if needed
RUN python src/utils/data_loader.py || true

# Expose MCP port
EXPOSE 8080

# Run server
CMD ["python", "src/server.py"]
```

### 2. Build and Run

```bash
# Build image
docker build -t australian-postcodes-mcp .

# Run container
docker run -d \
  --name postcodes-mcp \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  australian-postcodes-mcp
```

### 3. Docker Compose (with database persistence)

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
    environment:
      - SERVER_NAME=australian-postcodes
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

## Manual VPS Deployment

### 1. Server Requirements

- Ubuntu 22.04 or similar
- 1GB RAM minimum
- 1GB disk space
- Python 3.9+

### 2. Setup Script

```bash
#!/bin/bash

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip git sqlite3

# Clone repository
git clone https://github.com/yourusername/australian-postcodes-mcp.git
cd australian-postcodes-mcp

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Initialize database
python src/utils/data_loader.py

# Create systemd service
sudo tee /etc/systemd/system/postcodes-mcp.service > /dev/null <<EOF
[Unit]
Description=Australian Postcodes MCP Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/australian-postcodes-mcp
Environment="PATH=/home/ubuntu/australian-postcodes-mcp/venv/bin"
ExecStart=/home/ubuntu/australian-postcodes-mcp/venv/bin/python src/server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl enable postcodes-mcp
sudo systemctl start postcodes-mcp
```

### 3. Nginx Reverse Proxy (Optional)

```nginx
server {
    listen 80;
    server_name mcp.yourdomain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # SSE support
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

## Database Management

### Initial Data Import

```bash
# Run the data loader
python src/utils/data_loader.py

# This will:
# 1. Download CSV from GitHub
# 2. Parse ~17,000 records
# 3. Create SQLite database
# 4. Build indexes
# 5. Generate phonetic codes
```

### Data Updates

#### Manual Update

```bash
# Download latest data
curl -o data/postcodes_new.csv https://raw.githubusercontent.com/matthewproctor/australianpostcodes/refs/heads/master/australian_postcodes.csv

# Backup existing database
cp data/postcodes.db data/postcodes_backup.db

# Re-import data
python src/utils/data_loader.py --update
```

#### Automated Updates (Cron)

```bash
# Add to crontab (weekly update)
0 2 * * 1 cd /path/to/app && /path/to/venv/bin/python src/utils/data_loader.py --update >> logs/update.log 2>&1
```

## Monitoring and Maintenance

### Health Check Endpoint

The server provides a health check tool:

```python
# Check server health
result = await health_check()
# Returns: {"status": "healthy", "database": "connected", "records": 17289}
```

### Logging Configuration

Configure logging via environment variables:

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=/var/log/postcodes-mcp.log
LOG_FORMAT=json  # json or text
```

### Monitoring with Systemd

```bash
# View logs
sudo journalctl -u postcodes-mcp -f

# Check status
sudo systemctl status postcodes-mcp

# Restart service
sudo systemctl restart postcodes-mcp
```

### Performance Monitoring

Monitor these metrics:
- Response time (target: <100ms)
- Memory usage (typical: 50-100MB)
- Database size (typical: 10-15MB)
- Query patterns

## Troubleshooting

### Common Issues

#### 1. Database Not Found
```bash
# Error: sqlite3.OperationalError: unable to open database file

# Solution: Initialize database
python src/utils/data_loader.py
```

#### 2. Port Already in Use
```bash
# Error: Address already in use

# Solution: Change port or stop existing process
lsof -i :8080
kill <PID>
```

#### 3. Import Errors
```bash
# Error: ModuleNotFoundError

# Solution: Install dependencies
pip install -r requirements.txt
```

#### 4. FastMCP Cloud Build Fails
```
# Check requirements.txt for:
- No git+ URLs (use PyPI packages only)
- No local file references
- Compatible version specifications
```

### Debug Mode

Enable debug logging:

```bash
# Environment variable
export LOG_LEVEL=DEBUG

# Or in code
python src/server.py --debug
```

## Security Considerations

### Environment Variables

Never commit sensitive data. Use environment variables:

```env
# .env file (local only, not committed)
API_KEY=your_secret_key
DATABASE_URL=postgresql://user:pass@host/db
```

### Database Security

```bash
# Set appropriate permissions
chmod 600 data/postcodes.db

# Backup regularly
cp data/postcodes.db backups/postcodes_$(date +%Y%m%d).db
```

### Network Security

For production:
- Use HTTPS/TLS
- Implement rate limiting
- Validate origins for CORS
- Use firewall rules

```bash
# UFW example
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Scaling Considerations

### Current Limits
- SQLite: Good for <100 concurrent connections
- Memory: ~100MB for full dataset
- Response time: <100ms for most queries

### Scaling Options

#### 1. Horizontal Scaling
- Deploy multiple instances
- Use load balancer
- Share database via network

#### 2. Database Migration
```python
# Migrate to PostgreSQL for better concurrency
DATABASE_URL=postgresql://user:pass@host/postcodes
```

#### 3. Caching Layer
```python
# Add Redis for frequent queries
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600
```

## Backup and Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/postcodes"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Database backup
sqlite3 data/postcodes.db ".backup ${BACKUP_DIR}/postcodes_${TIMESTAMP}.db"

# Application backup
tar -czf ${BACKUP_DIR}/app_${TIMESTAMP}.tar.gz src/ data/ requirements.txt

# Keep last 30 days
find ${BACKUP_DIR} -name "*.db" -mtime +30 -delete
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +30 -delete
```

### Recovery Process

```bash
# Restore database
cp /backups/postcodes/postcodes_20250827.db data/postcodes.db

# Restore application
tar -xzf /backups/postcodes/app_20250827.tar.gz

# Restart service
sudo systemctl restart postcodes-mcp
```

## Support and Resources

- **Documentation**: See README.md and ARCHITECTURE.md
- **Issues**: GitHub Issues
- **FastMCP Cloud Support**: support@fastmcp.cloud
- **Community**: MCP Discord Server

## Checklist for Production

- [ ] Database initialized with full dataset
- [ ] Environment variables configured
- [ ] Logging configured
- [ ] Health checks passing
- [ ] Backup strategy implemented
- [ ] Monitoring setup
- [ ] Security review completed
- [ ] Performance tested
- [ ] Documentation updated
- [ ] GitHub repository public (for FastMCP Cloud)