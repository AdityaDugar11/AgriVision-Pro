import re

with open("README.md", "r") as f:
    content = f.read()

# Replace Our Solution section
solution_pattern = r"### Our Solution.*?24/7 availability.*?\(anytime, anywhere\)"
replacement = """### Prototype / Hackathon Project

**Disclaimer**: This project is a prototype / hackathon project and does not perform actual image-based crop disease detection.

- **Dataset**: None.
- **Model actually used**: `google/flan-t5-large` (a text-to-text generation LLM). No computer vision model is used.
- **Evaluation methodology**: None.
- **Measured accuracy**: N/A (0 test samples).
- **Number of test samples**: 0.
- **Actual supported crops**: Any crop name provided in the text input.
- **Whether WhatsApp integration actually works**: Yes, using the Twilio API, but requires the user to provide their own valid Twilio credentials.
- **Whether deployment is live**: No, the live URL on Railway is currently inactive.
- **What is simulated**: Image analysis is fully simulated. The uploaded image is saved but never analyzed. The model hallucinates a disease diagnosis and treatment purely based on the provided text inputs (crop name and location)."""

content = re.sub(solution_pattern, replacement, content, flags=re.DOTALL)

# Replace "Production-ready MVP"
content = content.replace("**Status:** Production-ready MVP", "**Status:** Prototype / Hackathon Project")

# Replace 95%+ accuracy claim anywhere else if exists
content = content.replace("✅ **95%+ accuracy** for Indian crop diseases", "")
content = content.replace("✅ Production-ready", "✅ Prototype demonstration")

with open("README.md", "w") as f:
    f.write(content)
print("Updated README.md")
