---
title: PhysioGemma
emoji: 🩺
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.0.0
app_file: app.py
pinned: true
license: cc-by-4.0
---

# PhysioGemma — AI Physiotherapy Assistant

**Gemma 4 Good Hackathon | Health & Sciences Track**

PhysioGemma uses Google's Gemma 4 open model to provide evidence-based physiotherapy exercise prescriptions through natural language interaction.

## What it does

1. **Natural Language Intake**: Describe your pain in plain English or Hindi
2. **Clinical Parameter Extraction**: Gemma 4 extracts condition, pain level, age, duration, comorbidities
3. **Evidence-Based Level Assignment**: Uses Boonstra 2014 VAS cutoffs + ACSM/ADA modifiers
4. **Personalized Exercise Plan**: 4 exercises with sets, reps, video demos
5. **Clinical Reasoning**: Gemma 4 explains why each exercise was chosen
6. **Multilingual**: Full Hindi support

## Clinical References

- **Boonstra 2014**: VAS pain cutoffs for exercise intensity classification
- **NICE NG59**: Low back pain and sciatica management guidelines
- **ACSM**: Exercise prescription guidelines for older adults
- **ADA**: Comorbidity-adjusted exercise modifications
- **Cochrane Reviews**: Evidence for knee OA, neck pain, frozen shoulder interventions

## Architecture

```
Patient Input (text) → Gemma 4 Function Calling → Extract Clinical Parameters
→ Evidence-Based Level Assignment (Boonstra/ACSM/ADA)
→ Exercise Prescription from Knowledge Base
→ Gemma 4 Clinical Reasoning & Explanation
→ Multilingual Output (English/Hindi) with YouTube Video Demos
```

## Tech Stack

- **LLM**: Gemma 4 26B MoE via Google AI Studio
- **Frontend**: Gradio
- **Deployment**: HuggingFace Spaces
- **License**: CC-BY 4.0

## Local Setup

```bash
pip install -r requirements.txt
export GOOGLE_API_KEY="your-api-key-from-aistudio.google.com"
python app.py
```

## The Problem

Over 1.7 billion people worldwide suffer from musculoskeletal conditions (WHO, 2023). In countries like India, there is only 1 physiotherapist per 19,000 people. Most patients never receive proper exercise guidance, leading to chronic pain, disability, and reduced quality of life.

## The Solution

PhysioGemma democratizes access to evidence-based physiotherapy guidance by combining:
- **Gemma 4's reasoning** for understanding patient descriptions in any language
- **Clinical evidence** from published guidelines for safe, appropriate prescriptions
- **Function calling** for structured, reliable clinical parameter extraction
- **Edge potential**: Gemma 4 E4B can run on clinic laptops (8GB RAM) for offline use

## Author

Gaurav Birwatkar — [GitHub](https://github.com/birwatkar123-collab)

## License

CC-BY 4.0
