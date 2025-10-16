# Sample Temporal Classification Output

This document contains vetted examples demonstrating the expected output from the temporal classification prompts. Each classification shows how to set fact type, temporal type, confidence, validity windows, and invalidations.

## Example 1: Financial Metric (FACT, STATIC)

**Source Text:**
```
Tesla's quarterly revenue was $25B in Q1 2024.
```

**Fact:**
```json
{
  "subject": "Tesla quarterly revenue",
  "predicate": "was",
  "object": "$25B in Q1 2024"
}
```

**Classification:**
```json
{
  "fact_index": 0,
  "fact_type": "FACT",
  "temporal_type": "STATIC",
  "confidence": 0.95,
  "valid_from": "2024-01-01T00:00:00Z",
  "valid_until": "2024-03-31T23:59:59Z",
  "is_open_interval": false,
  "invalidates_fact_ids": [],
  "invalidation_reason": ""
}
```

**Rationale:**
- FACT: Objective, verifiable financial data
- STATIC: Quarterly revenue doesn't change frequently (fixed for Q1 2024)
- High confidence: Explicit temporal marker and clear value
- Closed interval: Q1 2024 has a defined start and end

---

## Example 2: Universal Truth (FACT, ATEMPORAL)

**Source Text:**
```
Water boils at 100°C at sea level.
```

**Fact:**
```json
{
  "subject": "Water",
  "predicate": "boils at",
  "object": "100°C at sea level"
}
```

**Classification:**
```json
{
  "fact_index": 0,
  "fact_type": "FACT",
  "temporal_type": "ATEMPORAL",
  "confidence": 1.0,
  "valid_from": "beginning_of_time",
  "valid_until": "open",
  "is_open_interval": true,
  "invalidates_fact_ids": [],
  "invalidation_reason": ""
}
```

**Rationale:**
- FACT: Scientific fact, objectively verifiable
- ATEMPORAL: Physical law, doesn't change over time
- Perfect confidence: Well-established scientific principle
- Open interval: Valid indefinitely

---

## Example 3: Current Stock Price (FACT, DYNAMIC)

**Source Text:**
```
As of market close today, TSLA stock is trading at $250.75.
```

**Fact:**
```json
{
  "subject": "TSLA stock",
  "predicate": "trading at",
  "object": "$250.75"
}
```

**Classification:**
```json
{
  "fact_index": 0,
  "fact_type": "FACT",
  "temporal_type": "DYNAMIC",
  "confidence": 0.9,
  "valid_from": "extraction_time",
  "valid_until": "unknown",
  "is_open_interval": true,
  "invalidates_fact_ids": [],
  "invalidation_reason": "Price snapshot expected to change within hours."
}
```

**Rationale:**
- FACT: Verifiable market data
- DYNAMIC: Stock prices change continuously
- High confidence: Explicit temporal context ("as of market close")
- Open interval: Currently valid but will change soon
- valid_until unknown: Next price change unpredictable

---

## Example 4: Corporate Leadership (FACT, STATIC)

**Source Text:**
```
Elon Musk is the CEO of Tesla.
```

**Fact:**
```json
{
  "subject": "Elon Musk",
  "predicate": "is",
  "object": "CEO of Tesla"
}
```

**Classification:**
```json
{
  "fact_index": 0,
  "fact_type": "FACT",
  "temporal_type": "STATIC",
  "confidence": 0.85,
  "valid_from": "statement_time",
  "valid_until": "open",
  "is_open_interval": true,
  "invalidates_fact_ids": [],
  "invalidation_reason": ""
}
```

**Rationale:**
- FACT: Verifiable corporate information
- STATIC: CEO positions change rarely (years between changes)
- Good confidence: Present tense suggests current validity
- Open interval: Currently valid with no known end date

---

## Example 5: Opinion Statement (OPINION, STATIC)

**Source Text:**
```
The new iPhone design is beautiful and innovative.
```

