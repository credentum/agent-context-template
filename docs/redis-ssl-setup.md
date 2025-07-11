# Redis SSL/TLS Configuration Guide

This guide explains how to configure SSL/TLS for Redis in the Agent-First Context System.

## Development Environment

For local development, SSL is disabled by default in `.ctxrc.yaml`:

```yaml
redis:
  ssl: false  # Disabled for local development
```

## Production Environment

For production deployments, you should enable SSL:

1. **Update `.ctxrc.yaml`**:
   ```yaml
   redis:
     ssl: true
     verify_ssl: true
   ```

2. **Set Environment Variable**:
   ```bash
   export CONTEXT_ENV=production
   ```

3. **Configure Redis Server** with SSL certificates:
   ```conf
   # redis.conf
   tls-port 6379
   port 0
   tls-cert-file /path/to/redis.crt
   tls-key-file /path/to/redis.key
   tls-ca-cert-file /path/to/ca.crt
   ```

## Self-Signed Certificates (Testing)

For testing with self-signed certificates:

1. Generate certificates:
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout redis.key -out redis.crt -days 365 -nodes
   ```

2. Configure Redis to use them (see above)

3. Set environment to allow self-signed certs:
   ```bash
   export CONTEXT_ENV=development
   ```

## Cloud Providers

### AWS ElastiCache
- SSL is enabled by default for Redis 6.0+
- Use the cluster endpoint with `ssl: true`

### Azure Cache for Redis
- SSL is enabled by default
- Use port 6380 for SSL connections

### Google Cloud Memorystore
- Enable in-transit encryption when creating the instance
- Use `ssl: true` in configuration

## Troubleshooting

1. **Connection Refused**: Ensure Redis is listening on the SSL port
2. **Certificate Errors**: Check certificate paths and validity
3. **Verification Failed**: For self-signed certs, ensure `CONTEXT_ENV` is not set to `production`

## Security Best Practices

1. Always use SSL in production
2. Use strong passwords with SSL
3. Rotate certificates regularly
4. Monitor SSL certificate expiration
5. Use certificate pinning for enhanced security