# Sample Atomic Fact Extraction Output

Each example shows the structure expected from the atomic fact extraction prompts. All facts include identifiers, temporal cues, and supporting evidence so temporal agents can reason about them later.

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
      "fact_id": "john_works_at_google",
      "subject": "John",
      "predicate": "works at",
      "object": "Google",
      "supporting_text": "John, who works at Google, lives in NYC.",
      "observed_at": "unknown",
      "source_offset": "sent_1"
    },
    {
      "fact_id": "john_lives_in_nyc",
      "subject": "John",
      "predicate": "lives in",
      "object": "NYC",
      "supporting_text": "John, who works at Google, lives in NYC.",
      "observed_at": "unknown",
      "source_offset": "sent_1"
    }
  ]
}
```

**Highlights:** Pronouns already explicit, so no resolution required. Each fact records the exact clause used as evidence.

---

## Example 2: Preference Reversal with Contradiction Note

**Input Text:**
```
On 2025-05-01 the user said they loved pineapple pizza. On 2025-10-16 they said they no longer like pizza.
```

**Expected Output:**
```json
{
  "facts": [
    {
      "fact_id": "user_loves_pineapple_pizza",
      "subject": "User",
      "predicate": "loves",
      "object": "pineapple pizza",
      "supporting_text": "On 2025-05-01 the user said they loved pineapple pizza.",
      "observed_at": "2025-05-01",
      "source_offset": "sent_1"
    },
    {
      "fact_id": "user_dislikes_pizza",
      "subject": "User",
      "predicate": "dislikes",
      "object": "pizza",
      "supporting_text": "On 2025-10-16 they said they no longer like pizza. Supersedes fact_id=user_loves_pineapple_pizza.",
      "observed_at": "2025-10-16",
      "source_offset": "sent_2"
    }
  ]
}
```

**Highlights:** The newer statement references the prior `fact_id` directly inside `supporting_text`, helping the classifier close the earlier preference.

---

## Example 3: Temporal Sequence with Events

**Input Text:**
```
After the meeting, he went home and prepared dinner.
```

**Expected Output:**
```json
{
  "facts": [
    {
      "fact_id": "he_attended_meeting",
      "subject": "He",
      "predicate": "attended",
      "object": "the meeting",
      "supporting_text": "After the meeting, he went home and prepared dinner.",
      "observed_at": "unknown",
      "source_offset": "sent_1"
    },
    {
      "fact_id": "he_went_home",
      "subject": "He",
      "predicate": "went to",
      "object": "home",
      "supporting_text": "After the meeting, he went home and prepared dinner.",
      "observed_at": "unknown",
      "source_offset": "sent_1"
    },
    {
      "fact_id": "he_went_home_after_meeting",
      "subject": "he went home",
      "predicate": "occurred after",
      "object": "the meeting",
      "supporting_text": "After the meeting, he went home and prepared dinner.",
      "observed_at": "unknown",
      "source_offset": "sent_1"
    },
    {
      "fact_id": "he_prepared_dinner",
      "subject": "He",
      "predicate": "prepared",
      "object": "dinner",
      "supporting_text": "After the meeting, he went home and prepared dinner.",
      "observed_at": "unknown",
      "source_offset": "sent_1"
    },
    {
      "fact_id": "he_prepared_dinner_after_going_home",
      "subject": "he prepared dinner",
      "predicate": "occurred after",
      "object": "he went home",
      "supporting_text": "After the meeting, he went home and prepared dinner.",
      "observed_at": "unknown",
      "source_offset": "sent_1"
    }
  ]
}
```

**Highlights:** Sequencing facts capture ordering without guessing specific timestamps.

---

## Example 4: Future-Dated Effective Statement

**Input Text:**
```
On 2025-11-01 Alicia will become CTO, replacing Omar.
```

**Expected Output:**
```json
{
  "facts": [
    {
      "fact_id": "alicia_will_become_cto",
      "subject": "Alicia",
      "predicate": "will become",
      "object": "CTO",
      "supporting_text": "On 2025-11-01 Alicia will become CTO, replacing Omar. Effective 2025-11-01.",
      "observed_at": "statement_time",
      "source_offset": "sent_1"
    },
    {
      "fact_id": "omar_current_cto_until_2025_11_01",
      "subject": "Omar",
      "predicate": "serves as",
      "object": "CTO",
      "supporting_text": "On 2025-11-01 Alicia will become CTO, replacing Omar.",
      "observed_at": "unknown",
      "source_offset": "sent_1"
    }
  ]
}
```

**Highlights:** The upcoming change is captured with explicit wording about the future activation date so classifiers can open/close intervals correctly.

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
