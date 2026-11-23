# Ethiopian Languages: Selection, Fidel Pedagogy, Data, and Launch Plan

**Research brief · 23 November 2026**
**Scope:** A multi-language extension of the Korean app. The owner said "Ethiopian"; that is a nationality, not a language. Ethiopia has 80+ languages and five federal working languages. This brief evaluates Amharic (`am`), Afaan Oromo (`om`), Tigrinya (`ti`), Somali (`so`), Sidama, Wolaytta, and Gurage as **separate products**, and recommends one launch language plus a second.

**Bottom line:** Ship **Amharic first**, then **Tigrinya**. Do not ship an "Ethiopian" course. Build a **fidel-first hybrid**: a 6-week fidel literacy bootcamp (4-week core + 2-week expansion) plus 150 curated items and 10 scenes, with Latin transliteration as a hideable scaffold, not the primary representation. Use **Azure or Addis AI** for Amharic speech; the current OpenAI `tts-1` + `gpt-4o-transcribe` stack is not viable for Amharic. Treat realtime voice tutoring as **partially feasible only**: latency is fine, accuracy is not, and there is no Amharic pronunciation assessment.

---

## 0. Reality check (read this before the plan)

| Assumption | What the evidence says |
|---|---|
| "Amharic is like Korean but with a different alphabet." | No. Amharic has ~231 core fidel glyphs (plus labialized forms), contrastive gemination that the script does not mark, homophone letters, and a Semitic root-and-pattern verb system. Hangul's 24 letters and compositional blocks do not transfer. |
| "OpenAI/Whisper can transcribe Amharic." | Whisper large-v3 scores **CER 151% / WER 138%** on an Amharic benchmark — it hallucinates [43][44]. A fine-tuned Whisper-small is usable only after training. Azure, Google Chirp, and Addis AI are the production options. |
| "ElevenLabs supports Amharic." | Multilingual v2 and v3 do **not**. v4 lists Amharic, but there is no independent Amharic quality benchmark. ElevenLabs v3 scored **WER 148%** on Amharic TTS in a public benchmark. |
| "There is plenty of open Amharic data." | There is enough **speech** for ASR fine-tuning (WAXAL ~196 h train; Dataset.ET 51.5 h), but almost no **TTS** corpus, and the open **dictionary** is tiny (Kaikki: 2,374 distinct words; English Wiktionary: 2,368 Amharic lemmas; Amharic Wiktionary: 796 articles). |
| "Diaspora parents will pay." | Some will, but the price anchor is low: a community Amharic school in the US charges **$100/student/year**. Consumer apps must sit at roughly **$7–12/month** or **$60–90/year**, and justify it with outcomes (reading fidel, speaking with grandparents), not streaks. |
| "Add Oromo because it has 45M speakers." | Oromo is the largest L1 language, but its diaspora is smaller, ARPU is lower, content/native-review capacity is thinner, and the language is politically sensitive. It is a strong third language or impact/B2B play, not the first consumer launch. |

---

## 1. Language selection

### 1.1 Inventory

| Language | ISO | Speakers (best current estimates) | Script | Where it is spoken | Mutual intelligibility notes |
|---|---|---|---|---|---|
| **Amharic** | `am` / `amh` | **35M L1 (2020) + 25M L2 (2019) ≈ 60M total**; Ethnologue 2026 lists ~39M L1 / ~78M total [2] | Ge'ez/fidel abugida | Ethiopia (federal working language), diaspora | Amharic dialects are mutually intelligible [2]. Not intelligible with Tigrinya or Oromo. |
| **Afaan Oromo** | `om` / `orm` | **45.5M native (2019–2024)**; 41.7M in Ethiopia (33.8% of population); ~0.5M in Kenya [1][3] | Latin **Qubee** since 1991; Shaaldaa and Arabic informally | Oromia, Harar, Dire Dawa, Addis; Kenya; diaspora | A dialect continuum. West Central Oromo (Mecha/Tulama) is the Qubee standard; Borana/Orma are more divergent. Not intelligible with Somali or Amharic. |
| **Tigrinya** | `ti` / `tir` | **9.94M** (Ethiopia ~6.4M + Eritrea ~3.5M; diaspora additional) [4] | Ge'ez/fidel (Tigrinya abugida) | Tigray (Ethiopia), Eritrea, diaspora | Not intelligible with Amharic; shares script and some Ge'ez lexicon. Tigre is a separate language. |
| **Somali** | `so` / `som` | **23.8M** [5] | Latin (since 1972); Arabic and Osmanya informally | Somalia, Somaliland, Ethiopia (Somali Region, 6.7M [1]), Djibouti, Kenya, diaspora | Not intelligible with Oromo. Large, well-resourced diaspora language; not an "Ethiopian language" product. |
| **Sidama** | `sid` | **4.94M** [6] | Latin since 1993 (Ethiopic before) | Sidama Region | Closest to Highland East Cushitic languages; not mutually intelligible with Oromo. |
| **Wolaytta** | `wal` | **2.7M** [7] | Latin in schools; Ethiopic used by adults | Wolaita Zone, South Ethiopia | Omotic; not intelligible with Oromo/Amharic. |
| **Gurage** | multiple codes | **~2.4M** (2.01% of 118.5M) [8] | Ethiopic and Latin depending on variety | Gurage Zone, Central Ethiopia | A **cluster** (Sebat Bet, Sodo, Mesqan, etc.), not one language. Many varieties are not mutually intelligible. |
| Afar | `aa` | ~2.1M (1.74%) [8] | Latin | Afar Region, Djibouti, Eritrea | Cushitic; not a launch candidate. |
| Hadiyya / Gamo | `hdy` / `gmv` | ~2.0M / ~1.7M [8] | Latin | SNNPR/South Ethiopia | Small diaspora; no learning market. |

**Speaker-count caution:** Ethiopian censuses and Ethnologue differ by counting ethnicity, L1, and L2 differently. Use ranges, not a single precise number, in marketing.

### 1.2 Diaspora concentration (the paying market)

| Country | Ethiopian-born / diaspora estimate | Notes |
|---|---|---|
| **United States** | **~460,000** including descendants; **283,075 foreign-born** (ACS 2019–2023); ~350,000 in the Washington DC metro; ~96,000 in Los Angeles [9][10] | Largest, highest-ARPU market. DC, Minneapolis, Seattle, Dallas, Atlanta, LA. |
| **UAE** | ~200,000 [9] | Gulf labor migration; less family/heritage learning, more adult survival Amharic. |
| **Israel** | ~177,600 (Ethiopian Jews) [9] | Amharic heritage + Hebrew bilingual; strong fidel/religious literacy angle. |
| **United Kingdom** | ~90,000 [9] | London, Birmingham, Manchester. |
| **Canada** | ~44,065 (2016 census) [9] | Toronto, Calgary, Ottawa. |
| **Saudi Arabia** | Large but poorly enumerated | Labor migration; low consumer ARPU. |
| **Germany, Sweden, Norway, Australia** | Smaller (tens of thousands combined) | Tigrinya/Eritrean diaspora is significant in Germany and Sweden. |
| **Total diaspora** | **2.5M+** abroad [11] | Primary consumer market for heritage learning. |

**Language-by-diaspora:** Amharic is dominant in the US/Canada/UK/Israel; Oromo is significant in DC, Minneapolis, Seattle, Toronto, and Australia; Tigrinya is concentrated in DC, Dallas, Seattle, Germany, Sweden, and Israel; Somali is concentrated in Minneapolis, London, Toronto, and the Gulf.

### 1.3 Learning demand, resources, and willingness to pay

| Language | Existing learning resources (Nov 2026) | Demand signals | Willingness to pay | Content cost |
|---|---|---|---|---|
| **Amharic** | **Selam** (22 units / 68 lessons / 242 words; interactive fidel; premium), Learn Amharic For Beginners (template, 3.9★), Learn Amharic Fidel! (no audio, 3.8★), Clozemaster, Memrise, uTalk/50 Languages, FSI free course, YouTube, **28 italki tutors at $5–30/h**, university courses [12][13][14] | Duolingo does **not** list Amharic (checked 23 Nov 2026); Selam states it never has [12][56]. Selam has 160 ratings at 4.8★; italki has 8,256 Amharic reviews; Reddit threads ask "how do I learn as a diaspora?" [12][13][14] | **High** within diaspora: heritage identity, family communication, church, travel. Consumer $7–12/mo; tutoring $5–30/h. | Medium: 231+ glyphs, rich audio, native review; but speech tools exist. |
| **Afaan Oromo** | Very few structured apps; "Learn Afaan Oromo" apps; YouTube; **2 italki tutors**; Oromo-English dictionaries/phrasebooks; no Duolingo [14] | Largest L1 in Ethiopia; strong in-country pride and education policy; diaspora smaller and more dispersed | **Medium-low** in diaspora; low in-country ARPU; B2B/education possible | Medium-low for script (Latin), high for content/native review and speech (fewer tools). |
| **Tigrinya** | **Selam now ships Tigrinya** (10 vocabulary units / 32 lessons); **8 italki tutors**; a few phrasebook apps; no Duolingo [12][13][14] | High-intensity Eritrean/Tigrayan diaspora; identity and church; few alternatives | **High per capita**, smaller total | Low marginal cost after Amharic: same fidel engine; but weakest speech/data. |
| **Somali** | Several apps (Somali with Abzi, Baro Somali), Memrise, **5 italki tutors**, Quran/Somali resources; Latin script [14] | Large diaspora (Minneapolis, London, Toronto), strong oral culture | Medium-high | Low script cost; speech/data better than Tigrinya; but not "Ethiopian" framing. |
| **Sidama / Wolaytta** | Essentially none | In-country pride; NGO/education interest | Very low consumer; grant/B2B only | High relative to revenue; no diaspora. |
| **Gurage** | Essentially none | Strong in-group identity | Low/medium, fragmented | Very high: multiple varieties, no standard. |