**Fact:**
```json
{
  "subject": "new iPhone design",
  "predicate": "is",
  "object": "beautiful and innovative"
}
```

**Classification:**
```json
{
  "fact_index": 0,
  "fact_type": "OPINION",
  "temporal_type": "STATIC",
  "confidence": 0.95,
  "valid_from": "statement_time",
  "valid_until": "open",
  "is_open_interval": true,
  "invalidates_fact_ids": [],
  "invalidation_reason": ""
}
```

**Rationale:**
- OPINION: Subjective aesthetic judgment
- STATIC: Opinions change slowly, design is fixed
- High confidence: Clear subjective language ("beautiful")
- Open interval: Opinion likely persists unless retracted

---

## Example 6: Future Prediction (PREDICTION, DYNAMIC)

**Source Text:**
```
Analysts predict Tesla's revenue will reach $120B by end of 2025.
```

**Fact:**
```json
{
  "subject": "Tesla revenue",
  "predicate": "will reach",
  "object": "$120B by end of 2025"
}
```

**Classification:**
```json
{
  "fact_index": 0,
  "fact_type": "PREDICTION",
  "temporal_type": "DYNAMIC",
  "confidence": 0.7,
  "valid_from": "statement_time",
  "valid_until": "2025-12-31T23:59:59Z",
  "is_open_interval": false,
  "invalidates_fact_ids": [],
  "invalidation_reason": "Forecast through end of 2025."
}
```

---

## Example 6: Leadership Change (Invalidation Scenario)

**Source Text:**
```
On 2025-03-01 Omar stepped down as CTO. On 2025-03-15 Alicia became CTO.
```

**Facts:**
```json
[
  {
    "fact_id": "omar_cto",
    "subject": "Omar",
    "predicate": "serves as",
    "object": "CTO"
  },
  {
    "fact_id": "alicia_cto",
    "subject": "Alicia",
    "predicate": "serves as",
    "object": "CTO"
  }
]
```

**Classifications:**
```json
[
  {
    "fact_index": 0,
    "fact_type": "FACT",
    "temporal_type": "STATIC",
    "confidence": 0.8,
    "valid_from": "statement_time",
    "valid_until": "2025-03-14T23:59:59Z",
    "is_open_interval": false,
    "invalidates_fact_ids": [],
    "invalidation_reason": "Closed once successor named"
  },
  {
    "fact_index": 1,
    "fact_type": "FACT",
    "temporal_type": "STATIC",
    "confidence": 0.9,
    "valid_from": "2025-03-15T00:00:00Z",
    "valid_until": "open",
    "is_open_interval": true,
    "invalidates_fact_ids": ["omar_cto"],
    "invalidation_reason": "Replaces Omar as CTO effective 2025-03-15"
  }
]
```

**Rationale:**
- PREDICTION: Future-oriented forecast
- DYNAMIC: Predictions change as new data emerges
- Moderate confidence: Analyst predictions are uncertain
- Closed interval: Prediction has explicit end date (2025)

---

## Example 7: Historical Event (FACT, STATIC)

**Source Text:**
```
Tesla was founded in 2003 by Martin Eberhard and Marc Tarpenning.
```

**Fact:**
```json
{
  "subject": "Tesla",
  "predicate": "was founded by",
  "object": "Martin Eberhard and Marc Tarpenning"
}
```

**Classification:**
```json
{
  "fact_index": 0,
  "fact_type": "FACT",
  "temporal_type": "ATEMPORAL",
  "confidence": 0.95,
  "valid_from": "2003-01-01T00:00:00Z",
  "valid_until": "open",
  "is_open_interval": true
}
```

**Rationale:**
- FACT: Verifiable historical event
- ATEMPORAL: Historical facts don't change (founding is immutable)
- High confidence: Well-documented historical event
- Open interval: Remains true indefinitely once established

---

## Example 8: Employee Count (FACT, DYNAMIC)

**Source Text:**
```
Tesla currently employs approximately 140,000 people worldwide.
```

