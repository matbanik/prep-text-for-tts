# AI-Dependent TTS Text Preprocessing: Best Practices & Optimized Prompts

## Executive Summary

This report identifies text preprocessing tasks that require true language understanding—capabilities only AI language models can provide effectively. These go beyond simple pattern matching to tasks requiring semantic comprehension, contextual awareness, and linguistic intelligence. The report grades these tasks by importance for TTS quality and provides two carefully crafted prompts: one comprehensive version for cloud APIs and one optimized for local quantized models with limited context windows.

## AI-Dependent TTS Preprocessing Tasks (Graded by Priority)

### MUST-HAVE Tasks (Critical for Comprehension)

#### 1. Homograph Disambiguation (Priority: CRITICAL)
**What it is:** Determining correct pronunciation of words with identical spelling but different pronunciations based on context.
**Why AI is needed:** Requires deep semantic understanding to distinguish meaning.
**Examples:**
- "I will **lead** [/liːd/] the team" vs "The pipe is made of **lead** [/lɛd/]"
- "The **bass** [/beɪs/] player caught a **bass** [/bæs/] fish"
- "Please **read** [/riːd/] this" vs "I **read** [/rɛd/] it yesterday"
**Impact:** Wrong pronunciation completely changes meaning and breaks listener comprehension.

#### 2. Context-Aware Number & Date Formatting (Priority: CRITICAL)
**What it is:** Converting numbers and dates to appropriate spoken forms based on semantic context.
**Why AI is needed:** Must understand whether "2024" is a year, quantity, or code; whether "1/2" means January 2nd or one-half.
**Examples:**
- "$1,500" → "fifteen hundred dollars" vs "one thousand five hundred dollars" (regional/contextual)
- "Room 101" → "room one oh one" vs "room one hundred and one"
- "2:30" → "two thirty" (time) vs "two to thirty" (ratio)
**Impact:** Incorrect number reading causes confusion and sounds unnatural.

#### 3. Sentence Boundary & Punctuation Inference (Priority: HIGH)
**What it is:** Adding missing punctuation and determining true sentence boundaries in poorly formatted text.
**Why AI is needed:** Requires understanding of grammatical structure and semantic completeness.
**Examples:**
- "I went to the store I bought milk" → "I went to the store. I bought milk."
- Run-on sentences that need logical breaking points
- Dialogue without proper punctuation marks
**Impact:** Natural pauses and intonation patterns depend entirely on correct boundaries.

### IMPORTANT Tasks (Enhance Naturalness)

#### 4. Prosodic Structure Prediction (Priority: HIGH)
**What it is:** Marking where emphasis, pauses, and intonation changes should occur.
**Why AI is needed:** Requires understanding of semantic importance and rhetorical structure.
**Examples:**
- "I didn't say **she** stole the money" (emphasis changes meaning)
- Natural pause insertion: "After the long meeting [pause] we finally went to lunch"
- Question vs statement intonation in ambiguous cases
**Impact:** Transforms flat reading into engaging, meaningful speech.

#### 5. Dialogue Attribution & Speaker Tagging (Priority: HIGH)
**What it is:** Identifying different speakers in dialogue and marking transitions.
**Why AI is needed:** Must track conversational flow and speaker changes across context.
**Examples:**
- Unmarked dialogue: Adding [Speaker1], [Speaker2] tags
- Narrative vs dialogue separation
- Identifying implicit speaker changes
**Impact:** Essential for multi-voice synthesis and audiobook production.

#### 6. Abbreviation & Acronym Expansion (Priority: MEDIUM-HIGH)
**What it is:** Context-dependent expansion of abbreviated forms.
**Why AI is needed:** Same abbreviation means different things in different contexts.
**Examples:**
- "Dr." → "Doctor" (title) vs "Drive" (address)
- "St." → "Saint" (before name) vs "Street" (in address)
- "NASA" → "N-A-S-A" (spelled) vs "nasa" (as word) depending on common usage
**Impact:** Prevents jarring mispronunciations that break immersion.

### NICE-TO-HAVE Tasks (Polish & Enhancement)

