# CyberShield AI - Project Understanding Guide

> This document explains **what problem we are solving**, **why it matters**, and **how each module contributes** to the overall solution.

---

# 1. Problem Statement

Modern organizations generate millions of security events every day.

These events include:

- Network traffic
- Login attempts
- API requests
- DNS queries
- Emails
- SMS messages
- Web requests

Among millions of legitimate events, a small number may indicate cyber attacks such as:

- Phishing
- Credential stuffing
- Port scanning
- DDoS attacks
- Malware communication
- Insider threats

Security analysts cannot manually inspect every event.

Therefore, organizations need an intelligent system that can automatically answer:

> **Which events are likely to be malicious, why are they suspicious, and what should the security team do next?**

This is the core problem our project solves.

---

# 2. Our Solution

CyberShield AI is an Explainable AI-powered Cybersecurity Threat Detection Platform.

Instead of relying only on Generative AI, the system combines:

- Statistical Anomaly Detection
- Machine Learning Classification
- Bayesian Risk Fusion
- Explainable AI (XAI)
- Generative AI Response Automation

This layered architecture reduces false positives, improves explainability, and provides actionable guidance for Security Operations Center (SOC) analysts.

---

# 3. High-Level Architecture

```
                    Network Logs
                         │
                         ▼
              Feature Engineering
                         │
                         ▼
      Module 1 - Statistical Detection
                         │
                         ▼
      Module 2 - Phishing Classification
                         │
                         ▼
           Bayesian Risk Fusion
                         │
                         ▼
      Module 3 - Explainable AI Dashboard
                         │
                         ▼
 Module 4 - Guided Response Playbook
```

Each module performs a specific task.

The output of one module becomes the input to the next.

---

# 4. Module 1 - Statistical Anomaly Detection

## Purpose

Identify unusual network behaviour.

Module 1 does NOT determine whether traffic is malicious.

Instead, it answers:

> "Does this behaviour significantly differ from normal network activity?"

---

## Input

Network logs containing features such as:

- Packet size
- Connection duration
- Failed connections
- Request frequency
- Burst activity

---

## Processing

Feature Engineering creates statistical features.

The data is analysed using:

- Isolation Forest
- One-Class SVM

The models are combined into an ensemble to generate a normalized anomaly score.

---

## Output

```
anomaly_score (0-100)
```

Higher score means the behaviour is more unusual.

---

## Why this module exists

Many attacks behave differently from normal users.

This module quickly filters suspicious behaviour without requiring labeled attack data.

---

# 5. Module 2 - Phishing Detection & Bayesian Risk Fusion

## Purpose

Determine whether suspicious activity also resembles phishing or malicious communication.

Module 2 analyses:

- Emails
- URLs
- SMS
- API payloads
- Login attempts

using Natural Language Processing and Machine Learning.

---

## Processing

TF-IDF converts text into numerical vectors.

A LightGBM classifier estimates the phishing probability.

This probability is combined with Module 1's anomaly score using Bayesian Risk Fusion.

---

## Output

```
final_risk_probability
```

This represents the overall probability that an event is malicious.

---

## Why Bayesian Fusion?

Instead of trusting a single model, Bayesian inference combines multiple independent pieces of evidence.

This significantly reduces false positives.

---

# 6. Module 3 - Explainable AI Dashboard

## Purpose

Security analysts need to understand WHY an alert was generated.

Black-box AI is difficult to trust.

Module 3 provides transparent explanations.

---

## Processing

Uses:

- SHAP
- LIME
- Plotly
- Streamlit

to explain:

- Which features contributed most
- How much each feature influenced the prediction
- Overall threat trends

---

## Dashboard Pages

### Threat Overview

Displays:

- Risk distribution
- Threat summary
- Recent alerts

---

### Explainability

Shows:

- SHAP values
- Feature importance
- Local explanations

---

### Threat Explorer

Allows analysts to inspect individual security events.

---

# 7. Module 4 - Guided Response Playbook

## Purpose

Assist SOC analysts after a high-risk event has been confirmed.

Generative AI is intentionally used ONLY after statistical validation.

---

## Why?

LLMs are excellent at generating human-readable recommendations.

However, they should not make the primary security decision.

Statistical models make the detection decision.

LLMs assist with the response.

---

## Response includes

- Incident summary
- Threat explanation
- MITRE ATT&CK mapping
- Suggested investigation
- Containment steps
- Recovery recommendations
- Executive summary

---

# 8. Complete Workflow

```
Raw Network Logs
        │
        ▼
Feature Engineering
        │
        ▼
Statistical Anomaly Detection
        │
        ▼
Phishing Classification
        │
        ▼
Bayesian Risk Fusion
        │
        ▼
Explainable AI Dashboard
        │
        ▼
Guided Response Playbook
```

---

# 9. Why This Architecture?

Many AI cybersecurity projects directly send logs to an LLM.

Our project follows a layered engineering approach.

Instead of:

```
Logs
 ↓
LLM
 ↓
Alert
```

we use:

```
Logs
 ↓
Statistical Detection
 ↓
ML Classification
 ↓
Bayesian Evidence Fusion
 ↓
Explainable AI
 ↓
LLM Response Generation
```

This approach is:

- More explainable
- More reliable
- More scalable
- More cost-effective
- Better suited for enterprise SOC environments

---

# 10. Key Innovations

- Statistical anomaly detection for unknown attacks
- Bayesian probability fusion to reduce false positives
- Explainable AI using SHAP and LIME
- Interactive SOC dashboard
- LLM-assisted incident response
- Modular architecture for easy extension
- Lightweight models suitable for edge deployment

---

# 11. Real-World Impact

CyberShield AI helps organizations:

- Detect suspicious network behaviour earlier
- Reduce alert fatigue
- Explain AI decisions to analysts
- Respond faster to cyber incidents
- Improve Security Operations Center efficiency

---

# 12. Future Enhancements

- Live packet capture integration
- SIEM integration (Splunk, Microsoft Sentinel)
- Threat intelligence API integration
- Real-time streaming analytics
- Cloud deployment
- Multi-tenant enterprise architecture
- Continuous online model learning

---

# Final Vision

CyberShield AI is not just an AI chatbot.

It is a layered cybersecurity decision-support platform that combines Statistical Learning, Machine Learning, Bayesian Inference, Explainable AI, and Generative AI to help organizations detect, understand, and respond to cyber threats efficiently.