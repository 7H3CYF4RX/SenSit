# SenSIt - Complete Usage Guide

## 🚀 Quick Start

### 1. Installation

```bash
cd /home/viruz/Tools/Sen-SIt

# Run setup script
bash setup.sh

# Or manually:
pip3 install -r requirements.txt
chmod +x sensit.py
```

### 2. Configuration

```bash
# Set OpenAI API key (required for AI validation)
export OPENAI_API_KEY="sk-your-api-key-here"

# Optional: Set AWS credentials (for AWS secret validation)
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

### 3. Test Run

```bash
# Test with sample file
python sensit.py --file test_sample.txt --verbose

# Expected output: Multiple secrets detected with AI analysis
```

## 📖 Usage Examples

### Basic Scanning

```bash
# Scan a single file
python sensit.py --file config.js

# Scan a directory
python sensit.py --directory /path/to/project

# Scan a URL
python sensit.py --url https://example.com
```

### Advanced Options

```bash
# Full scan with all features
python sensit.py --directory ~/projects/webapp \
  --output report.json \
  --verbose

# Quick scan without AI (faster)
python sensit.py --file .env --no-ai

# Safe scan without live API validation
python sensit.py --url https://target.com --no-api

# Quiet mode (errors only)
python sensit.py --file secrets.txt --quiet

# JSON output only
python sensit.py --file config.json --json-only
```

### Bug Bounty Workflow

```bash
# 1. Initial reconnaissance scan
python sensit.py --url https://target.com \
  --no-api \
  --output initial_scan.json

# 2. Review findings and validate high-confidence secrets
python sensit.py --file initial_scan.json \
  --verbose

# 3. Live validation of confirmed secrets (with permission!)
python sensit.py --url https://target.com \
  --output final_report.json
```

## 🎯 Understanding Output

### Severity Levels

- **CRITICAL**: Confirmed active secrets (AWS keys, Stripe live keys, etc.)
- **HIGH**: Likely valid secrets with high AI confidence
- **MEDIUM**: Potential secrets requiring manual review
- **LOW**: Low-confidence matches, likely false positives

### Validation Status

- **✓ CONFIRMED**: Live API validation successful - SECRET IS ACTIVE
- **~ LIKELY**: High AI confidence (>85%) - probably real
- **? POSSIBLE**: Medium AI confidence (60-85%) - needs review
- **○ UNVERIFIED**: Low confidence or no validation

### Exit Codes

- `0`: No secrets found
- `1`: Potential secrets found
- `2`: Confirmed active secrets found
- `130`: Interrupted by user

## 🔧 Configuration

### Custom Config File

Create `my_config.yml`:

```yaml
openai:
  model: "gpt-4o-mini"
  batch_size: 10

scanning:
  max_depth: 5
  max_pages: 1000
  rate_limit: 20

validation:
  enable_ai_validation: true
  enable_api_validation: false  # Safer for testing
  ai_confidence_threshold: 80
```

Use it:
```bash
python sensit.py --config my_config.yml --url https://target.com
```

## 📊 Output Formats

### CLI Output

Beautiful colored terminal output with:
- Severity indicators (color-coded)
- Validation status icons
- AI confidence scores
- Code context
- API validation details

### JSON Export

```bash
python sensit.py --file config.js --output report.json
```

Output structure:
```json
{
  "target": "config.js",
  "total_files_scanned": 1,
  "total_secrets_found": 5,
  "scan_duration": 3.45,
  "secrets": [
    {
      "type": "aws_access_key",
      "value": "AKIA...",
      "location": "config.js:10",
      "severity": "CRITICAL",
      "status": "CONFIRMED",
      "entropy": 3.82,
      "ai_confidence": 95,
      "ai_reasoning": "Valid AWS access key format",
      "api_valid": true,
      "api_details": {
        "account_id": "123456789012"
      }
    }
  ]
}
```

## 🤖 AI Validation Details

### How It Works

1. **Context Extraction**: Grabs ±5 lines around the secret
2. **Prompt Engineering**: Sends to OpenAI with specialized prompt
3. **Analysis**: AI determines if real secret or test/example
4. **Confidence Score**: Returns 0-100% confidence
5. **Reasoning**: Provides explanation

### Cost Optimization

- **Batch Processing**: Groups 10 secrets per API call
- **Smart Filtering**: Only validates high-entropy matches
- **Caching**: Saves AI responses for repeated scans
- **Model Selection**: Uses gpt-4o-mini (cheap & fast)

**Typical Costs:**
- Small file: $0.01
- Medium project: $0.50
- Large codebase: $2.00

### Disabling AI

```bash
# Faster but less accurate
python sensit.py --file config.js --no-ai
```

## ✅ API Validation

### Supported Services

| Service | Validation Method | Risk Level |
|---------|------------------|------------|
| AWS | STS GetCallerIdentity | ⚠️ High |
| Stripe | Balance Retrieve | ⚠️ High |
| GitHub | User API | ⚠️ Medium |
| Slack | Webhook POST | ⚠️ Low |
| Twilio | Account Verify | ⚠️ Medium |

### Safety Considerations

⚠️ **WARNING**: Live API validation makes real requests!

- Only validate with explicit permission
- Use `--no-api` for reconnaissance
- Be aware of rate limits
- Some APIs may log validation attempts

### Safe Testing

```bash
# Scan without live validation
python sensit.py --url https://target.com --no-api