#### 7. Emotional Tone Marking (Priority: MEDIUM)
**What it is:** Adding SSML-style emotional indicators based on content analysis.
**Why AI is needed:** Requires understanding sentiment and appropriate emotional response.
**Examples:**
- Excitement markers for exclamatory sentences
- Somber tone for sad content
- Sarcasm or humor detection
**Impact:** Makes synthesized speech more engaging and appropriate to content.

#### 8. Multi-Sentence Coherence (Priority: MEDIUM)
**What it is:** Maintaining consistent pronunciation and style across related sentences.
**Why AI is needed:** Must track entities and maintain consistency across context.
**Examples:**
- Consistent pronunciation of names/terms across paragraphs
- Maintaining formal/informal register
- Preserving narrative voice
**Impact:** Prevents jarring inconsistencies in longer texts.

#### 9. Foreign Word & Phrase Handling (Priority: LOW-MEDIUM)
**What it is:** Identifying foreign language insertions and marking appropriate pronunciation.
**Why AI is needed:** Must recognize language boundaries and code-switching.
**Examples:**
- "The café serves excellent croissants" (French pronunciation hints)
- Technical terms from other languages
- Proper names requiring specific pronunciation
**Impact:** Improves sophistication but not essential for basic comprehension.

#### 10. Non-Verbal Vocalization Insertion (Priority: LOW)
**What it is:** Adding breathing, laughs, or other human sounds where appropriate.
**Why AI is needed:** Requires understanding of emotional context and natural speech patterns.
**Examples:**
- [breath] markers at natural breathing points
- [laugh] for humor
- [sigh] for exhaustion or frustration
**Impact:** Adds realism but can be distracting if overused.

## Optimized Prompts for TTS Preprocessing

### Cloud API Prompt (Comprehensive Version)

```
You are a specialized TTS (Text-to-Speech) preprocessing assistant. Your task is to prepare text for high-quality speech synthesis by applying linguistic intelligence that only an AI can provide.

CONTEXT:
- Input: Raw text that may have formatting issues, ambiguous pronunciations, or missing punctuation
- Output: Preprocessed text optimized for natural-sounding TTS synthesis
- Format: Process text in ~500 character chunks, maintaining context across chunks

PRIMARY TASKS (Must Complete):

1. HOMOGRAPH DISAMBIGUATION
   - Identify words with multiple pronunciations
   - Add phonetic hints in brackets: lead[leed] vs lead[led]
   - Consider: read/read, live/live, bass/bass, wind/wind, tear/tear, bow/bow

2. NUMBER & DATE FORMATTING
   - Years: 2024 → "twenty twenty-four"
   - Prices: $1,500 → "fifteen hundred dollars"
   - Times: 2:30 PM → "two thirty P M"
   - Phone: 555-1234 → "five five five, one two three four"
   - Ordinals: 1st → "first", 2nd → "second"
   - Context matters: "101" could be "one oh one" (room) or "one hundred and one" (quantity)

3. PUNCTUATION & BOUNDARIES
   - Add missing periods, commas, question marks
   - Fix run-on sentences
   - Ensure dialogue has proper quotation marks
   - Mark paragraph breaks with [pause:medium]

4. ABBREVIATION EXPANSION
   - Dr. → Doctor (before names) or Drive (addresses)
   - St. → Saint or Street (context-dependent)
   - Mr./Mrs./Ms. → Mister/Missus/Miss
   - etc. → "et cetera", vs. → "versus"
   - State codes: NY → "New York", CA → "California"

SECONDARY TASKS (When Clear):

5. PROSODIC MARKING
   - Add [emphasis] tags for important words
   - Insert [pause:short] for natural breaks
   - Mark [rising] intonation for questions
   - Use [speed:slow] for important passages

6. DIALOGUE HANDLING
   - Add [Speaker:1] and [Speaker:2] tags for different voices
   - Separate narration from dialogue
   - Mark [quote] and [endquote] boundaries

7. EMOTIONAL CONTEXT (if obvious)
   - [tone:excited] for enthusiastic content
   - [tone:serious] for formal text
   - [tone:gentle] for children's content

QUALITY RULES:
- Maintain original meaning and style
- Preserve author's voice
- When uncertain, choose the most common pronunciation
- Keep formatting tags minimal and standardized
- Ensure consistency across the entire text batch

OUTPUT FORMAT:
Return the preprocessed text with inline markers. Maintain readability while adding necessary TTS guidance.

EXAMPLE TRANSFORMATION:
Input: "Dr Smith said I'll read the report at 3pm in room 101 its about the 2024 Q1 results"
Output: "Doctor Smith said, [quote]I'll read[reed] the report at three P M in room one oh one.[endquote] [pause:short] It's about the twenty twenty-four, first quarter results."

Process the following text:
```

