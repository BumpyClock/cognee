# Sample Atomic Fact Extraction Output

This document contains vetted examples demonstrating the expected output from the atomic fact extraction prompts.

## Example 1: Compound Sentence

**Input Text:**
```
John, who works at Google, lives in NYC.
```

**Expected Output:**
```json
{
  "facts": [
    {
      "subject": "John",
      "predicate": "works at",
      "object": "Google"
    },
    {
      "subject": "John",
      "predicate": "lives in",
      "object": "NYC"
    }
  ]
}
```

**Rationale:**
- Two distinct atomic facts extracted from a compound sentence
- Each fact contains one simple relationship
- Pronoun resolution not needed (subject is explicit)

---

## Example 2: Pronoun Resolution

**Input Text:**
```
Sarah joined the company in 2020. She became CEO in 2023.
```

**Expected Output:**
```json
{
  "facts": [
    {
      "subject": "Sarah",
      "predicate": "joined",
      "object": "the company"
    },
    {
      "subject": "Sarah joined the company",
      "predicate": "occurred in",
      "object": "2020"
    },
    {
      "subject": "Sarah",
      "predicate": "became",
      "object": "CEO"
    },
    {
      "subject": "Sarah became CEO",
      "predicate": "occurred in",
      "object": "2023"
    }
  ]
}
```

**Rationale:**
- "She" is resolved to "Sarah" using context
- Temporal information extracted as separate facts
- Event facts created to capture timing relationships

---

## Example 3: Temporal Sequence

**Input Text:**
```
After the meeting, he went home and prepared dinner.
```

**Expected Output:**
```json
{
  "facts": [
    {
      "subject": "he",
      "predicate": "attended",
      "object": "the meeting"
    },
    {
      "subject": "he",
      "predicate": "went to",
      "object": "home"
    },
    {
      "subject": "he went home",
      "predicate": "occurred after",
      "object": "the meeting"
    },
    {
      "subject": "he",
      "predicate": "prepared",
      "object": "dinner"
    },
    {
      "subject": "he prepared dinner",
      "predicate": "occurred after",
      "object": "he went home"
    }
  ]
}
```

**Rationale:**
- Three actions extracted: attended meeting, went home, prepared dinner
- Temporal ordering preserved through "occurred after" relationships
- Sequential dependencies captured

---

## Example 4: Cause-Effect Relationship

**Input Text:**
```
The company's revenue increased by 20% due to strong product sales.
```

**Expected Output:**
```json
{
  "facts": [
    {
      "subject": "the company's revenue",
      "predicate": "increased by",
      "object": "20%"
    },
    {
      "subject": "product sales",
      "predicate": "was",
      "object": "strong"
    },
    {
      "subject": "revenue increase",
      "predicate": "caused by",
      "object": "strong product sales"
    }
  ]
}
```

**Rationale:**
- Revenue increase extracted with quantitative value
- Product sales quality captured separately
- Causal relationship explicitly represented

---

## Example 5: Multiple Events with Temporal Markers

**Input Text:**
```
Tesla announced a new Model 3 variant priced at $35,000 in Q1 2024.
```

**Expected Output:**
```json
{
  "facts": [
    {
      "subject": "Tesla",
      "predicate": "announced",
      "object": "new Model 3 variant"
    },
    {
      "subject": "new Model 3 variant",
      "predicate": "priced at",
      "object": "$35,000"
    },
    {
      "subject": "Tesla announced new Model 3 variant",
      "predicate": "occurred in",
      "object": "Q1 2024"
    }
  ]
}
```

**Rationale:**
- Announcement event extracted
- Pricing information captured separately
- Temporal marker preserved as a distinct fact

---

## Example 6: Complex Multi-Event Scenario

**Input Text:**
```
The CEO announced a restructuring plan on Monday. The stock price dropped 15% by market close. Investors expressed concern about layoffs.
```

**Expected Output:**
```json
{
  "facts": [
    {
      "subject": "The CEO",
      "predicate": "announced",
      "object": "restructuring plan"
    },
    {
      "subject": "CEO announced restructuring plan",
      "predicate": "occurred on",
      "object": "Monday"
    },
    {
      "subject": "stock price",
      "predicate": "dropped by",
      "object": "15%"
    },
    {
      "subject": "stock price dropped",
      "predicate": "occurred by",
      "object": "market close"
    },
    {
      "subject": "stock price drop",
      "predicate": "occurred after",
      "object": "CEO announced restructuring plan"
    },
    {
      "subject": "investors",
      "predicate": "expressed",
      "object": "concern about layoffs"
    }
  ]
}
```

**Rationale:**
- Three main events: announcement, stock drop, investor reaction
- Temporal relationships inferred from narrative sequence
- Implicit causality captured through temporal ordering

---

## Notes for Prompt Tuning

1. **Pronoun Resolution**: LLM should consistently resolve pronouns to their referents. If context is insufficient, pronouns may be kept but flagged for review.

2. **Temporal Marker Extraction**: Always extract explicit temporal markers ("in 2024", "on Monday") as separate facts using "occurred in/on/at" predicates.

3. **Causal Relationships**: Use "caused by", "resulted from", or "led to" predicates to capture explicit or strongly implied causality.

4. **Event Reification**: When creating temporal or causal relationships, use event descriptions as subjects (e.g., "Sarah became CEO" rather than just "Sarah").

5. **Consistency**: Subject and object names should be consistent across facts in the same extraction round.