# Review findings manually
cat report.json

# Validate specific secrets with permission
# (manually test high-confidence findings)
```

## 🎓 Advanced Usage

### Custom Patterns

Add to `signatures/patterns.yml`:

```yaml
custom_api_key:
  pattern: 'CUSTOM_[A-Z0-9]{32}'
  entropy_min: 3.5
  description: "Custom API Key"
  severity: "HIGH"
  validation: "ai_only"
```

### Filtering Results

```bash
# Only show CRITICAL secrets
python sensit.py --file config.js | grep "CRITICAL"

# Export and filter JSON
python sensit.py --file config.js --output report.json
jq '.secrets[] | select(.severity=="CRITICAL")' report.json
```

### Integration with Other Tools

```bash
# Pipe URLs from subfinder
subfinder -d target.com | while read url; do
  python sensit.py --url "$url" --no-api --quiet
done

# Scan git repositories
find ~/repos -name ".git" -type d | while read repo; do
  python sensit.py --directory "$(dirname $repo)"
done
```

## 🐛 Troubleshooting

### Common Issues

**1. OpenAI API Key Not Found**
```bash
export OPENAI_API_KEY="sk-..."
# Or add to ~/.bashrc for persistence
```

**2. Import Errors**
```bash
pip3 install -r requirements.txt --upgrade
```

**3. Permission Denied**
```bash
chmod +x sensit.py
```

**4. SSL Certificate Errors**
```bash
# Disable SSL verification (not recommended)
# Edit config.yml: verify_ssl: false
```

**5. Rate Limiting**
```bash
# Reduce rate in config.yml
scanning:
  rate_limit: 5  # slower but safer
```

### Debug Mode

```bash
# Enable verbose logging
python sensit.py --file config.js --verbose

# Python debug mode
python -u sensit.py --file config.js
```

## 📈 Performance Tips

### Speed Optimization

```bash
# Disable AI for faster scans
python sensit.py --directory /large/project --no-ai

# Reduce max pages for web scans
# Edit config.yml: max_pages: 100

# Use multiple instances for large directories
find /project -type f -name "*.js" | xargs -P 4 -I {} python sensit.py --file {}
```

### Memory Optimization

- Scan directories in chunks
- Use `--quiet` mode for large scans
- Disable verbose output
- Process files individually instead of whole directories

## 🔒 Security Best Practices

### DO:
✅ Get written permission before scanning
✅ Use `--no-api` for initial reconnaissance
✅ Report findings through proper channels
✅ Secure your scan reports
✅ Use rate limiting to avoid detection

### DON'T:
❌ Scan targets without authorization
❌ Validate secrets without permission
❌ Share discovered secrets publicly
❌ Use aggressive scanning on production systems
❌ Ignore responsible disclosure practices

## 📚 Additional Resources

- **README.md**: Full documentation
- **config.yml**: Configuration options
- **signatures/patterns.yml**: All regex patterns
- **test_sample.txt**: Test file with sample secrets

## 💡 Tips & Tricks

### 1. Create Aliases

```bash
# Add to ~/.bashrc
alias sensit='python /home/viruz/Tools/Sen-SIt/sensit.py'
alias sensit-safe='python /home/viruz/Tools/Sen-SIt/sensit.py --no-api'
```

### 2. Batch Processing

```bash
# Scan multiple files
for file in *.js; do
  python sensit.py --file "$file" --output "reports/${file}.json"
done
```

### 3. Integration with CI/CD

```bash
# Add to .gitlab-ci.yml or .github/workflows
python sensit.py --directory . --no-api --json-only > secrets.json
if [ -s secrets.json ]; then exit 1; fi
```

### 4. Quick Checks

```bash
# Fast check without validation
python sensit.py --file .env --no-ai --no-api --quiet
echo $?  # 0 = no secrets, 1 = secrets found
```

## 🎯 Real-World Examples

### Example 1: Bug Bounty Recon
```bash
# Discover secrets without triggering alerts
python sensit.py --url https://target.com \
  --no-api \
  --output recon.json \
  --verbose
```

### Example 2: Code Review
```bash
# Scan before committing
python sensit.py --directory . --no-api
```

### Example 3: Incident Response
```bash
# Quick check for exposed credentials
python sensit.py --file suspicious_file.log \
  --verbose \
  --output incident_report.json
```

---

## 🆘 Need Help?

- Check README.md for full documentation
- Review test_sample.txt for examples
- Run `python sensit.py --help`
- Enable `--verbose` for detailed output

**Happy Hunting! 🎯**
