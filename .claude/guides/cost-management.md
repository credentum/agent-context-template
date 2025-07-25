# Cost Management & Token Optimization

## 💰 Token Usage & Cost Control

### Monitoring Usage
Run locally to inspect monthly token burn:
```bash
npx ccusage@latest
```

### Cost Optimization Strategies

1. **Keep prompts tight**
   - Prefer bullet lists to prose
   - Be specific and concise
   - Avoid redundant context

2. **Context Management**
   - Use `/compact` every ~100 lines of dialogue
   - Use `/clear` between unrelated tasks
   - Don't include unnecessary files

3. **GitHub Actions Limits**
   - Set `max_turns: 3` unless task truly needs more
   - Use `timeout_minutes` to prevent runaway jobs
   - Consider using claude-sonnet for simple tasks

### Efficient Patterns
- Batch related changes together
- Use direct prompts for automated reviews
- Leverage caching where possible

### Cost Estimation
- Opus: ~$15 per million input tokens
- Sonnet: ~$3 per million input tokens
- Consider model choice based on task complexity

### Budget Controls
```yaml
# In GitHub Actions
max_turns: 3          # Limit conversation length
timeout_minutes: 10   # Prevent runaway jobs
```

### Best Practices
- Review token usage weekly
- Set up billing alerts
- Use Sonnet for routine tasks
- Reserve Opus for complex problems
- Optimize prompts based on usage patterns