**Key competitive fact:** Selam is the only serious Amharic consumer course, and it is still small (242 words/phrases). It has already expanded to Tigrinya. That validates both the Amharic wedge and the Tigrinya second-language path, while leaving room for a deeper, more honest product.

### 1.4 Script differences

| Language | Script | Learner burden | App implication |
|---|---|---|---|
| Amharic | Fidel (abugida), 33 base families × 7 orders ≈ 231 core glyphs + labialized | **High**: 200+ shapes, 7 vowel orders, homophones, unmarked gemination | Needs a real script bootcamp, whole-syllable teaching, audio for every glyph, typing. |
| Tigrinya | Fidel, same 33×7 structure, plus letters Amharic has merged (e.g., ሀ/ሐ/ኀ, ሰ/ሠ, ጸ/ፀ are distinct) | **High**, but transferable from Amharic | Reuse the Amharic fidel engine with a Tigrinya phoneme map and different example words. |
| Oromo | Latin Qubee; digraphs `ch, dh, ny, ph, sh`; doubled vowels/consonants | **Low** for literates; real work is ejectives, implosive `dh`, vowel length, gemination, pitch | No script bootcamp; build a **phonology bootcamp**. |
| Somali | Latin; doubled vowels/consonants; `dh`, `x`, `q`, `c` | Low | No script bootcamp; tone/stress and dialect variation. |
| Sidama / Wolaytta | Latin (Sidama since 1993; Wolaytta Latin in schools) | Low | No script bootcamp. |
| Gurage | Ethiopic/Latin by variety | High + no standard | Do not launch. |

### 1.5 Recommendation and reasoning

**Launch: Amharic.** It has the largest diaspora with the highest ability and willingness to pay, the most existing demand signals, the best speech tooling, and a script that creates a defensible "we teach you to actually read" wedge. Amharic also functions as Ethiopia's lingua franca, so in-country L2 demand is real (25M L2 speakers).

**Second: Tigrinya.** It reuses the fidel bootcamp, has a concentrated and motivated diaspora, has almost no quality competition, and Selam's Tigrinya launch validates demand. The marginal content cost is lower than Oromo because the script engine transfers. The risk is speech/data quality, so launch it as **reading + curated audio + text teacher**, not as a voice-tutoring product.

**Third: Oromo.** The largest L1 population and a strategically important market, but weaker diaspora ARPU, thinner learning-content supply, and political sensitivity. Enter after Amharic/Tigrinya with a Latin-script phonology bootcamp, an in-country/B2B partner, or a grant-funded impact track.

**Do not launch:** Somali under an "Ethiopian" brand (separate product if pursued), Sidama/Wolaytta (no consumer market), Gurage (not one language).

**Decision rule:** If the goal is **revenue**, Amharic → Tigrinya → Oromo. If the goal is **reach/impact in Ethiopia**, Amharic → Oromo → Tigrinya, with donor/B2B funding. Be explicit about which goal the roadmap is optimizing.

---

## 2. Ge'ez/fidel script pedagogy

### 2.1 How the abugida works

Fidel is an **abugida** [60]: each basic glyph is a consonant plus an inherent vowel, and the vowel is changed by modifying the glyph rather than adding a separate letter. Each consonant family has **seven orders**:

| Order | Vowel (learner approximation) | Example with ሰ | Note |
|---|---|---|---|
| 1 | **ä** (ə, "uh") | ሰ | Base/inherent form; dictionaries cite this form. |
| 2 | **u** | ሱ | |
| 3 | **i** | ሲ | |
| 4 | **a** | ሳ | **Not** the same as order 1. English speakers conflate them. |
| 5 | **e** | ሴ | |
| 6 | **ə** (reduced, often silent) | ስ | The "neutral" form used in clusters; e.g., ስም `səm` "name". |
| 7 | **o** | ሶ | |

The 33 consonant families run in the traditional **"hahu" order**: ሀ ለ ሐ መ ሠ ረ ሰ ሸ ቀ በ ተ ቸ ኀ ነ ኘ አ ከ ኸ ወ ዐ ዘ ዠ የ ደ ጀ ገ ጠ ጨ ጰ ጸ ፀ ፈ ፐ. Some charts add a 34th family or count labialized series, giving **231–238** core forms; with labiovelar glyphs such as ኳ (`kʷa`), ጏ (`gʷa`), ቧ (`bʷa`), the practical inventory is **~250+ shapes** [17][18].

### 2.2 Standard teaching order and methods

Ethiopian schooling does not teach the alphabet as an abstract grid. Evidence from the reading-acquisition literature:

- Instruction starts with **the easiest and most frequent fidel**, each introduced with a **common word** containing it [17].
- **Chanting and rhythmic repetition** are widely used to memorise fidel–word associations [17].
- Schools group letters by **visual similarity** (e.g., the "one-legged" ኀ, ነ, ኘ), and teach the vowel orders as shape transformations of a base [17].
- Fidel recognition is initially **less accurate** than Latin letter naming, but **word reading and spelling in Ethiopic are better** in the first three grades — the larger syllable unit helps word-level reading [17].
- Adult self-study guides recommend: learn the **vowels first**, then **one consonant family at a time across all 7 orders**, write each form repeatedly, then build 2-letter words (አዎ `awo` "yes", እኔ `əne` "I", ንብ `nəb` "bee"), then copy dialogues [18].

**Effective method for the app:** whole-syllable recognition, organised by **family × order matrix**, with audio for every cell, writing/tracing, and spaced retrieval. Do **not** teach it as "consonant + vowel assembly" like Hangul. A consonant-first sequence is useful for shape families, but the learner must memorise the **syllable**, not derive it.

**Time expectations (design estimates, not RCTs):**

| Stage | Content | Hours | Check |
|---|---|---|---|
| F1 | 10 high-frequency families × 7 orders (70 glyphs), vowels, audio | 3–5 | Read 40 syllables |
| F2 | Remaining 23 families; visual-similarity groups | 5–8 | Read 150 syllables |
| F3 | Labialized forms, 6th-order reduction, common words | 3–4 | Read 100 words |
| F4 | Typing, real signs/menus, names, numbers | 3–5 | Type your name; read a menu |
| F5 | Fluency + gemination awareness | ongoing | 60–80 syllables/min |

Selam claims most learners "read basic Fidel within 2–3 weeks" at 15–20 min/day [12]. That is a vendor claim. A realistic app promise is **"recognise the core system in 2 weeks; read common words in 4–6 weeks; all 231 forms in ~6 weeks at 20 min/day; fluency in 3 months."** FSI's overall Amharic course is ~1,100 class hours (44 weeks) to professional proficiency, which is a different target [54].

**What learners complain about (qualitative; app reviews/forums, not a controlled study):**

- "Too many lookalike shapes." The visual density is real; shape-family grouping and writing practice help more than isolated flashcard recognition [17][18].
- "The app writes ሰ and ሴ both as 'se'." Transliteration that collapses the seven orders teaches wrong pronunciation; this is a common failure in low-quality fidel apps [12].
- "There's no audio" or "the audio sounds robotic." Fidel cannot be learned from spelling alone; every glyph and example word needs a native recording.
- "I can recognise letters but I can't read words." Recognition ≠ decoding fluency; learners need word-level and real-text practice, not just the chart.
- "I can't type it." Learners who cannot type avoid writing; teach the OS/Keyman keyboard early and provide an on-screen fidel keyboard.

### 2.3 Common confusions