**Fact:**
```json
{
  "subject": "Tesla",
  "predicate": "employs",
  "object": "approximately 140,000 people worldwide"
}
```

**Classification:**
```json
{
  "fact_index": 0,
  "fact_type": "FACT",
  "temporal_type": "DYNAMIC",
  "confidence": 0.75,
  "valid_from": "extraction_time",
  "valid_until": "unknown",
  "is_open_interval": true
}
```

**Rationale:**
- FACT: Verifiable corporate metric
- DYNAMIC: Employee counts change frequently (monthly)
- Moderate confidence: "approximately" indicates imprecision
- Open interval: Currently valid but will change soon

---

## Example 9: Product Specification (FACT, ATEMPORAL)

**Source Text:**
```
The Model 3 Standard Range has a 272-mile EPA estimated range.
```

**Fact:**
```json
{
  "subject": "Model 3 Standard Range",
  "predicate": "has",
  "object": "272-mile EPA estimated range"
}
```

**Classification:**
```json
{
  "fact_index": 0,
  "fact_type": "FACT",
  "temporal_type": "STATIC",
  "confidence": 0.9,
  "valid_from": "statement_time",
  "valid_until": "open",
  "is_open_interval": true
}
```

**Rationale:**
- FACT: Verifiable product specification
- STATIC: Official EPA ratings don't change frequently for a model
- High confidence: Official specification
- Open interval: Valid until model is updated

---

## Example 10: Market Sentiment (OPINION, DYNAMIC)

**Source Text:**
```
Investors are currently optimistic about Tesla's AI initiatives.
```

**Fact:**
```json
{
  "subject": "Investors",
  "predicate": "are optimistic about",
  "object": "Tesla's AI initiatives"
}
```

**Classification:**
```json
{
  "fact_index": 0,
  "fact_type": "OPINION",
  "temporal_type": "DYNAMIC",
  "confidence": 0.8,
  "valid_from": "extraction_time",
  "valid_until": "unknown",
  "is_open_interval": true
}
```

**Rationale:**
- OPINION: Subjective market sentiment
- DYNAMIC: Market sentiment changes rapidly
- Good confidence: "currently" indicates recency
- Open interval: Valid now but may change quickly

---

## Classification Decision Tree

### Fact Type Classification

```
Is the statement objectively verifiable?
├─ YES → Is it about the future?
│         ├─ YES → PREDICTION
│         └─ NO → FACT
└─ NO → OPINION
```

### Temporal Type Classification (for FACT)

```
Does the fact change over time?
├─ NEVER CHANGES → ATEMPORAL
│   Examples: Scientific laws, historical events, mathematical truths
├─ CHANGES RARELY (years) → STATIC
│   Examples: CEO, headquarters location, product specifications
└─ CHANGES FREQUENTLY (days/weeks) → DYNAMIC
    Examples: Stock prices, employee count, current metrics
```

### Confidence Scoring

- **1.0**: Scientific facts, mathematical truths, explicit temporal markers
- **0.9-0.95**: Well-documented historical events, official specifications
- **0.7-0.85**: Present tense corporate facts, analyst predictions
- **0.4-0.6**: Ambiguous temporal context, uncertain data sources
- **0.1-0.3**: Insufficient context, conflicting information

---

## Notes for Prompt Tuning

1. **ATEMPORAL vs STATIC**: ATEMPORAL facts are immutable truths (physics, history). STATIC facts can change but rarely do (CEO, locations).

2. **Temporal Markers**: Explicit markers ("as of", "currently", "in 2024") significantly increase confidence.

3. **Open vs Closed Intervals**:
   - Open: Facts currently valid with no known expiration (CEO positions, current metrics)
   - Closed: Facts with explicit end dates (quarterly revenue, time-bounded predictions)

4. **Confidence Calibration**: Lower confidence for approximate values ("around", "approximately") and ambiguous time references.

5. **Prediction Handling**: All future-oriented statements are PREDICTIONS, even if stated with high certainty.
