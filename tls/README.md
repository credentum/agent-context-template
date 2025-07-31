# TLS/SSL Configuration for Production

This directory contains TLS certificates for production deployments. For security reasons, certificates are not included in the repository and must be generated separately.

## Directory Structure

```
tls/
├── README.md (this file)
├── ca.crt (Certificate Authority - shared)
├── qdrant/
│   ├── qdrant.crt
│   └── qdrant.key
├── neo4j/
│   ├── bolt/
│   │   ├── public.crt
│   │   └── private.key
│   └── https/
│       ├── public.crt
│       └── private.key
└── redis/
    ├── redis.crt
    ├── redis.key
    └── ca.crt (copy of root CA)
```

## Generating Certificates

### Option 1: Self-Signed Certificates (Development/Testing)

```bash
# Create directories
mkdir -p tls/{qdrant,neo4j/{bolt,https},redis}

# Generate CA key and certificate
openssl genrsa -out tls/ca.key 4096
openssl req -new -x509 -days 3650 -key tls/ca.key -out tls/ca.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=AgentContext-CA"

# Generate Qdrant certificates
openssl genrsa -out tls/qdrant/qdrant.key 2048
openssl req -new -key tls/qdrant/qdrant.key -out tls/qdrant/qdrant.csr \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=qdrant"
openssl x509 -req -in tls/qdrant/qdrant.csr -CA tls/ca.crt -CAkey tls/ca.key \
  -CAcreateserial -out tls/qdrant/qdrant.crt -days 365

# Generate Neo4j certificates (bolt)
openssl genrsa -out tls/neo4j/bolt/private.key 2048
openssl req -new -key tls/neo4j/bolt/private.key -out tls/neo4j/bolt/cert.csr \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=neo4j-bolt"
openssl x509 -req -in tls/neo4j/bolt/cert.csr -CA tls/ca.crt -CAkey tls/ca.key \
  -CAcreateserial -out tls/neo4j/bolt/public.crt -days 365

# Generate Neo4j certificates (https)
openssl genrsa -out tls/neo4j/https/private.key 2048
openssl req -new -key tls/neo4j/https/private.key -out tls/neo4j/https/cert.csr \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=neo4j-https"
openssl x509 -req -in tls/neo4j/https/cert.csr -CA tls/ca.crt -CAkey tls/ca.key \
  -CAcreateserial -out tls/neo4j/https/public.crt -days 365

# Generate Redis certificates
openssl genrsa -out tls/redis/redis.key 2048
openssl req -new -key tls/redis/redis.key -out tls/redis/redis.csr \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=redis"
openssl x509 -req -in tls/redis/redis.csr -CA tls/ca.crt -CAkey tls/ca.key \
  -CAcreateserial -out tls/redis/redis.crt -days 365

# Copy CA cert to Redis directory
cp tls/ca.crt tls/redis/ca.crt

# Clean up CSR files
rm tls/{qdrant/qdrant.csr,neo4j/bolt/cert.csr,neo4j/https/cert.csr,redis/redis.csr}

# Set proper permissions
chmod 600 tls/**/*.key
chmod 644 tls/**/*.crt
```

### Option 2: Let's Encrypt (Production)

For production deployments with public domains, use Let's Encrypt certificates:

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificates for your domains
certbot certonly --standalone -d your-qdrant-domain.com
certbot certonly --standalone -d your-neo4j-domain.com
certbot certonly --standalone -d your-redis-domain.com

# Copy certificates to appropriate directories
# (adjust paths based on your Let's Encrypt output)
```

### Option 3: Corporate CA

If you have a corporate Certificate Authority, request certificates following your organization's procedures.

## Environment Variables

Set these in your `.env` file for production:

```bash
# API Keys and Passwords
QDRANT_API_KEY=your_secure_api_key_here
NEO4J_AUTH=neo4j/your_secure_password_here
REDIS_PASSWORD=your_secure_redis_password_here

# TLS Settings (optional overrides)
QDRANT_TLS_ENABLED=true
NEO4J_TLS_LEVEL=REQUIRED
REDIS_TLS_ENABLED=true
```

## Client Configuration

### Python Clients

```python
# Qdrant with TLS
from qdrant_client import QdrantClient
client = QdrantClient(
    host="localhost",
    port=6333,
    https=True,
    api_key="your_api_key",
    verify=True  # Set to path of ca.crt for self-signed
)

# Neo4j with TLS
from neo4j import GraphDatabase
driver = GraphDatabase.driver(
    "bolt+s://localhost:7687",  # Note the +s for SSL
    auth=("neo4j", "your_password"),
    encrypted=True,
    trust="TRUST_ALL_CERTIFICATES"  # For self-signed
)

# Redis with TLS
import redis
r = redis.Redis(
    host="localhost",
    port=6379,
    password="your_password",
    ssl=True,
    ssl_certfile="tls/redis/redis.crt",
    ssl_keyfile="tls/redis/redis.key",
    ssl_ca_certs="tls/ca.crt"
)
```

## Security Best Practices

1. **Never commit certificates to Git** - Add `tls/` to `.gitignore`
2. **Use strong passwords** - Generate with `openssl rand -base64 32`
3. **Rotate certificates regularly** - Set up automated renewal
4. **Monitor certificate expiry** - Set up alerts 30 days before expiry
5. **Use separate certificates per service** - Don't share private keys
6. **Restrict file permissions** - Keys should be 600, certs 644
7. **Use hardware security modules (HSM)** for private key storage in high-security environments

## Troubleshooting

### Common Issues

1. **Certificate verification failed**
   - Check certificate dates: `openssl x509 -in cert.crt -noout -dates`
   - Verify certificate chain: `openssl verify -CAfile ca.crt cert.crt`

2. **Connection refused**
   - Ensure ports are not blocked by firewall
   - Check service logs: `docker-compose logs <service>`

3. **Permission denied**
   - Check file permissions: `ls -la tls/`
   - Ensure Docker can read certificate files

### Testing TLS Connections

```bash
# Test Qdrant HTTPS
curl -k https://localhost:6333/health

# Test Neo4j Bolt with TLS
echo "RETURN 1;" | cypher-shell -a bolt+s://localhost:7687 -u neo4j -p your_password

# Test Redis TLS
redis-cli --tls --cert tls/redis/redis.crt --key tls/redis/redis.key --cacert tls/ca.crt -p 6379 ping
```
