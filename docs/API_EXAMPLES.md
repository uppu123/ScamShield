# API Examples

```bash
# Health
curl http://localhost:5000/health

# Analyze text
curl -X POST http://localhost:5000/analyze_text \
  -H "Content-Type: application/json" \
  -d '{"text": "Urgent hiring! Work from home, no experience, pay registration fee Rs 1000, earn Rs 50000 per month. Contact whatsapp."}'

# Analyze screenshot
curl -X POST http://localhost:5000/analyze_image \
  -F "image=@posting.png"

# Report a scam
curl -X POST http://localhost:5000/report_scam \
  -H "Content-Type: application/json" \
  -d '{"text": "...", "notes": "asked for fee on WhatsApp", "source": "telegram"}'

# Recent reports
curl "http://localhost:5000/reports?limit=10"

# Chat Q&A
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Is asking for a security deposit normal?"}'
```
