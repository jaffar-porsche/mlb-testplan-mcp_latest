# DATONA Confluence MCP Server
# Official Python runtime as base image
FROM python:3.11-alpine

# Metadata labels for better container management
LABEL name="mcporsche-confluence-mcp"

# Set working directory
WORKDIR /app

# Install system dependencies
# - curl: health checks
# - ca-certificates: HTTPS support
# - openssl: certificate extraction for .p12 auth (optional feature)
RUN apk add --no-cache curl ca-certificates openssl

# Copy requirements and install dependencies
COPY confluence-mcp/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python application files (modular structure)
COPY confluence-mcp/mcp_server.py ./
COPY confluence-mcp/config.py ./
COPY confluence-mcp/client.py ./
COPY confluence-mcp/cert_loader.py ./
COPY confluence-mcp/models.py ./
COPY confluence-mcp/html_utils.py ./
COPY confluence-mcp/routes/ ./routes/
COPY docker/start.sh ./

# Create directory for certificate mounts (optional)
RUN mkdir -p /app/certs

# Set permissions and create non-root user for security
RUN chmod +x start.sh && \
    addgroup -g 1001 -S mcpuser && \
    adduser -S mcpuser -u 1001 -G mcpuser && \
    chown -R mcpuser:mcpuser /app
USER mcpuser

# Environment variables will be passed from docker-compose
ENV PORT=8001

EXPOSE 8001

# Health check - using curl to check FastAPI health endpoint
# Note: Port will be set by environment variable at runtime
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:"$PORT"/docs || exit 1

# Start the MCP server using uvicorn
# Port will be read from PORT environment variable
CMD ["./start.sh"]
