# CI Security Guide

This guide covers the security features implemented in Phase 2 of the CI migration, including cryptographic signing of CI results and secure key management.

## Table of Contents
1. [Overview](#overview)
2. [Security Architecture](#security-architecture)
3. [Key Management](#key-management)
4. [Signing CI Results](#signing-ci-results)
5. [Verifying Signatures](#verifying-signatures)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Overview

The CI security system provides:
- **Cryptographic signing** of all CI results using GPG
- **Signature verification** before accepting results
- **Tamper detection** for posted CI results
- **Backward compatibility** with unsigned results

## Security Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Local CI Run   │────▶│  Sign Results    │────▶│  Post to GitHub │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                            │
                               ▼                            ▼
                        ┌──────────────┐           ┌─────────────────┐
                        │ Private Key  │           │ Check Run with  │
                        │ (CI_SIGNING_ │           │ Signature in    │
                        │     KEY)     │           │ external_id     │
                        └──────────────┘           └─────────────────┘
                                                            │
                                                            ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Update PR Status│◀────│ Verify Signature │◀────│ CI Verifier     │
└─────────────────┘     └──────────────────┘     │ Workflow        │
                               ▲                   └─────────────────┘
                               │
                        ┌──────────────┐
                        │  Public Key  │
                        │ (.github/ci- │
                        │ public-key)  │
                        └──────────────┘
```

## Key Management

### Initial Setup

1. **Generate CI Signing Keypair**:
   ```bash
   ./scripts/generate-ci-keypair.py \
     --name "CI Bot" \
     --email "ci@example.com" \
     --output-dir ci-keys
   ```

2. **Add Public Key to Repository**:
   ```bash
   cp ci-keys/ci-public-key.asc .github/ci-public-key.asc
   git add .github/ci-public-key.asc
   git commit -m "feat(ci): add CI signing public key"
   git push
   ```

3. **Add Private Key to CI Environment**:
   ```bash
   # Base64 encode the private key
   cat ci-keys/ci-private-key.asc | base64 -w0 | pbcopy

   # Add to GitHub Secrets as CI_SIGNING_KEY
   # Settings → Secrets → Actions → New repository secret
   ```

4. **Add Key Fingerprint** (optional but recommended):
   ```bash
   # Add the fingerprint as CI_KEY_FINGERPRINT secret
   cat ci-keys/key-fingerprint.txt
   ```

5. **Secure Private Key**:
   ```bash
   # After adding to CI, securely delete local copy
   shred -vfz ci-keys/ci-private-key.asc
   rm -rf ci-keys
   ```

### Key Rotation

When the key approaches expiration (2 years by default):

1. Generate new keypair with `generate-ci-keypair.py`
2. Update `.github/ci-public-key.asc` in repository
3. Update `CI_SIGNING_KEY` secret with new private key
4. Keep old public key for verifying historical results

## Signing CI Results

### Automatic Signing

Enable signing when posting CI results:

```bash
# With environment variable
export CI_ENABLE_SIGNING=true
./scripts/post-ci-results.py ci-output.json --pr 123

# Or with command flag
./scripts/post-ci-results.py ci-output.json --pr 123 --enable-signing
```

### Manual Signing (for testing)

```bash
# Sign results file
./scripts/sign-ci-results.py ci-output.json --output signed-results.json

# Verify signature
./scripts/sign-ci-results.py ci-output.json \
  --verify \
  --public-key .github/ci-public-key.asc \
  --signature "BASE64_SIGNATURE"
```

### What Gets Signed

The entire CI results JSON is signed, including:
- Test results
- Coverage data
- Linting results
- Type checking results
- Timestamps and metadata
- Runner information

## Verifying Signatures

### Automatic Verification

The `ci-local-verifier` workflow automatically:
1. Extracts signatures from check run `external_id`
2. Loads public key from `.github/ci-public-key.asc`
3. Verifies signature matches results
4. Reports verification status in PR

### Manual Verification

```bash
# Verify results file with signature
./scripts/verify-ci-results.py ci-results.json \
  --public-key .github/ci-public-key.asc

# The script automatically detects wrapped results with signatures
```

### Verification Status

Results show signature status:
- ✅ **Signed**: Results cryptographically signed
- ⚠️ **Not signed**: Results not signed (backward compatible)
- ❌ **Invalid signature**: Signature verification failed

## Troubleshooting

### Common Issues

1. **"No private key provided" error**
   - Ensure `CI_SIGNING_KEY` environment variable is set
   - Check the key is base64 encoded properly

2. **"Failed to import private key"**
   - Verify the private key is valid GPG format
   - Check base64 decoding: `echo $CI_SIGNING_KEY | base64 -d`

3. **"Signature verification failed"**
   - Ensure public key matches private key
   - Check results haven't been modified
   - Verify canonical JSON formatting

4. **"Public key not found"**
   - Ensure `.github/ci-public-key.asc` exists
   - Check file permissions are readable

### Debug Commands

```bash
# Test key import
export CI_SIGNING_KEY="your_base64_key"
python -c "from sign_ci_results import CIResultSigner; s = CIResultSigner()"

# Verify key fingerprint
gpg --import .github/ci-public-key.asc
gpg --fingerprint

# Test signing locally
echo '{"test": "data"}' > test.json
./scripts/sign-ci-results.py test.json
```

## Best Practices

### Security

1. **Never commit private keys** to the repository
2. **Use strong passphrases** for manual keys (CI keys have no passphrase)
3. **Rotate keys regularly** (before expiration)
4. **Monitor verification failures** as potential tampering
5. **Backup public keys** for historical verification

### Performance

1. **Signing overhead**: <100ms per operation
2. **Verification overhead**: <50ms per operation
3. **Cache signed results** between retries
4. **Use --enable-signing selectively** during testing

### Integration

1. **Start with signing disabled** to test integration
2. **Enable signing gradually** (warnings before failures)
3. **Monitor success rates** after enabling
4. **Document key management** procedures for your team

### Configuration

Add to `.coverage-config.json` to require signatures:
```json
{
  "require_signature": true
}
```

This will make signature verification mandatory for all CI results.

## Migration Path

### Phase 1: Setup (Current)
- [x] Generate and distribute keys
- [x] Update workflows to support signatures
- [x] Test with signing enabled manually

### Phase 2: Soft Enforcement
- [ ] Enable signing by default in CI
- [ ] Show warnings for unsigned results
- [ ] Monitor signature verification rates

### Phase 3: Hard Enforcement
- [ ] Require signatures via config
- [ ] Reject unsigned results
- [ ] Full security compliance

## Summary

The CI security system provides strong guarantees about the authenticity and integrity of CI results while maintaining backward compatibility and good performance. Follow the setup guide carefully and test thoroughly before enabling enforcement.