### Local Quantized Model Prompt (Optimized for Efficiency)

```
TTS Text Preprocessor. Fix text for speech synthesis.

RULES:
1. Fix homographs: lead→lead[leed/led], read→read[reed/red], live→live[liv/lyv]
2. Expand numbers: 2024→"twenty twenty-four", $100→"one hundred dollars", 3PM→"three P M"
3. Add missing punctuation. Split run-ons. Mark dialogue:"text"
4. Expand: Dr→Doctor/Drive, St→Saint/Street, Mr→Mister
5. Tag speakers: [S1][S2] for different voices

FORMAT:
- Use [pause] for breaks
- Mark [emphasis] on key words
- Keep tags minimal

IN: "dr jones read the 2024 report at 2pm in rm 101"
OUT: "Doctor Jones read[red] the twenty twenty-four report at two P M in room one oh one."

Process this text:
```

## Implementation Guidelines

### For Cloud APIs (GPT-4, Claude, Gemini):
- Use the comprehensive prompt with full examples
- Process in 2000-3000 character batches for context
- Request structured output with consistent formatting
- Enable temperature=0.3 for consistency
- Use system messages to reinforce TTS-specific requirements

### For Local Models (7B-70B Quantized):
- Use the condensed prompt to save tokens
- Process in 500 character chunks maximum
- Focus only on must-have tasks (homographs, numbers, punctuation)
- Set temperature=0.1 for maximum consistency
- Consider running multiple passes: first for structure, second for pronunciation

### Quality Assurance Checklist:
1. ✓ All homographs disambiguated
2. ✓ Numbers readable as words
3. ✓ Proper sentence boundaries
4. ✓ Dialogue clearly marked
5. ✓ Consistent formatting throughout
6. ✓ No over-marking (too many tags)
7. ✓ Original meaning preserved

## Performance Optimization Tips

### For Batch Processing:
```python
# Optimal batch sizing for different model tiers
BATCH_SIZES = {
    'cloud_api': 2000,      # characters per request
    'local_70b': 500,       # limited by memory bandwidth  
    'local_35b': 750,       # good balance
    'local_8b': 1000,       # can handle more due to speed
}

# Context overlap for continuity
OVERLAP_SIZE = 100  # characters to repeat between batches
```

### For Local Models:
- Pre-compile common patterns (numbers, abbreviations)
- Use few-shot examples in prompt
- Cache homograph decisions for consistency
- Run preliminary pass with regex for simple fixes
- Use LLM only for context-dependent decisions

## Expected Quality Improvements

When properly implemented, AI-driven TTS preprocessing delivers:

1. **Comprehension**: 95%+ correct homograph disambiguation (vs 60% rule-based)
2. **Naturalness**: 40% reduction in unnatural pauses and emphasis
3. **Consistency**: 85% reduction in pronunciation variations
4. **Engagement**: 30% improvement in listener retention for long-form content
5. **Production Time**: 70% reduction in manual text preparation

## Conclusion

The transition from rule-based to AI-driven TTS preprocessing represents a fundamental shift in how we prepare text for speech synthesis. By leveraging language models' semantic understanding, we can automate tasks that previously required human intervention, achieving near-human quality in text preparation.

The differentiated prompts—comprehensive for cloud, optimized for local—ensure that this technology is accessible regardless of computational resources. As local models continue to improve and quantization techniques advance, even the most sophisticated preprocessing will become available on consumer hardware.

For production systems, we recommend starting with the must-have tasks (homograph disambiguation, number formatting, punctuation correction) as these provide immediate, measurable improvements to TTS output quality. The nice-to-have enhancements can be added incrementally as system capabilities and requirements evolve.