| Confusion | Type | Teaching response |
|---|---|---|
| ሀ / ሃ / ሐ / ሓ / ኀ / ኃ / ኻ | **Homophones** (h/ḥ/ḫ) with different vowel orders | Teach as one sound set for listening; preserve spelling for reading; fold only for search. |
| አ / ኣ / ዐ / ዓ | **Homophones** (glottal/`ʕ`) | Same: one sound, multiple spellings. |
| ጸ / ፀ | **Homophones** (ejective s') | Same. |
| ሰ / ሠ | **Homophones** (s/ś) | Same. |
| ተ / ጠ | **Not homophones**: /t/ vs /tʼ/ | Teach as a **contrast pair** with audio; shapes and transliteration both mislead. |
| ነ / ኘ; በ / ቨ; ደ / ጅ | Visual/ejective neighbours | Contrast drills, handwriting, audio. |
| ሰ / ሴ, ሳ / ሰ | Vowel-order confusion (order 1 vs 4 vs 5) | Never transliterate both as "se"; force the vowel contrast. |

The homophone sets are exactly the ones used in Amharic NLP normalization: ሀ/ሃ/ሐ/ሓ/ኀ/ኃ/ኻ → ሀ; አ/ኣ/ዐ/ዓ → አ; ጸ/ፀ → ጸ; ሰ/ሠ → ሰ [19]. But normalization is **application-dependent**: it helps information retrieval, and **hurts** POS tagging and sentiment because it destroys meaning distinctions (e.g., ድህነት "poverty" vs ድኅነት "salvage") [19]. Use a **search-fold** only; never rewrite display text or training text.

### 2.4 Gemination

Gemination is **contrastive** in Amharic: consonant length distinguishes words (e.g., አለ can be `alä` "he said" or `allä` "there is"). It is **not indicated in normal orthography** [2]. Readers use morphology and context. Some dictionaries/transliterations double the consonant; Haddis Alemayehu experimented with a dot above the letter; Unicode has combining gemination marks (U+135D–U+135F), but they are rare and poorly supported [20][21].

**App implication:** store a lexical gemination flag and a phonetic form for every headword. Do not expect the fidel string alone to determine pronunciation. TTS/ASR and minimal-pair drills need the flag. Display it as a subtle diacritic or in the romanization, not as a correction of the learner's spelling.

### 2.5 Unicode and normalization

| Block | Range | Use |
|---|---|---|
| Ethiopic | **U+1200–U+137F** (384 code points, 358 assigned) | Core fidel, punctuation, numerals |
| Ethiopic Supplement | U+1380–U+139F | Additional letters |
| Ethiopic Extended | U+2D80–U+2DDF | Extended fidel |
| Ethiopic Extended-A | U+AB00–U+AB2F | Extended fidel |
| Ethiopic Extended-B | U+1E7E0–U+1E7FF | Extended fidel |

Sources: Unicode chart [21], block summary [20].

**Pitfalls:**

1. **NFC is not enough.** Ethiopic has essentially no canonical decompositions. NFC will not unify ሀ and ኀ, or ጸ and ፀ — they are distinct code points. Homophone folding must be an explicit map.
2. **Word separator.** Traditional text uses U+1361 ፡; modern text uses ASCII space. Tokenizers must treat both as boundaries. Full stop is U+1362 ።; comma U+1363; question mark U+1367. Normalize punctuation before matching.
3. **Numerals.** Ethiopic numerals U+1369–U+137C coexist with Arabic digits. Normalize to Arabic digits for TTS, prices, and search.
4. **Combining marks.** U+135D–U+135F are rare; font support and input methods vary. Do not require them for display.
5. **Lookalikes/fonts.** Some fonts lack Ethiopic Extended-B; test Noto Sans Ethiopic and Abyssinica SIL on every glyph used. Subset fonts carefully for PWA size.
6. **Romanization is not normalization.** Learners will type `selam`, `sälam`, `səlam`; store a canonical key plus a fuzzy transliteration key.

### 2.6 Comparison to Hangul, and what to reuse

| Dimension | Hangul | Fidel |
|---|---|---|
| Basic units | 24 letters (14 consonants + 10 vowels) | 33 consonant families × 7 orders ≈ 231+ |
| Composition | Jamo assemble into syllable blocks (11,172 possible; ~2,000 used) | Each syllable is a **precomposed glyph**; no productive assembly |
| Design logic | Featural (mouth shape) | Historical/visual; shape families, not phonetics |
| Main difficulty | Codas, liaison, assimilation, spelling-to-sound | Inventory size, vowel orders, homophones, gemination |
| Time to recognition | 3–6 hours (design estimate) | 10–20 hours (design estimate) |
| Time to decode text | 10–20 hours | 25–40 hours (design estimate) |

**What transfers from the Hangul bootcamp:** the 7-day lesson → drill → read-aloud → typing → final check structure; the "read real signs" gate; the SRS scheduling; the audio-first drills; the honesty about recognition vs reading.

**What does not transfer:** jamo composition, batchim rules, liaison. Fidel needs a **glyph-family matrix**, not a composer.

**App abstraction:** introduce a `ScriptSystem` boundary with:
- `script_type` (`abugida` | `alphabet`), `units`, `families`, `orders`
- `glyph_audio`, `example_words`, `confusable_sets`
- `normalizer` (NFC + punctuation + digits) and `search_fold` (homophones)
- `renderer` (font stack, fallback, subset)
- `keyboard` (OS/Keyman/GeezIME) and `typing_drills`
- `decoder_gates` (syllable → word → real-world text)

This lets Amharic and Tigrinya share the fidel engine, while Oromo/Somali use a Latin phonology engine without pretending the scripts are the same.

---

## 3. Linguistic structure for curriculum

### 3.1 Amharic

- **Morphology:** Semitic **root-and-pattern**. Triconsonantal roots map to verb stems (Type A/B/C), with gemination and vowel patterns carrying aspect/voice/causative. Derived stems (passive, causative, reciprocal) are productive [2].
- **Verbs:** prefixes and suffixes mark **person (1/2/3), number (sg/pl), gender (2sg/3sg)**, and aspect (perfect, imperfect, gerund, jussive, imperative). Perfect uses suffixes (`-hu`, `-h/-k`, `-š`, `-ä`, `-äčč`, `-(ə)n`, `-aččəhu`, `-u`); imperfect uses prefixes (`ə-`, `t-`, `y-`, `n-`) plus plural suffixes [2].
- **Object suffixes:** `-ñ` me, `-h` you (m), `-š` you (f), `-w` him, `-at` her, `-n` us, `-aččəhu` you (pl), `-aččäw` them. These stack on the verb and are a major beginner hurdle.
- **Definiteness:** a **suffix**, not a separate word: masculine `-u/-w`, feminine `-wa/-itu`, plural `-u` [2]. Example pattern: ቤት `bet` "house" → ቤቱ `betu` "the house".
- **Case:** accusative `-(ə)n` on definite/possessed/proper objects (differential object marking); postpositions otherwise [2].
- **Word order:** **SOV**, verb final; adjectives before nouns; postpositions.
- **Politeness:** `እርስዎ` `ərswo` "you" (polite/formal), `አንተ` `antä` (m), `አንቺ` `anči` (f), `እናንተ` `ənnantä` (pl). Polite address uses plural/3rd-person agreement; `እርሳቸው` for a respected third person. Titles: `አቶ` Ato (Mr.), `ወ/ሮ` W/ro (Mrs.), `ወ/ሪት` W/rit (Miss); kin terms (`አባ` father, `እማ` mother) for elders.
- **Transliteration:** no universal standard. **BGN/PCGN** is for place names [52]; **ALA-LC** for bibliographic use [53]; Ethiopianist scholarly transcription uses `ä, ə, ḥ, ś, ṣ, t'`. The app should define **one learner romanization** (e.g., simple `e` for order 1, `a` for order 4) and compute it from the lexicon, never let an LLM improvise it.

### 3.2 Afaan Oromo

- **Script:** Qubee Latin, adopted 1991. 26 letters plus digraphs `ch, dh, ny, ph, sh`; long vowels and geminate consonants are written double. `dh` is a retroflex implosive; `c`, `q`, `ph`, `x` are ejectives [3].
- **Morphology:** agglutinative, suffixing. Nouns take **case** (nominative, accusative, genitive, dative, ablative, locative, instrumental), **number** (`-oota`, `-wwan`, `-een`), and **definiteness** (`-(t)icha` m, `-(t)ittii` f) [3].
- **Verbs:** person/number/gender agreement; tense/aspect; passive, causative, reciprocal derivation. The verb is final.
- **Word order:** **SOV**; adjectives before nouns; postpositions.
- **Prosody:** **pitch-accent/tone** system; high tone on the penultimate or final syllable, with complex morpheme-level patterns. Qubee does **not** mark tone, so TTS/ASR need lexical tone information [3].
- **Politeness:** `isin` (you pl./polite), `ati` (you sg.); `obbo` (respected man/elder), `aayyoo` (mother/elder woman) in many communities; kin terms and elder-first greetings. Avoid assuming Amharic-style titles.
- **Curriculum note:** because the script is Latin, the beginner burden is **phonology** (ejectives, implosive `dh`, vowel length, gemination, pitch), not literacy. A "sound gym" transfers better than a "script bootcamp."

### 3.3 Tigrinya

- **Script:** fidel, but Tigrinya keeps consonant distinctions that Amharic has merged — the ሀ/ሐ/ኀ, ሰ/ሠ, and ጸ/ፀ series are not simple homophones — plus ejectives and labialized series. Amharic readers can decode the shapes but will mispronounce the values.
- **Phonology:** pharyngeal `/ħ/` and `/ʕ/` are real phonemes, and Tigrinya also has a velar/uvular ejective fricative; Amharic has lost the pharyngeals. Ejectives are prominent. This is the main pronunciation challenge for Amharic speakers and English speakers.
- **Grammar:** SOV; verb-final; person/gender/number agreement; gerund and compound tenses; definite/indefinite marking; Ge'ez lexical and religious layer. Do not assume Amharic grammar with swapped words.
- **Politeness:** `ንስኻ` (you m), `ንስኺ` (f), `ንስኹም` (pl./polite); `ኣቶ` Ato, `ወ/ሮ` W/ro; elder kin terms.
- **Curriculum note:** reuse the fidel matrix, but re-teach the **consonant values** and pharyngeals. A Tigrinya course that only swaps vocabulary into Amharic audio is malpractice.

### 3.4 The 300–500 highest-value items

Do not build a 5,000-word dictionary first. Build a **core 300 for A1**, expand to 500 by A1+. A defensible composition:

| Bucket | Count | Examples / notes |
|---|---|---|
| Concrete nouns | 120 | family, people, food, body, places, transport, time, weather, clothing, household, work, school, health, religion, animals, nature |
| Verbs | 60 | be, have, go, come, want, need, can, must, know, understand, speak, see, hear, eat, drink, buy, pay, give, take, open, close, wait, help, like, live, work, study, sleep, wake, sit, stand, walk, run, read, write, say, ask, answer, find, lose, bring, send, call, meet, leave, arrive, start, finish, try, remember, forget, think, feel, hurt, cook, clean, wash, wear, drive, ride, cross, enter, exit, stay, return, become, seem |
| Adjectives / adverbs | 40 | good, bad, big, small, hot, cold, new, old, fast, slow, cheap, expensive, near, far, right, left, here, there, now, later, very, a little, more, less, early, late, easy, hard, clean, dirty, happy, sad, tired, hungry, thirsty, beautiful, ugly, quiet, loud, same, different |
| Function words / particles | 50 | and, but, or, because, if, with, without, in, on, under, to, from, at, this, that, who, what, where, when, why, how, not, yes, no, please, thanks, sorry, also, only, again, still, already, maybe, before, after, between, during, until, for, about, like, than, each, every, some, all, none, other, own, very |
| Fixed phrases / repair | 30 | "I don't understand", "repeat please", "speak slowly", "how do you say…?", "what is this?", "I'm learning", "excuse me", "no problem", "one more", "the bill please" |
| Numbers / time / counters | 30 | 1–20, tens, 100, 1,000; today/tomorrow/yesterday; morning/afternoon/evening; hour/day/week/month/year; kilo, liter, piece, cup, plate |
| Cultural / religious terms | 30 | coffee, injera, fasting, holiday, church, mosque, wedding, funeral, elder, neighbour, market, taxi, bajaj, etc. |
| **Total** | **~360** | Add 100–140 scene-specific items to reach 500. |

**Frequency source:** there is no authoritative open Amharic frequency list. Build one from the **WAXAL Amharic transcripts** (1.06M words in train alone [26]) plus CC-licensed news and the app's own scene scripts; lemmatize with HornMorpho or a curated lexicon. Do not trust a raw web count without normalization and native review.

### 3.5 First 20 communicative functions

| # | Function | Example target (Amharic; native review required) | Scene |
|---|---|---|---|
| 1 | Greet by time of day and respond | ሰላም / እንደምን አደሩ | doorway |
| 2 | Introduce self (name, origin) | ስሜ … ነው | café intro |
| 3 | Ask/answer "how are you?" | እንደምን ነህ? / ደህና ነኝ | phone |
| 4 | Exchange contact / spell name | ስልክ ቁጥርህ ስንት ነው? | phone |
| 5 | Count, prices, money | ስንት ነው? | market |
| 6 | Bargain | ትንሽ ቀንስ | market |
| 7 | Order food/drink, state preference | ቡና እፈልጋለሁ | café |
| 8 | Ask for bill / pay | ሂሳቡ ስንት ነው? | restaurant |
| 9 | Take a taxi: destination, price | ታክሲ እፈልጋለሁ | street |
| 10 | Ask directions / understand left-right-straight | በቀኝ / በግራ / ቀጥል | street |
| 11 | Ask "where is…?" | ሆስፒታል የት ነው? | street |
| 12 | Tell time / make appointment | ስንት ሰዓት ነው? | phone |
| 13 | Talk about family (ages, siblings) | ቤተሰቤ … | home |
| 14 | Describe daily routine / work | ስራዬ … | home |
| 15 | Shop for clothes/sizes/colors | ትልቅ / ትንሽ | shop |
| 16 | Pharmacy/health: symptoms, doctor | ራሴ ያቃጥለኛል | clinic |
| 17 | Phone call: ask for someone, wrong number | … አለ? | phone |
| 18 | Request/repair: please, sorry, repeat, slow | እባክህ / ይቅርታ / ደግመህ ተናገር | any |
| 19 | Express likes/dislikes/needs | … እወዳለሁ | café |
| 20 | Say goodbye / leave-taking | ደህና ሁን | doorway |

Add cultural scenes: coffee ceremony, holiday/fasting meal, church/mosque visit, market day, wedding/funeral condolence. These are the moments diaspora learners actually need.

### 3.6 Honorifics, age, and cultural norms

- **Amharic:** default to `እርስዎ` + plural agreement with strangers/elders; `አንተ/አንቺ` only with peers/children. Use titles and kin terms before first names. Greet before business; elders first. Right hand for food/gifts; shoes off in homes/churches; coffee ceremony is a social ritual, not a transaction. Avoid direct refusals; soften with "I'll try" / "maybe."
- **Oromo:** `isin` for polite/plural; `obbo`/`aayyoo` for elders in many areas; greet before asking; Gadaa/eldership remains socially important in many communities. Avoid assuming Amharic honorifics.
- **Tigrinya:** `ንስኹም` polite/plural; `ኣቶ`/`ወ/ሮ`; elder kin terms; Orthodox fasting and church calendar shape hospitality. Eritrean and Tigrayan identities are distinct — do not collapse them.
- **Somali:** `adiga`/`idinka`, `walaal` (brother/sister), `aabbe`/`hooyo`; elder-first greeting; hospitality around tea/coffee. Clan/topic sensitivity applies.

**Product rule:** age and relationship should be **settings**, not a single "formal/informal" toggle. The app should teach "who am I talking to?" before "which pronoun?"

---

## 4. Data and tooling

### 4.1 Corpora

| Resource | Languages | Size / content | License | Production use |
|---|---|---|---|---|
| **WAXAL** (Google, 2026) | 19 African languages incl. **Amharic, Oromo, Tigrinya, Sidama, Wolaytta** | Per-language labelled ASR: Amharic **~196 h train + 12 h test**, Oromo **~199 h + 12 h**, Tigrinya **~195 h + 12 h**; natural/read speech, speaker-disjoint v2 splits [25][26][57] | **CC BY-SA 4.0** | **Yes** for ASR training/eval, with attribution + share-alike; no TTS data for these languages |
| **Dataset.ET** | Amharic, Oromo, Tigrinya, Somali, 80+ | **Amharic 51.5 h** read speech (493 speakers); **Oromo 9.8 h** (74 speakers); 500k+ Amharic / 450k+ Oromo / 200k+ Tigrinya/Somali sentences claimed [27][59] | **CC BY 4.0** per release | **Yes** for ASR/TTS fine-tuning; verify text license per release |
| **FLEURS** | 102 languages incl. Amharic (`am_et`) | ~10–12 h read speech per language | **CC BY 4.0** | Evaluation |
| **FLORES-200** | 200 languages incl. **am, om, ti, so** | **3,001** professionally translated sentences per language [28] | **CC BY-SA 4.0** | MT evaluation only; far too small for curriculum |
| **Common Voice** | Amharic, Oromo, Tigrinya, Somali | Amharic **3.07 h total / 1.94 h validated** (CV27, 56 speakers); Tigrinya **0.11 h / 0.03 h** (CV17); Oromo archive ~528 MB [29][30] | **CC0** | Supplement/eval only; Tigrinya is unusable as a primary corpus |
| **EthioLLM / EthioNLP** | Amharic, Ge'ez, Oromo, Somali, Tigrinya | Multilingual corpora, models, benchmarks; research releases [31][32] | Mixed; check each dataset/model | Research-grade; useful for baselines |
| **Amharic TTS datasets** | Amharic | `hayuLabs/amharic-tts-clean`: 13.6k rows, 129 speakers, 8.8–28.7 s clips, CC BY 4.0; plus smaller TTS sets [58] | **CC BY 4.0** | **Yes** for TTS fine-tuning, with quality filtering |
| **Amharic news/text corpora** | Amharic | Several HF/Mendeley news collections (e.g., `Lab-et/amharic-corpus`, news-classification sets); size varies | Often CC BY 4.0 or unclear [63] | Frequency/LM only; audit license and dedupe against eval |
| **JW300 / CCAligned / WikiMatrix** | am, om, ti, so + many | Parallel text; noisy, dated | Varies (often CC BY-NC / unknown) | Research only; license audit required |
| **MENYO-20k** | **Yoruba–English** | 20k parallel sentences | CC BY-NC 4.0 | **Not Ethiopian.** The premise is a common mix-up; do not plan around it [37] |
| **Lacuna Fund** | African/Asian/Latin American languages | Grants and funded datasets, not one corpus | Varies | Discovery hub, not a drop-in dataset [38] |
| **Masakhane** | African NLP community | Community, models, benchmarks | Varies | Network/benchmarks, not a curriculum corpus |

**Verdict:** speech data is **adequate for ASR fine-tuning** (200 h per language is a real asset), but **TTS data is the bottleneck**. For a polished app, budget to record **1–2 hours of studio audio with 1–2 native voices** for the 500 core items and fidel examples. That is cheaper and more controllable than chasing open TTS corpora.

### 4.2 Dictionaries and lexicons

| Resource | Coverage | License | Quality / use |
|---|---|---|---|
| **English Wiktionary / Kaikki** | Amharic **2,368 lemmas**; Oromo **1,241**; Tigrinya **879** [22][23][24] | **CC BY-SA** (Wiktionary) | Tiny, inconsistent, but usable as a seed with attribution. Kaikki extraction: **2,374 distinct Amharic words** (2026-10-30) [22]. |
| **Amharic Wiktionary** | **796 articles** [23] | CC BY-SA | Too small to be a primary source. |
| **admas-net/dictionaries** | Amharic/Tigrinya/Oromo | **CC0 1.0** [36] | Best permissive seed; inspect coverage and quality before shipping. |
| **Tigrinya BiLexicon (GeezLab)** | Tigrinya–English word pairs | **MIT** [35] | Author states it is "highly crude" with "numerous inaccuracies" and **cannot serve as a reference dictionary**. Research/seed only. |
| **Abyssinica Dictionary** | Amharic, Oromiffa, Tigrinya, Ge'ez, multi-language | Proprietary/free web | Good lookup UX; **do not scrape** without permission. |
| **ADLIS (University of Gondar)** | Amharic dictionary with morphology/TTS | Open-source claim | Domain was unreachable at time of writing; verify before depending on it. |
| **SelamSoft / AmharicDictionary.com** | Amharic–English | Proprietary/free web | Lookup/reference; license unclear. |
| **Kane, Leslau, Amsalu Aklilu dictionaries** | Amharic/Tigrinya | Copyright | Excellent quality; **not open**. Use for native review, not redistribution. |

**Practical plan:** seed with **CC0 admas-net + CC BY-SA Wiktionary/Kaikki**, then have a native lexicographer build a **2,000-entry curated core** with fidel, romanization, POS, gloss, audio, example, frequency rank, gemination flag, and dialect note. That curated set is the product asset; the open data is scaffolding.

**Oromo-specific:** open coverage is the thinnest of the three. `admas-net` and 1,241 Wiktionary lemmas are the main open seeds; the widely used 4,000-entry Oromo–English/English–Oromo dictionary and phrasebook is copyrighted [62], as are the standard academic dictionaries. Budget native lexicon work.

### 4.3 Morphology, tokenization, normalization

| Tool | Languages | License | Status |
|---|---|---|---|
| **HornMorpho** (Gasser) | Amharic, Oromo, Tigrinya | **GPL-3.0** [33] | Real, maintained (updated 2026), research-grade; Python. GPL is a constraint for a closed app — run as a separate service or legal-review. |
| **amseg** | Amharic | **MIT** [34] | Segmentation, normalization, transliteration/romanization; production-usable preprocessing. |
| **Tigrinya BiLexicon** | Tigrinya | MIT [35] | Statistical lexicon, not a morphology engine. |
| **HornMorpho / UD lemmatizer** | Amharic | Varies | Lemmatization for frequency lists; validate against a curated lexicon. |
| **LISU** | — | — | **Could not verify a public Ethiopian-language tool named LISU** (Nov 2026). Do not plan around it. |
| **Awahi** | — | — | **Could not verify a public Amharic NLP tool named Awahi** (Nov 2026). Treat as a false lead. |

**Spell checking:** no mature open-source Amharic/Oromo/Tigrinya spell checker was found. **Abyssinica Spelling** is a commercial Word add-in [61]. Build a lexicon + edit-distance + homophone-fold checker; present **suggestions**, never silent autocorrect, because homophone substitution changes meaning [19].

**Tokenization:** there is no standard subword tokenizer for these languages. Train SentencePiece on normalized text, validate segmentation against `amseg`/HornMorpho, and remember fidel is 3 bytes per glyph in UTF-8, so token/character budgets differ from Korean.

**LLM coverage:** EthioLLM provides open models/corpora for Amharic, Ge'ez, Oromo, Somali, and Tigrinya [31]. Commercial LLMs can translate Amharic but hallucinate lexicon, gender, and verb forms; constrain generation to DB item IDs and native-reviewed templates. Do not use an LLM as a dictionary.

**Normalization pipeline:** Unicode NFC → unify punctuation (U+1361/U+1362 → space/.) → Arabic digits → collapse whitespace → optional homophone **search fold** (never display fold). For Oromo: NFKC, lowercase, preserve apostrophes (`ʼ` marks glottal stop), keep doubled vowels/consonants.

### 4.4 Keyboards, fonts, transliteration

| Item | Options | License / notes |
|---|---|---|
| **Keyboard/IME** | iOS/Android system Amharic keyboard; **Keyman** Amharic keyboard; **GeezIME** (Windows/macOS); **Abyssinica** keyboard/transliteration | Keyman keyboard is CC BY 2.0 [51]; GeezIME/Abyssinica are proprietary/freeware — check redistribution. |
| **Fonts** | **Noto Sans Ethiopic** (566 glyphs, 505 characters, 4 Unicode blocks); **Abyssinica SIL** | Both **OFL 1.1**; safe to embed [49][50]. Test Ethiopic Extended-B coverage. |
| **Transliteration** | **BGN/PCGN** (place names), **ALA-LC** (bibliographic), Ethiopianist scholarly | BGN/PCGN PDF [52], ALA-LC PDF [53]. Pick one learner scheme and compute it; do not mix. |
| **Transliteration tool** | `amseg` romanization | MIT; validate output against the chosen scheme [34]. |

**Desktop reality:** many diaspora learners use phones; mobile OS keyboards already support Amharic. Desktop web users may not have an Ethiopic keyboard, so provide an **on-screen fidel keyboard** and a **Latin transliteration input** that converts to fidel (with a preview). Teach typing early — learners who cannot type avoid writing.

### 4.5 Licensing constraints (summary)

| Source | Constraint | Mitigation |
|---|---|---|
| WAXAL | CC BY-SA 4.0 | Attribute; derivative datasets share-alike; keep model training records; legal review on weights. |
| Dataset.ET | CC BY 4.0 | Attribute; check per-release text license. |
| Wiktionary/Kaikki | CC BY-SA | Attribute; share-alike on derived dictionary content; keep a credits page. |
| admas-net | CC0 | No attribution required, but keep provenance. |
| HornMorpho | GPL-3.0 | Isolate as a service or avoid in the shipped binary; legal review. |
| Tigrinya BiLexicon | MIT | Attribute; quality-gate. |
| Noto/Abyssinica fonts | OFL 1.1 | Embed; keep license text. |
| Keyman | CC BY 2.0 | Attribute. |
| Vendor APIs (Azure/Google/Addis) | Terms of service; audio retention/training rights | Read terms; store only what you need; prefer vendors that do not train on your audio. |
| Native recordings | Work-for-hire/consent | Written release for voice + likeness; pay fair rates. |

### 4.6 Production-usable vs research-grade

| Capability | Production-usable now | Research-grade / pilot only |
|---|---|---|
| Amharic ASR | Azure `am-ET`, Google Chirp 3 `am-ET` (Preview), **Addis Scribe** | Open Ethio-ASR, WAXAL fine-tunes, Whisper fine-tunes |
| Amharic TTS | **Azure Ameha/Mekdes**, **Gemini TTS**, **Addis Voices 2** | Meta MMS, open VITS fine-tunes |
| Oromo ASR | **Addis Scribe**; Google Chirp 2 `om-ET` (batch/streaming) | Ethio-ASR, WAXAL Whisper/MMS |
| Oromo TTS | **Addis Voices 2** | Meta MMS |
| Tigrinya ASR/TTS | **Addis only (vendor-claimed, unbenchmarked)** | Meta MMS |
| Morphology | amseg (normalization) | HornMorpho (GPL), academic analyzers |
| Dictionary | Curated 2k core + CC0 admas | Wiktionary/Kaikki, Tigrinya BiLexicon |
| Realtime voice tutoring | **No** at Korean quality | Constrained pilots only |

---

## 5. Speech and AI coverage

### 5.1 Provider matrix

| Provider | Amharic | Oromo | Tigrinya | Realtime | Notes |
|---|---|---|---|---|---|
| **Azure Speech** | STT `am-ET` real-time + batch; TTS **2 voices** (`am-ET-AmehaNeural`, `am-ET-MekdesNeural`); **no pronunciation assessment** | ❌ | ❌ | STT real-time ✅ | Stable, cheap, but TTS sounds robotic (naturalness 2.54/5) and only 2 voices [41][45]. |
| **Google Cloud** | Chirp 3 `am-ET` **Preview**, streaming [46]; Gemini TTS supports Amharic; **no Amharic voice listed in Cloud TTS** | Chirp 2 `om-ET` batch/streaming | ❌ | Chirp 3 streaming ✅, but 6.67 s first words in an independent test [39] | Good accuracy, poor interactivity for Amharic streaming. |
| **Addis AI** | STT + TTS + realtime; **best measured Amharic/Oromo** | ✅ | ✅ (claimed) | Addis Live beta (Amharic); streaming STT for 7 languages | Startup risk; vendor benchmarks; 30–43 ms final text [39][40][42]. |
| **OpenAI** | Whisper large-v3 **unusable** (CER 151%); `gpt-4o-transcribe` unbenchmarked for Amharic; `gpt-4o-mini-tts` **bad** (TTS WER 31%, naturalness 1.2/5); `tts-1` is undocumented for Amharic | Unverified | Unverified | Realtime API unbenchmarked | Do not build Amharic speech on OpenAI today [41][43][55]. |
| **ElevenLabs** | v2/v3 **no Amharic**; v4 lists Amharic but no independent benchmark; v3 TTS **WER 148%** | ❌ | ❌ | ❌ | Not for MVP [41][47]. |
| **Meta MMS** | ASR + TTS checkpoints exist | ASR + TTS checkpoints exist | ASR + TTS checkpoints exist | ❌ | Research-grade; TTS WER 22.9%, naturalness 3.09 [41][48]. |
| **Coqui / XTTS** | ❌ (XTTS v2 16 languages, no Amharic) | ❌ | ❌ | ❌ | Framework can train VITS if you have TTS data; no ready voice. |

### 5.2 Measured quality (what the numbers actually say)

**Amharic ASR — WAXAL natural speech, 100 clips (lower is better):**

| System | Mode | WER | CER |
|---|---|---|---|
| Hohe (wav2vec2-BERT, offline) | batch | **25.4%** | **11.2%** |
| Gemini 4 Argon | batch | 25.6% | 11.6% |
| Gemini Flash | batch | 28.2% | 14.8% |
| **Addis Scribe** | streaming 0.32 s | **28.4%** | **13.1%** |
| Google Chirp 3 | streaming | 32.5% | 16.5% |
| Google Chirp 3 | batch | 29.2% | 13.5% |
| Shook (Whisper medium) | live | 35.0% | 16.6% |

On FLEURS read speech, Addis Scribe is **19.8% WER / 8.2% CER**; Hohe is 20.6%/7.9% [39]. On an independent 1,548-clip read benchmark, the best clean open model is **28.45% WER / 9.46% CER**; adding a 5-gram LM drops WER to **24.83%** [43]. Whisper large-v3 is a **control, not a contender**: CER **151%**, WER **138%** — hallucination [43]. Meta **Seamless M4T v2** lists `amh` as supported but scores **WER 103%** on the same benchmark — listing a language is not capability [43].

**Amharic TTS — 87 prompts, ASR-judge WER/CER + blind listening (1–5):**

| System | CER | WER | Naturalness | Intelligibility | Composite |
|---|---|---|---|---|---|
| Gemini 3.1 Flash TTS | **2.89%** | **11.02%** | 3.90 | 3.96 | 3.84 |
| Azure Ameha | 3.03% | 11.16% | 2.54 | 4.49 | 3.49 |
| Azure Mekdes | 4.15% | 13.01% | — | — | — |
| Addis Voice 2 | 4.44% | 13.87% | **4.01** | **4.80** | **4.25** |
| Meta MMS | 7.86% | 22.89% | 3.09 | 2.84 | 3.03 |
| OpenAI gpt-4o-mini-tts | 18.74% | 31.34% | 1.20 | 3.47 | 2.55 |
| ElevenLabs v3 | 111.65% | 147.86% | 1.00 | 1.23 | 2.00 |

Source: Addis AI public benchmark, **vendor-run** but reproducible with published clips/transcripts [41]. The ordering is plausible and consistent with user reports: Azure is intelligible but robotic; Gemini/Addis are more natural; OpenAI/ElevenLabs fail.

**Oromo ASR — WAXAL natural speech, 150 clips:**

| System | Mode | WER | CER |
|---|---|---|---|
| **Addis Scribe** | live 1.12 s | **21.1%** | **6.8%** |
| Addis Scribe | upload | 22.3% | 7.6% |
| Ethio-ASR Oromo | offline | 24.8% | 7.1% |
| Whisper-small (WAXAL) | offline | 28.2% | 8.2% |
| MMS-300M | offline | 29.5% | 7.9% |
| Gemini Flash | batch | 29.8% | 9.7% |
| Google Chirp 2 | batch | 34.8% | 9.9% |
| Google Chirp 2 | streaming | 42.4% | 14.2% |

Source: Addis AI benchmark [40]. Oromo is **better than Amharic** on WER in these runs, despite less tooling — likely because the Latin orthography and WAXAL data are cleaner.

**Tigrinya:** **no public, independently reproduced WER** found. WAXAL provides ~195 h train + 12 h test; Common Voice has ~0.1 h; Addis claims STT/TTS. Expect Oromo-like or worse; **pilot 100 clips before making claims**. Do not promise realtime Tigrinya.

**Pronunciation assessment:** Azure Pronunciation Assessment supports **33 locales** and **Amharic is not one of them** [45]. There is no phoneme-level Amharic scorer from Azure, Google, or OpenAI. Any "pronunciation score" for Amharic would be an ASR-derived proxy — useful for word-level intelligibility, not phoneme accuracy.

### 5.3 Realtime feasibility

**Latency is solved; accuracy is not.**

- Addis Scribe: first words **1.56 s**, final text **30 ms** after speech ends (Amharic); Oromo 1.57–2.21 s / 37–43 ms [39][40].
- Google Chirp 3 streaming: **6.67 s** first words, 1,411 ms final — not conversational [39].
- Azure `am-ET`: real-time supported; no public latency/accuracy benchmark for Amharic; likely usable for push-to-talk.

At **25–28% WER on natural speech**, roughly **1 in 4 words is wrong**. On L2/accented speech, it is worse. That is acceptable for **constrained drills with expected answers**, not for free-form conversation or automatic grammar correction.

**Verdict:** Amharic realtime voice tutoring is **partially feasible**:
- ✅ Push-to-talk (3–8 s) + batch/streaming STT + expected-answer matching.
- ✅ Read-aloud fidel/word drills with word-level diff and confidence.
- ✅ Text teacher + pre-generated audio + optional TTS playback.
- ❌ Full-duplex, open-ended AI conversation with reliable correction.
- ❌ Phoneme-level pronunciation scoring.

**Tigrinya:** unbenchmarked; treat as **text + pre-generated audio only** until a 100-clip pilot proves otherwise.

### 5.4 Recommended speech architecture and costs

**Core audio (pre-generated, cached):**
- Generate every fidel example, all 500 core items, and all scene lines with **Azure Ameha + Mekdes** (cheap, intelligible) and **Addis Voice 2** (more natural). A/B test with 10 native listeners; pick one voice per persona.
- Cost is trivial: 500 items × 3 s × 2 voices ≈ 50 min audio. Azure at ~$0.0095/min ≈ **$0.50**; Addis at $0.032/min ≈ **$1.60** [41][42]. Store Opus/MP3 mono; ship offline.
- Do **not** use runtime TTS for core content. It adds latency, cost, and inconsistency.

**Dynamic audio (dictionary lookup, user text):**
- Azure TTS on demand, rate-limited, cached by hash. Fallback to a pre-recorded "sorry, no audio" or a text-only card.
- Never send user text to a vendor that trains on it without consent.

**ASR (push-to-talk):**
- Azure fast transcription or Addis Scribe; 3–8 s clips; language hint `am`.
- Normalize (NFC, punctuation, digits), apply **homophone fold only for matching**, compute Levenshtein against expected answer + accepted variants; threshold at word-level.
- Show "I heard: …" with an edit button; never a bare "wrong."
- Cost: Addis STT $0.022/1k characters; ~1 min speech ≈ 400 chars ≈ **$0.009/min**. Ten minutes/day ≈ **$0.09/day** ≈ **$2.70/month** per active learner — material against a $10 ARPU. Cap free-tier minutes; use batch/offline where possible [42].

**Realtime:** don't ship full-duplex. Ship "hold to speak" with 1.5–3 s response; stream partial text if the vendor supports it; keep a text fallback always visible. Revisit when WER <15% on learner speech and a pronunciation scorer exists.

---

## 6. Market and monetization

### 6.1 Market size

- **Ethiopia:** ~118.5M people (2024); Amharic ~60M total speakers; Oromo ~45.5M; Tigrinya ~10M; Somali ~24M (incl. Somalia) [2][3][4][5][8].
- **Diaspora:** 2.5M+ abroad; US ~460k incl. descendants, 283k foreign-born; DC metro ~350k; LA ~96k; UAE ~200k; Israel ~178k; UK ~90k; Canada ~44k [9][10][11].
- **Heritage segment:** a large share of second-generation diaspora understand some Amharic but cannot read/write fidel. Selam explicitly targets this segment; Reddit threads describe exactly this profile ("I barely understand it too, but I can read it a bit") [12].
- **Illustrative TAM (label as estimate):** 2.5M diaspora → ~500k households with children/heritage learners → 5% paying at $80/year ≈ **$2M/year** consumer serviceable market; add B2B/community schools and in-country L2. This is small enough that **ARPU and retention matter more than user count**.

### 6.2 Competitors and pricing

For the broader competitor framing, see `docs/research/04-competitive-teardown.md`; it predates this analysis and does not cover Selam or the Amharic tutoring market.

| Product | Languages | Model | Price | Weakness / opening |
|---|---|---|---|---|
| **Selam** | Amharic (22 units/68 lessons/242 words), Tigrinya (10 units/32 lessons) | Freemium, premium subscription; native audio; fidel trainer | Price in-app; category $7–15/mo | Small catalog; new; no web; shallow grammar. **Opening:** deeper fidel fluency + more scenes + honest speech. |
| **Learn Amharic For Beginners** | Amharic | Template app, weekly subscription | Weekly auto-renew | No native author; tracking; template content. |
| **Learn Amharic Fidel!** | Amharic | One-off/quiz | Low | **No audio**; collapses vowel orders (ሰ/ሴ both "se"). |
| **Clozemaster** | Amharic + many | Subscription | ~$8–12/mo | Assumes literacy; no speaking; community sentences. |
| **Memrise** | Amharic + many | Freemium/Pro | ~$8–12/mo | Vocabulary, not a course. |
| **uTalk / 50 Languages** | Amharic + many | One-off/phrasebook | ~$10 | Travel phrases; no fidel; no grammar. |
| **italki** | Amharic (28 tutors), Tigrinya (8), Oromo (2), Somali (5) | Marketplace | **$5–30/h** | Human, high quality, but expensive and unscheduled. **Opening:** structured practice between lessons. |
| **FSI / Live Lingua** | Amharic | Free | $0 | Dated, drill-heavy, no mobile UX. |
| **Duolingo** | **No Amharic** | — | — | Absence signals both neglect and opportunity [12][56]. |
| **Community schools** | Amharic | Weekend classes | **$100/student/year** (ECSAC, grades 1–12, Saturdays) [15] | Cheap, social, but limited hours and scaling. **Opening:** supplement, not replacement. |
| **Church academies** | Amharic/Ge'ez | Sunday school + academy | Donation/subsidized | Captive audience; doctrinal content; slow procurement [16]. |

### 6.3 Willingness to pay and the heritage wedge

- **Parents** pay for **outcomes and identity**: "my child can read the Bible/fidel," "can talk to grandma," "knows the coffee ceremony." They are less price-sensitive than adult hobby learners but need proof of progress.
- **Adult heritage learners** pay for **repair**: understand spoken Amharic but can't read/write; embarrassed at family events; want fidel + texting + phone calls. This is the sharpest wedge because the pain is concrete and the alternative (community school) is designed for children.
- **Adult L2 learners** (partners, travelers, aid workers, adopted Ethiopians) pay for **survival + politeness**: market, taxi, greetings, family. Smaller segment, higher churn.
- **Price architecture:** free fidel unit + 20 items; **$9.99/mo or $69/year**; family plan $12.99/mo; B2B $1–3/student/month or $300–1,000/school/year. Anchor against one italki hour ($5–30), not against Duolingo.
- **Do not** charge for "AI chat" until it works; charge for **curated audio, fidel fluency, and scene practice**.

### 6.4 B2B / community angle

- **Weekend/community schools:** ECSAC (US) runs a Saturday Amharic program, grades 1–12, **$100/student/year**, registration closed/limited [15]. Church academies such as **Abune Gorgorios II Academy** (Mahibere Kidusan, EOTC) run religious/secular education for children [16]. These are distribution partners and a validation channel, not a high-ARPU SaaS market.
- **What to sell:** a turnkey fidel + conversation curriculum, printable worksheets, student progress dashboards, and teacher training. Price per school, not per seat, because school budgets are tiny.
- **What not to sell:** a replacement for teachers or religious instruction. Position as "practice between Saturday classes."
- **Pilot:** 2 schools, 1 term, 30–60 students; measure fidel decoding gain vs control; use results for both B2B and consumer marketing.

### 6.5 Positioning

**"Read your family's language."** Not "learn Ethiopian." Not "AI tutor." The promise: in 4 weeks you can read the core fidel; in 6 weeks, common words; in 10 weeks you can handle 10 family/market/taxi scenes; every word has native audio; no fake pronunciation scores.

Against Selam: deeper fidel fluency, more scenes, better speech honesty, web/PWA. Against italki: structured daily practice and memory. Against community school: convenience and individual pacing. Against Duolingo: a language it doesn't teach.

---

## 7. Recommendation and 6-month plan

### 7.1 Decision

| Decision | Recommendation | Why |
|---|---|---|
| Launch language | **Amharic (`am`)** | Largest diaspora + L2 demand, best speech tools, strongest WTP, script wedge, validated by Selam/italki. |
| Second language | **Tigrinya (`ti`)** | Reuses fidel engine, concentrated diaspora, little competition, Selam already validates. |
| Third | **Oromo (`om`)** | Largest L1, Latin script cheap, but lower ARPU/thinner content; enter with B2B/impact. |
| Script approach | **Fidel-first hybrid** | 6-week bootcamp (4 core + 2 expansion) + 150 items; transliteration hideable; audio + typing; no Latin-primary. |
| Speech | **Azure + Addis, pre-generated core; push-to-talk ASR** | Production-usable; OpenAI/ElevenLabs not viable; no pronunciation assessment. |
| Realtime tutoring | **Do not ship** | 25–28% WER, no phoneme scoring; constrained drills only. |
| "Ethiopian" branding | **Do not use** | It is a country, not a language; it erases Oromo/Tigrinya/Somali distinctions. |

### 7.2 MVP scope (Amharic, ~12 weeks of build)

| Component | Scope | Acceptance |
|---|---|---|
| **Fidel bootcamp** | 6 weeks (4 core + 2 expansion), 20 min/day; 33 families × 7 orders; 231 core + ~30 labialized; 100 example words; writing/tracing; typing | Read 80% of 150 common syllables; type your name; read a menu/sign |
| **Core items** | **150 active items** across 10 scenes; 300–500 lexicon entries (150 active + 150–350 recognition/dictionary) | 80% retention at 7 days; 70% at 30 days |
| **Scenes** | Greetings/self-intro, family, café, market, taxi/directions, phone, shop, clinic, home visit, holiday/coffee ceremony | Complete 8/10 scenes; 2-minute recorded roleplay |
| **Dictionary** | **2,000 curated entries** (fidel, romanization, POS, gloss, audio for top 500, example, gemination flag, frequency rank) + fallback lookup; ship 1,000 if the review budget slips | Search handles homophones and punctuation; audio on 100% of core 500 |
| **Audio** | 2 native voices (m/f), studio or high-quality remote; all fidel examples + 500 lexicon headwords + scene lines | Native review sign-off; no TTS for core |
| **Speech drills** | Push-to-talk, 10 scripted drills, expected-answer matching, "I heard…" editable transcript | <2.5 s response; no free-form scoring |
| **Text teacher** | Constrained responses, grammar cards, repair phrases; no open-ended chat | 90% of replies from curated templates/DB |
| **Offline/PWA** | Downloadable audio + fidel pack; review queue offline | Works on a 3G phone; <50 MB initial pack |
| **Analytics** | Fidel decoding accuracy, item retention, scene completion, streak, WTP survey | Dashboard + weekly cohort report |

**Do not build in MVP:** Tigrinya, Oromo, free-form AI conversation, pronunciation scores, social features, user-generated content, a 20k dictionary, a web editor, an Anki importer.

### 7.3 Data source plan with licenses

| Layer | Source | License | Action |
|---|---|---|---|
| ASR training/eval | WAXAL am/om/ti | CC BY-SA 4.0 | Use for fine-tuning/eval; attribute; share-alike on derived data; legal review on weights. |
| ASR/TTS fine-tune | Dataset.ET Amharic 51.5 h, Oromo 9.8 h | CC BY 4.0 | Use; attribute; verify per-release text license. |
| TTS fine-tune | hayuLabs/amharic-tts-clean + recorded studio | CC BY 4.0 + work-for-hire | Filter for noise/domain; record 1–2 h of app-specific script. |
| Dictionary seed | admas-net (CC0), Wiktionary/Kaikki (CC BY-SA) | CC0 / CC BY-SA | Seed then curate 2k; credits page; share-alike on derived dictionary. |
| Morphology | HornMorpho (GPL-3.0) or amseg (MIT) | GPL/MIT | Use amseg in-process; HornMorpho as isolated service or skip. |
| Evaluation | FLEURS (CC BY 4.0), FLORES-200 (CC BY-SA 4.0) | Permissive | Eval only; do not ship sentences. |
| Fonts/input | Noto Sans Ethiopic, Abyssinica SIL, Keyman | OFL/CC BY | Embed with licenses; on-screen keyboard. |
| Speech API | Azure, Google, Addis | Commercial terms | Store audio; check training/retention; provider abstraction. |

**Native review budget:** 1 Amharic linguist/teacher ~10 h/week for 10 weeks (lexicon, fidel examples, scene scripts, audio QA), plus 2 voice talents for ~4 h each. This is the real cost driver, not compute.

### 7.4 Speech strategy (decision)

1. **Pre-generate** all core audio with Azure Ameha/Mekdes and Addis Voice 2; blind-test 20 clips with 10 native speakers; choose per persona.
2. **ASR** via Addis Scribe or Azure fast transcription; push-to-talk; expected-answer matching; confidence threshold; editable transcript.
3. **No pronunciation score.** Use minimal-pair discrimination, self-compare with native audio, and human review. If a score is shown, label it "intelligibility to a speech model," not "pronunciation."
4. **No realtime** until WER <15% on learner speech and a phoneme scorer exists. Offer "text teacher + audio" as the fallback.
5. **Provider abstraction:** `SpeechProvider` interface with `transcribe`, `synthesize`, `stream`, `cost_estimate`; Azure + Addis adapters; cache by hash; kill switch to pre-generated audio.

### 7.5 Six-month risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Speech accuracy too low for speaking features** | High | High | Constrained drills, expected answers, text fallback, no pronunciation claims. |
| **No TTS corpus / robotic voices** | Medium | High | Record 1–2 h studio; Azure/Addis; avoid OpenAI/ElevenLabs. |
| **Native review bottleneck / dialect disputes** | High | Medium | Pick Addis standard; document variants; 1 reviewer + community advisory; pay fairly. |
| **Fidel drop-off (231+ glyphs)** | High | High | 6-week bootcamp, 10–15 new glyphs/day, audio, SRS, typing, real-world gates; measure lesson-10 retention. |
| **Data licensing (CC BY-SA/GPL)** | Medium | Medium | License register; isolate GPL; attribute; legal review before launch. |
| **Small market / low ARPU** | High | High | Family plan, annual prepay, B2B schools, Oromo impact track; keep burn low. |
| **Competitor (Selam) expands faster** | Medium | Medium | Differentiate on fidel fluency, scene depth, speech honesty, web/PWA. |
| **Political sensitivity (Amharic vs Oromo/Tigrinya)** | Medium | High | Language-specific branding; community advisors; no "Ethiopian" erasure; no partisan content. |
| **LLM hallucination in Amharic** | High | High | Constrain to DB IDs; native review; no free-form chat; validate with lexicon. |
| **Font/encoding bugs** | Medium | Medium | Noto/Abyssinica tests; NFC + explicit fold; punctuation/digit normalization; device matrix. |

### 7.6 What to validate with 10 user interviews (before building)

**Recruit:** 4 diaspora parents (DC/Toronto/London) with children 6–14; 3 heritage adults (2nd gen, understand but can't read); 2 adult L2 learners (partner/travel/work); 1 community-school teacher/administrator.

**Ask:**
1. What do you currently use? Why did you stop? (Selam, YouTube, church, tutor, nothing.)
2. What is the concrete moment you want to handle? (grandmother call, market, church, wedding, texting.)
3. Fidel: do you want to read/write, or only speak? What have you tried? What frustrated you?
4. Would you pay $9.99/mo or $69/year? What would make it worth it? What would make it not worth it?
5. Would you pay for your child? Who decides? What outcome do you need to see?
6. Do you prefer a human teacher, an app, or both? What should the app never do?
7. Which dialect/voice sounds "right"? Play 4 samples (Addis, Gondar, Gojjam, Tigrinya) and ask.
8. What device/keyboard do you use? Do you type Amharic? How?
9. How do you feel about religious/cultural content (coffee ceremony, fasting, church)? Include or avoid?
10. Would you join a 4-week pilot? What would make you recommend it to a friend?

**Pass/fail gates:**
- ≥7/10 identify **fidel reading** or **child's fidel** as a top-3 pain.
- ≥5/10 would pay **$8+/mo** or **$60+/year** (or a family plan).
- ≥6/10 prefer **app + human/community** over app alone.
- ≥7/10 rate at least one voice sample **4/5** on naturalness.
- ≥5/10 say current alternatives are **insufficient**.
- If <4/10 would pay, pivot to **B2B/schools** or **Oromo impact/grant** before building consumer.

### 7.7 Six-month milestones and kill criteria

| Month | Milestone | Gate |
|---|---|---|
| 1 | 10 interviews; fidel prototype (10 families); Azure/Addis voice test; license register | 7/10 pain; 5/10 WTP; voice ≥4/5 |
| 2 | Full fidel bootcamp (33 families); 150-item lexicon; 5 scenes; native reviewer hired | 80% fidel decoding at lesson 10 in 10 testers |
| 3 | 10 scenes; 2,000 dictionary; audio 500 items; push-to-talk drills | 70% item retention at 30 days; <2.5 s ASR |
| 4 | Closed beta (50 users); family plan; B2B pilot with 1 school | 40% week-4 retention; 10% conversion |
| 5 | Public launch (US/Canada/UK); content marketing; church/school partnerships | 500 activated; CAC < $20; NPS > 30 |
| 6 | Decide Tigrinya: reuse engine, record audio, pilot 100 clips | Tigrinya ASR/WER acceptable; 100 waitlist |

**Kill/pivot criteria:** if week-4 retention <25% or conversion <5% after two pricing tests, stop consumer expansion and pivot to B2B school supplement or grant-funded Oromo literacy. Do not add languages to escape a weak first language.

---

## Sources

All URLs accessed **23 November 2026** unless otherwise noted.

1. Wikipedia, *Languages of Ethiopia* — https://en.wikipedia.org/wiki/Languages_of_Ethiopia
2. Wikipedia, *Amharic* — https://en.wikipedia.org/wiki/Amharic
3. Wikipedia, *Oromo language* — https://en.wikipedia.org/wiki/Oromo_language
4. Wikipedia, *Tigrinya language* — https://en.wikipedia.org/wiki/Tigrinya_language
5. Wikipedia, *Somali language* — https://en.wikipedia.org/wiki/Somali_language
6. Wikipedia, *Sidama language* — https://en.wikipedia.org/wiki/Sidama_language
7. Wikipedia, *Wolaytta language* — https://en.wikipedia.org/wiki/Wolaytta_language
8. Translated, *Ethiopia data index* — https://imminent.translated.com/data-index/ethiopia
9. Wikipedia, *Ethiopians* (diaspora table) — https://en.wikipedia.org/wiki/Ethiopians
10. George Mason University IIR, *Ethiopia: Immigrant Stories* (ACS 2019–2023) — https://iir.gmu.edu/immigrant-stories-overview/ethiopia
11. IOM / iDiaspora, *Mapping of Ethiopian Diasporas* — https://www.idiaspora.org/en/learn/resources/research-and-studies/mapping-ethiopian-diasporas-residing-united-states-america
12. Selam, *The Best Apps to Learn Amharic in 2026* (updated Aug 2026) — https://learnwithselam.com/best-amharic-apps
13. Apple App Store, *Selam—Learn Amharic & Tigrinya* (v1.0.12, Nov 2026) — https://apps.apple.com/us/app/selam-learn-and-speak-amharic/id6772249785
14. italki, *Amharic tutors* (28 tutors; $5–30/h; 8,256 reviews) — https://www.italki.com/en/teachers/amharic
15. ECSAC, *2026–2027 Amharic Language Program* ($100/student/year; Saturdays; grades 1–12) — https://www.ecsac.org/amharic-lessons-2025
16. Mahibere Kidusan USA, *Abune Gorgorios II Academy* — https://us.eotcmk.org/node/40
17. ILA, *A Bigger Picture of Early Literacy and Biliteracy Acquisition in Abugidas* (2024) — https://ila.onlinelibrary.wiley.com/doi/full/10.1002/rrq.555
18. University of Wisconsin LCTL, *Practicing the Amharic Alphabet* — https://wisc.pb.unizin.org/lctlresources/chapter/beginning-the-amharic-alphabet/
19. Belay et al., *Impacts of Homophone Normalization on Semantic Models for Amharic* (2021) — https://www.inf.uni-hamburg.de/en/inst/ab/lt/publications/2021-belayetal-ict4da-amharicnorm.pdf
20. Wikipedia, *Ethiopic (Unicode block)* — https://en.wikipedia.org/wiki/Ethiopic_(Unicode_block)
21. Unicode 18.0 chart, *Ethiopic U+1200–U+137F* — https://www.unicode.org/Public/18.0.0/charts/PDF/U1200.pdf
22. Kaikki.org, *Amharic machine-readable dictionary* (extracted 2026-10-30; 2,374 words) — https://kaikki.org/dictionary/Amharic/index.html
23. Wiktionary, *Category:Amharic lemmas* (2,368 pages); Amharic Wiktionary statistics (796 articles) — https://en.wiktionary.org/wiki/Category:Amharic_lemmas ; https://am.wiktionary.org/w/api.php?action=query&meta=siteinfo&siprop=statistics&format=json
24. Wiktionary, *Category:Oromo lemmas* (1,241) and *Category:Tigrinya lemmas* (879) — https://en.wiktionary.org/wiki/Category:Oromo_lemmas ; https://en.wiktionary.org/wiki/Category:Tigrinya_lemmas
25. Google, *WAXAL dataset card* — https://huggingface.co/datasets/google/WaxalNLP
26. WAXAL v2 split metadata (per-language hours) — https://huggingface.co/datasets/google/WaxalNLP/raw/main/data/ASR_v2/metadata/split_comparison.csv
27. Dataset.ET, *Datasets* (Amharic 51.5 h, Oromo 9.8 h, CC BY 4.0) — https://dataset.et/dataset
28. FLORES-200 — https://huggingface.co/datasets/facebook/flores ; https://huggingface.co/datasets/Muennighoff/flores200
29. *Data Quality Issues in Multilingual Speech Datasets* (Common Voice 17 table) — https://arxiv.org/html/2506.17525v1
30. Mozilla Data Collective, *Common Voice 27.0 — Amharic* (3.07 h total, 1.94 h validated) — https://mozilladatacollective.com/datasets/cmu5p8lx400zwmi07jbi3c13l
31. Tonja et al., *EthioLLM* (LREC-COLING 2024) — https://aclanthology.org/2024.lrec-main.561/
32. *Natural Language Processing in Ethiopian Languages* survey + resource list — https://arxiv.org/abs/2303.14406 ; https://github.com/EthioNLP/Ethiopian-Language-Survey
33. HornMorpho (GPL-3.0) — https://github.com/hltdi/HornMorpho
34. amseg (MIT; segmentation, normalization, transliteration) — https://pypi.org/project/amseg/
35. GeezLab, *Tigrinya BiLexicon* (MIT; author warns of inaccuracies) — https://github.com/fgaim/Tigrinya-BiLexicon
36. admas-net, *Amharic/Tigrinya/Oromo Dictionaries* (CC0) — https://github.com/admas-net/dictionaries
37. Adelani et al., *MENYO-20k* (Yoruba–English, not Ethiopian) — https://arxiv.org/abs/2103.08647
38. Lacuna Fund, *Language datasets* — https://lacunafund.org/datasets/language/
39. Addis AI, *Addis Scribe on Amharic* (5 Oct 2026) — https://addisassistant.com/benchmarks/addis-scribe-amharic
40. Addis AI, *Addis Scribe on Afaan Oromo* (27 Oct 2026) — https://addisassistant.com/benchmarks/addis-scribe-oromo
41. Addis AI, *Addis Voice 2 on Amharic* (12 Aug 2026) — https://addisassistant.com/benchmarks/addis-voice-2-amharic
42. Addis AI, *Pricing* — https://addisassistant.com/pricing
43. Dataset.ET, *Amharic ASR Benchmark* (16 models, 1,548 clips, 2026) — https://huggingface.co/datasets/snapwre/amharic-asr-benchmark
44. Gete et al., *Whispering in Amharic: Fine-tuning Whisper for Low-resource Language* (2025) — https://arxiv.org/abs/2503.18485
45. Microsoft, *Azure Speech language and voice support* (Amharic STT/TTS; pronunciation assessment 33 locales) — https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support
46. Google Cloud, *Chirp 3 Transcription* (Amharic `am-ET`, Preview) — https://cloud.google.com/speech-to-text/docs/models/chirp-3
47. ElevenLabs, *Models and supported languages* (v3 vs v4) — https://elevenlabs.io/docs/overview/models
48. Meta, *MMS: Scaling Speech Technology to 1,000+ Languages* — https://arxiv.org/abs/2305.13516
49. Google Fonts, *Noto Sans Ethiopic* (OFL 1.1) — https://fonts.google.com/noto/specimen/Noto+Sans+Ethiopic
50. SIL, *Abyssinica SIL* (OFL) — https://software.sil.org/abyssinica/
51. Keyman, *Amharic Keyboard* (CC BY 2.0) — https://keyman.com/en/keyboards/h/amharic/
52. BGN/PCGN, *Romanization of Amharic* (1967 system) — https://assets.publishing.service.gov.uk/media/634e71ebe90e0731a800892a/ROMANIZATION_OF_AMHARIC_22.pdf
53. Library of Congress, *ALA-LC Romanization: Amharic* — https://www.loc.gov/catdir/cpso/romanization/amharic.pdf
54. *How Long to Learn Amharic? ~1,100 Hours (FSI)* — https://hourstolearnalanguage.com/hours/amharic/
55. Internal: `docs/research/05-tech-and-ai.md` (OpenAI `gpt-4o-transcribe` deprecation Feb 26, 2027; speech pricing) — local file
56. Duolingo, *Courses* (no Amharic listed; checked 23 Nov 2026) — https://www.duolingo.com/courses
57. WAXAL paper — https://huggingface.co/papers/2602.02734
58. Hayu Labs, *Amharic TTS Clean* (13.6k rows, 129 speakers, CC BY 4.0) — https://huggingface.co/datasets/hayuLabs/amharic-tts-clean
59. Dataset.ET, *Amharic Speech v0.2.0* (51.5 h, CC BY 4.0) — https://dataset.et/dataset/amharic-speech-v0-2-0
60. Wikipedia, *Geʽez script* — https://en.wikipedia.org/wiki/Ge%CA%BDez_script
61. EthioCloud, *Abyssinica Spelling — Amharic Spell Checker for Microsoft Word* — https://www.ethiocloud.com/blog/post/abyssinica-spelling-amharic-spell-checker-for-microsoft-word
62. Archive.org, *Oromo–English/English–Oromo Dictionary & Phrasebook* (4,000 entries; copyrighted) — https://archive.org/details/english-oromo
63. Hugging Face, *Lab-et/amharic-corpus* (CC BY 4.0; 100k–1M rows) — https://huggingface.co/datasets/Lab-et/amharic-corpus
