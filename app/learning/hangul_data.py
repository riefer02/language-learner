"""Hand-authored Hangul curriculum for the seven-lesson bootcamp.

This module is intentionally data-only: plain dicts, lists, and strings.  A
Flask/Jinja route can render it without touching models or the database.

Romanization follows Revised Romanization (RR) where a standard spelling
exists, but the pronunciation cues prioritize the actual sound.  The final
lesson repeats an important caveat: the sound-change rules here are simplified
classroom rules, not a complete phonology of Korean.
"""

# fmt: off
HANGUL_LESSONS = [
    {
        "slug": "letters",
        "day": 1,
        "title": "The shape of Hangul",
        "subtitle": "Consonants, vowels, and how a syllable block is built",
        "goal": (
            "Recognize the 14 basic consonants and 6 basic vowels, and read "
            "your first ten CV blocks."
        ),
        "summary": (
            "Hangul is a featural alphabet written in syllable blocks. Learn "
            "the 14 basic consonants, 6 basic vowels, and the layout of a "
            "simple CV block."
        ),
        "can_do": (
            "I can identify the 14 basic consonants and 6 basic vowels and "
            "read simple blocks such as 가, 나, and 다."
        ),
        "sections": [
            {
                "heading": "A featural alphabet in blocks",
                "body": (
                    "Hangul was created in the 15th century. Several consonant "
                    "shapes hint at the mouth or tongue position: ㄱ, ㄴ, ㅁ, "
                    "ㅅ, and ㅇ are the classic examples. Vowels are built from "
                    "horizontal and vertical strokes plus short marks. The "
                    "letters are not written in a flat line. They are packed "
                    "into syllable blocks. Within a block, the initial "
                    "consonant comes first (left or top), then the vowel "
                    "(right or below), then an optional final consonant at the "
                    "bottom. Korean text then flows left to right and top to "
                    "bottom."
                ),
            },
            {
                "heading": "The 14 basic consonants",
                "body": (
                    "These are the plain consonants. The romanization is a "
                    "guide, not a perfect map: Korean sounds do not line up "
                    "exactly with English. A plain consonant is relaxed, and "
                    "ㄱ ㄷ ㅂ ㅈ become voiced between vowels."
                ),
                "table": {
                    "headers": ["Letter", "Romanization", "Pronunciation cue"],
                    "rows": [
                        ["ㄱ", "g / k", "Between English g and k; voiced between vowels; unreleased [k] at the end."],
                        ["ㄴ", "n", "Like n in no."],
                        ["ㄷ", "d / t", "Between English d and t; voiced between vowels; unreleased [t] at the end."],
                        ["ㄹ", "r / l", "A light tap, between r and l; never the strong English r."],
                        ["ㅁ", "m", "Like m in mom."],
                        ["ㅂ", "b / p", "Between English b and p; voiced between vowels; unreleased [p] at the end."],
                        ["ㅅ", "s", "Like s in see; before i or y it sounds closer to sh."],
                        ["ㅇ", "silent / ng", "Silent at the start of a syllable; ng at the end."],
                        ["ㅈ", "j", "Between English j and ch, but without the puff."],
                        ["ㅊ", "ch", "Like ch in church, with a puff of air."],
                        ["ㅋ", "k", "Like k in kite, with a puff of air."],
                        ["ㅌ", "t", "Like t in top, with a puff of air."],
                        ["ㅍ", "p", "Like p in pie, with a puff of air."],
                        ["ㅎ", "h", "Like h in hi; often weaker between voiced sounds."],
                    ],
                },
            },
            {
                "heading": "The 6 basic vowels",
                "body": (
                    "Korean vowels are pure: hold the sound without gliding "
                    "into another vowel. English speakers often add a glide "
                    "to ㅗ and ㅜ, so keep them short and steady."
                ),
                "table": {
                    "headers": ["Letter", "Romanization", "Pronunciation cue", "Example block"],
                    "rows": [
                        ["ㅏ", "a", "Open a as in father, but shorter.", "가"],
                        ["ㅓ", "eo", "Between the vowel in uh and aw; lips relaxed.", "거"],
                        ["ㅗ", "o", "Round o as in go, but without the glide.", "고"],
                        ["ㅜ", "u", "Like oo in food, but shorter.", "구"],
                        ["ㅡ", "eu", "Like the u in put, with lips spread.", "그"],
                        ["ㅣ", "i", "Like ee in see, but shorter.", "기"],
                    ],
                },
            },
            {
                "heading": "How a syllable block is built",
                "body": (
                    "A block is initial + vowel + optional final. Tall vertical "
                    "vowels (ㅏ ㅓ ㅣ) sit to the right of the consonant. "
                    "Horizontal vowels (ㅗ ㅜ ㅡ) sit below it. A final "
                    "consonant, called batchim, goes at the bottom. Read the "
                    "block as one syllable, not as separate letters."
                ),
                "table": {
                    "headers": ["Block", "Parts", "Why it looks that way"],
                    "rows": [
                        ["가", "ㄱ + ㅏ", "Vertical vowel to the right."],
                        ["고", "ㄱ + ㅗ", "Horizontal vowel below."],
                        ["한", "ㅎ + ㅏ + ㄴ", "Vertical vowel right; batchim below."],
                    ],
                },
            },
            {
                "heading": "Read your first ten blocks",
                "body": (
                    "Say each block aloud. The romanization is a reminder, not "
                    "the goal. 가 is one syllable, not three letters."
                ),
                "table": {
                    "headers": ["Block", "Romanization", "Sound"],
                    "rows": [
                        ["가", "ga", "soft g + a"],
                        ["나", "na", "n + a"],
                        ["다", "da", "soft d + a"],
                        ["라", "ra", "light tap + a"],
                        ["마", "ma", "m + a"],
                        ["바", "ba", "soft b + a"],
                        ["사", "sa", "s + a"],
                        ["아", "a", "silent ㅇ + a"],
                        ["자", "ja", "soft j + a"],
                        ["하", "ha", "h + a"],
                    ],
                },
            },
            {
                "heading": "A realistic first session",
                "body": (
                    "Recognition comes quickly because the system is small and "
                    "regular, but decoding fluency takes practice. Spend a few "
                    "minutes reading blocks aloud, then mix the order. Do not "
                    "worry yet about final consonants or sound changes; those "
                    "are lessons 2 and 3."
                ),
            },
        ],
        "drills": [
            {
                "prompt": "Read this block: 가",
                "options": ["ga", "na", "da", "ma"],
                "answer": "ga",
                "explanation": "ㄱ + ㅏ = 가, pronounced ga.",
            },
            {
                "prompt": "Read this block: 나",
                "options": ["na", "da", "ma", "ra"],
                "answer": "na",
                "explanation": "ㄴ + ㅏ = 나, pronounced na.",
            },
            {
                "prompt": "Read this block: 다",
                "options": ["da", "ta", "na", "ba"],
                "answer": "da",
                "explanation": "ㄷ + ㅏ = 다, pronounced da. ㄷ is a soft d here.",
            },
            {
                "prompt": "Read this block: 라",
                "options": ["ra", "la", "na", "da"],
                "answer": "ra",
                "explanation": "ㄹ + ㅏ = 라. RR writes ㄹ as r at the start of a syllable; the sound is a light tap.",
            },
            {
                "prompt": "Read this block: 마",
                "options": ["ma", "ba", "na", "pa"],
                "answer": "ma",
                "explanation": "ㅁ + ㅏ = 마, pronounced ma.",
            },
            {
                "prompt": "Read this block: 바",
                "options": ["ba", "pa", "ma", "da"],
                "answer": "ba",
                "explanation": "ㅂ + ㅏ = 바, pronounced ba. ㅂ is soft here, not aspirated.",
            },
            {
                "prompt": "Read this block: 사",
                "options": ["sa", "sha", "za", "da"],
                "answer": "sa",
                "explanation": "ㅅ + ㅏ = 사, pronounced sa.",
            },
            {
                "prompt": "Read this block: 아",
                "options": ["a", "ha", "ya", "eo"],
                "answer": "a",
                "explanation": "ㅇ is silent at the start, so ㅇ + ㅏ = 아, pronounced a.",
            },
            {
                "prompt": "Read this block: 자",
                "options": ["ja", "cha", "za", "sa"],
                "answer": "ja",
                "explanation": "ㅈ + ㅏ = 자, pronounced ja.",
            },
            {
                "prompt": "Read this block: 하",
                "options": ["ha", "a", "ka", "da"],
                "answer": "ha",
                "explanation": "ㅎ + ㅏ = 하, pronounced ha.",
            },
        ],
        "notes": [
            "Hangul is written in syllable blocks, but each block is read left to right and top to bottom.",
            "ㅇ is a silent placeholder at the start of a syllable; at the end it is ng.",
            "Romanization is a crutch. Once you know the letters, practice sound-to-letter mapping without it.",
            "Recognition is fast; fluent decoding takes practice. Do not expect to read a newspaper after one lesson.",
        ],
    },
    {
        "slug": "vowels-and-blocks",
        "day": 2,
        "title": "More vowels, tighter consonants",
        "subtitle": "Glides, the ㅐ/ㅔ merger, and the tense/aspirated contrast",
        "goal": (
            "Read blocks with glide and combined vowels, and hear the "
            "difference between plain, tense, and aspirated consonants."
        ),
        "summary": (
            "The remaining vowels are built from the six basics, and consonant "
            "triples (plain/tense/aspirated) change the feel of a block. "
            "Practice 10 mixed blocks and a 40-block grid."
        ),
        "can_do": (
            "I can read blocks with ㅑ, ㅕ, ㅛ, ㅠ, ㅐ, ㅔ, and the w-glides, "
            "and I can tell plain, tense, and aspirated consonants apart."
        ),
        "sections": [
            {
                "heading": "The rest of the vowel inventory",
                "body": (
                    "These vowels are combinations or additions to the six "
                    "basics. Learn them in families: y-glides, e-vowels, and "
                    "w-glides. For most young Seoul speakers ㅐ and ㅔ sound "
                    "the same; do not drill them as a strong contrast. ㅚ is "
                    "also often pronounced like ㅞ today, and ㅙ/ㅞ are merged "
                    "for many speakers. Learn the spelling and let context "
                    "help."
                ),
                "table": {
                    "headers": ["Letter", "Romanization", "Cue", "Example block"],
                    "rows": [
                        ["ㅑ", "ya", "ㅏ with a y glide.", "야"],
                        ["ㅕ", "yeo", "ㅓ with a y glide.", "여"],
                        ["ㅛ", "yo", "ㅗ with a y glide.", "요"],
                        ["ㅠ", "yu", "ㅜ with a y glide.", "유"],
                        ["ㅐ", "ae", "Historically distinct; usually the same as ㅔ in modern Seoul.", "개"],
                        ["ㅔ", "e", "Like e in bed, short; merged with ㅐ for most young speakers.", "게"],
                        ["ㅒ", "yae", "ㅐ with a y glide; rare.", "얘"],
                        ["ㅖ", "ye", "ㅔ with a y glide.", "예"],
                        ["ㅘ", "wa", "ㅗ + ㅏ, said in one syllable.", "과"],
                        ["ㅙ", "wae", "ㅗ + ㅐ; merged with ㅞ for many speakers.", "왜"],
                        ["ㅚ", "oe", "Originally [ø]; most speakers now say it like ㅞ [we].", "회"],
                        ["ㅝ", "wo", "ㅜ + ㅓ.", "워"],
                        ["ㅞ", "we", "ㅜ + ㅔ.", "웨"],
                        ["ㅟ", "wi", "ㅜ + ㅣ.", "위"],
                        ["ㅢ", "ui", "ㅡ + ㅣ; after a consonant it often simplifies to i.", "의"],
                    ],
                },
            },
            {
                "heading": "Plain, tense, and aspirated consonants",
                "body": (
                    "Korean contrasts three kinds of obstruents. Plain "
                    "consonants are relaxed. Tense consonants are made with a "
                    "tighter throat and no puff of air; the pitch often rises. "
                    "Aspirated consonants have a strong puff. English speakers "
                    "often hear plain and tense as the same, so practice the "
                    "contrast slowly. ㅆ is the tense version of ㅅ; ㅅ has no "
                    "aspirated partner."
                ),
                "table": {
                    "headers": ["Plain", "Tense", "Aspirated", "Contrast"],
                    "rows": [
                        ["ㄱ (g/k)", "ㄲ (kk)", "ㅋ (k)", "가 / 까 / 카 — relaxed / tight / puffed"],
                        ["ㄷ (d/t)", "ㄸ (tt)", "ㅌ (t)", "다 / 따 / 타 — relaxed / tight / puffed"],
                        ["ㅂ (b/p)", "ㅃ (pp)", "ㅍ (p)", "바 / 빠 / 파 — relaxed / tight / puffed"],
                        ["ㅈ (j)", "ㅉ (jj)", "ㅊ (ch)", "자 / 짜 / 차 — relaxed / tight / puffed"],
                        ["ㅅ (s)", "ㅆ (ss)", "—", "사 / 싸 — plain / tense"],
                    ],
                },
            },
            {
                "heading": "The 40-block practice grid",
                "body": (
                    "Take five consonants (ㄱ, ㄴ, ㅁ, ㅂ, ㅅ) and eight vowels "
                    "(ㅏ, ㅓ, ㅗ, ㅜ, ㅡ, ㅣ, ㅐ, ㅔ). Combine them into a "
                    "5 × 8 grid and read across, then down, then in random "
                    "order. That is 40 blocks. Do not write romanization under "
                    "every block: say the sound first, then check."
                ),
                "table": {
                    "headers": ["Initial", "ㅏ", "ㅓ", "ㅗ", "ㅜ", "ㅡ", "ㅣ", "ㅐ", "ㅔ"],
                    "rows": [
                        ["ㄱ", "가", "거", "고", "구", "그", "기", "개", "게"],
                        ["ㄴ", "나", "너", "노", "누", "느", "니", "내", "네"],
                        ["ㅁ", "마", "머", "모", "무", "므", "미", "매", "메"],
                        ["ㅂ", "바", "버", "보", "부", "브", "비", "배", "베"],
                        ["ㅅ", "사", "서", "소", "수", "스", "시", "새", "세"],
                    ],
                },
            },
            {
                "heading": "Reading practice: 10 mixed blocks",
                "body": (
                    "These blocks combine what you have learned. Some are "
                    "common words, some are just syllables; read the block, "
                    "not the romanization."
                ),
                "table": {
                    "headers": ["Block", "Romanization", "Note"],
                    "rows": [
                        ["고", "go", "ㄱ + ㅗ"],
                        ["구", "gu", "ㄱ + ㅜ"],
                        ["기", "gi", "ㄱ + ㅣ"],
                        ["과", "gwa", "ㄱ + ㅘ; one syllable, not go-a"],
                        ["귀", "gwi", "ㄱ + ㅟ"],
                        ["냐", "nya", "ㄴ + ㅑ"],
                        ["뎌", "dyeo", "ㄷ + ㅕ"],
                        ["뵤", "byo", "ㅂ + ㅛ"],
                        ["쉬", "swi", "ㅅ + ㅟ"],
                        ["희", "hui", "ㅎ + ㅢ; often heard as 히"],
                    ],
                },
            },
            {
                "heading": "Romanization is a crutch",
                "body": (
                    "RR is useful for names and signs, but it hides "
                    "distinctions: ㅓ and ㅗ both look like o, and ㄱ, ㄲ, ㅋ "
                    "all begin with g or k. Final consonants are not "
                    "released, so romanization often adds a vowel that is not "
                    "there. Use romanization to get started, then drop it. The "
                    "goal is sound-to-letter mapping: see a block and hear it, "
                    "hear a syllable and see it."
                ),
            },
        ],
        "drills": [
            {
                "prompt": "Read this block: 고",
                "options": ["go", "gu", "gi", "gwa"],
                "answer": "go",
                "explanation": "ㄱ + ㅗ = 고, pronounced go.",
            },
            {
                "prompt": "Read this block: 구",
                "options": ["gu", "go", "gi", "geu"],
                "answer": "gu",
                "explanation": "ㄱ + ㅜ = 구, pronounced gu.",
            },
            {
                "prompt": "Read this block: 기",
                "options": ["gi", "go", "gu", "gwi"],
                "answer": "gi",
                "explanation": "ㄱ + ㅣ = 기, pronounced gi.",
            },
            {
                "prompt": "Read this block: 과",
                "options": ["gwa", "goa", "gwo", "ga"],
                "answer": "gwa",
                "explanation": "ㄱ + ㅘ = 과. The ㅘ is one glide, so it is gwa, not go-a.",
            },
            {
                "prompt": "Read this block: 귀",
                "options": ["gwi", "gui", "gi", "gwe"],
                "answer": "gwi",
                "explanation": "ㄱ + ㅟ = 귀, pronounced gwi.",
            },
            {
                "prompt": "Read this block: 냐",
                "options": ["nya", "na", "ya", "neo"],
                "answer": "nya",
                "explanation": "ㄴ + ㅑ = 냐, pronounced nya.",
            },
            {
                "prompt": "Read this block: 뎌",
                "options": ["dyeo", "deo", "tyeo", "dyo"],
                "answer": "dyeo",
                "explanation": "ㄷ + ㅕ = 뎌, pronounced dyeo.",
            },
            {
                "prompt": "Read this block: 뵤",
                "options": ["byo", "bo", "pyo", "byu"],
                "answer": "byo",
                "explanation": "ㅂ + ㅛ = 뵤, pronounced byo.",
            },
            {
                "prompt": "Read this block: 쉬",
                "options": ["swi", "shi", "sui", "swe"],
                "answer": "swi",
                "explanation": "ㅅ + ㅟ = 쉬, pronounced swi. Do not read it as English she.",
            },
            {
                "prompt": "Which is the Revised Romanization of 희?",
                "options": ["hui", "hi", "hwi", "heui"],
                "answer": "hui",
                "explanation": "RR spells 희 as hui; in modern Seoul speech it often sounds like 히 (hi).",
            },
        ],
        "notes": [
            "ㅐ and ㅔ are merged for most young Seoul speakers. Learn the spelling; do not expect a reliable sound difference.",
            "ㅚ is often pronounced like ㅞ, and ㅙ/ㅞ are merged for many speakers.",
            "Tense consonants (ㄲ ㄸ ㅃ ㅆ ㅉ) are not aspirated. The tension is in the throat, not a puff of air.",
            "ㅅ has no aspirated partner; ㅆ is the tense version.",
            "Romanization is a crutch. The goal is to map sound to letter directly.",
            "A 40-block grid is a workout, not a race. Accuracy first, then speed.",
        ],
    },
    {
        "slug": "batchim-sound-changes",
        "day": 3,
        "title": "Batchim and sound changes",
        "subtitle": "Final consonants, seven representative sounds, and why spelling is not the whole story",
        "goal": (
            "Read common batchim words and predict basic liaison, "
            "nasalization, and tensification."
        ),
        "summary": (
            "Batchim is a final consonant. Korean reduces many finals to seven "
            "representative sounds, then resyllabifies and assimilates across "
            "syllable boundaries. These are simplified classroom rules, not a "
            "complete phonology."
        ),
        "can_do": (
            "I can identify the seven representative batchim sounds and "
            "predict common liaison and assimilation changes in short words."
        ),
        "sections": [
            {
                "heading": "What batchim is",
                "body": (
                    "Batchim (받침) is the final consonant in a syllable block. "
                    "It is written at the bottom: 한 = ㅎ + ㅏ + ㄴ. Not every "
                    "syllable has one. When it does, the final consonant is "
                    "often unreleased: the mouth takes the shape but the sound "
                    "stops without a puff. 밥 is close to bap with the lips "
                    "closed at the end, not bap-uh."
                ),
                "table": {
                    "headers": ["Block", "Batchim", "Sound"],
                    "rows": [
                        ["한", "ㄴ", "[n]"],
                        ["밥", "ㅂ", "[p], unreleased"],
                        ["옷", "ㅅ", "[t], unreleased"],
                        ["강", "ㅇ", "[ŋ]"],
                        ["물", "ㄹ", "[l]"],
                    ],
                },
            },
            {
                "heading": "Seven representative final sounds",
                "body": (
                    "Korean has many batchim letters but only seven "
                    "representative final sounds in careful standard "
                    "pronunciation. Different letters can sound the same at "
                    "the end of a syllable. Final ㅎ is usually [t], but it is "
                    "often silent before a vowel (좋아 becomes 조아). Consonant "
                    "clusters such as ㄳ, ㄺ, and ㅄ also reduce to one of these "
                    "sounds; they are beyond this lesson."
                ),
                "table": {
                    "headers": ["Final sound", "Letters", "Example", "Romanization"],
                    "rows": [
                        ["[k]", "ㄱ ㅋ ㄲ", "국", "guk"],
                        ["[n]", "ㄴ", "눈", "nun"],
                        ["[t]", "ㄷ ㅅ ㅆ ㅈ ㅊ ㅌ ㅎ", "옷", "ot"],
                        ["[l]", "ㄹ", "물", "mul"],
                        ["[m]", "ㅁ", "밤", "bam"],
                        ["[p]", "ㅂ ㅍ", "밥", "bap"],
                        ["[ŋ]", "ㅇ", "강", "gang"],
                    ],
                },
            },
            {
                "heading": "Liaison (연음): finals move to the next syllable",
                "body": (
                    "When a syllable ends in a consonant and the next syllable "
                    "begins with ㅇ (a silent placeholder), the final consonant "
                    "moves to the start of the next syllable. The spelling "
                    "stays the same; the sound resyllabifies. This is why "
                    "한국어 does not sound like han-guk-eo with a hard stop in "
                    "the middle."
                ),
                "table": {
                    "headers": ["Written", "Sounds like", "Romanization", "Why"],
                    "rows": [
                        ["한국어", "한구거", "hangugeo", "Final ㄱ moves to 어."],
                        ["옷이", "오시", "osi", "Final ㅅ moves to 이 and sounds like [ɕ]."],
                        ["꽃을", "꼬츨", "kkocheul", "Final ㅊ moves to 을."],
                    ],
                },
            },
            {
                "heading": "Common changes at syllable boundaries",
                "body": (
                    "These are simplified classroom rules. Dialect, speed, and "
                    "individual habit all vary. Learn the common patterns, "
                    "then let listening correct you. 학교 is spelled hakgyo in "
                    "RR, but the second consonant is tense; the table shows "
                    "the actual sound."
                ),
                "table": {
                    "headers": ["Written", "Sounds like", "Romanization", "Pattern"],
                    "rows": [
                        ["한국말", "한궁말", "hangungmal", "ㄱ + ㅁ → ㅇ (nasalization)"],
                        ["신라", "실라", "silla", "ㄴ + ㄹ → ㄹㄹ (lateralization)"],
                        ["같이", "가치", "gachi", "ㅌ + 이 → ㅊ (palatalization)"],
                        ["학교", "학꾜", "hakkyo", "ㄱ + ㄱ → ㄲ (tensification)"],
                        ["좋아", "조아", "joa", "ㅎ disappears between vowels"],
                    ],
                },
            },
            {
                "heading": "A caution about rules",
                "body": (
                    "These are simplified classroom rules, not a complete "
                    "phonology. Real speech varies by dialect, age, and speed. "
                    "Some words have irregular pronunciations that must be "
                    "learned individually. Use the rules as a first guess, "
                    "then check with audio or a native speaker. Do not let the "
                    "rules stop you from speaking."
                ),
            },
            {
                "heading": "How to practice",
                "body": (
                    "Read each word in its written form, then say the "
                    "predicted pronunciation. Cover the sounds-like column and "
                    "test yourself. Then reverse: hear the pronunciation and "
                    "find the written word. Five minutes a day beats one long "
                    "session."
                ),
            },
        ],
        "drills": [
            {
                "prompt": "Read this word: 밥",
                "options": ["bap", "bap-uh", "ba", "ban"],
                "answer": "bap",
                "explanation": "ㅂ as batchim is an unreleased [p]. Close your lips and stop; do not add a vowel.",
            },
            {
                "prompt": "Read this word: 옷",
                "options": ["ot", "os", "o", "on"],
                "answer": "ot",
                "explanation": "Final ㅅ is pronounced [t], so 옷 sounds like ot, not os.",
            },
            {
                "prompt": "Read this word: 물",
                "options": ["mul", "mur", "mu", "mun"],
                "answer": "mul",
                "explanation": "Final ㄹ is [l]; do not roll it like a Spanish r.",
            },
            {
                "prompt": "Read this word: 강",
                "options": ["gang", "gan", "ga", "gam"],
                "answer": "gang",
                "explanation": "Final ㅇ is [ŋ], the ng in sing.",
            },
            {
                "prompt": "Read this word: 꽃",
                "options": ["kkot", "kkoch", "kko", "kkon"],
                "answer": "kkot",
                "explanation": "Final ㅊ is unreleased [t]; the tense ㄲ at the start remains tense.",
            },
            {
                "prompt": "Read this word: 한국어",
                "options": ["hangugeo", "hanguk-eo", "hanguksa", "hangugo"],
                "answer": "hangugeo",
                "explanation": "The final ㄱ of 국 moves to 어: 한구거, hangugeo.",
            },
            {
                "prompt": "Read this word: 옷이",
                "options": ["osi", "oti", "o-i", "ossi"],
                "answer": "osi",
                "explanation": "The final ㅅ moves to 이 and sounds like [ɕ]: 오시, osi.",
            },
            {
                "prompt": "Read this word: 꽃을",
                "options": ["kkocheul", "kkoteul", "kkoche", "kkoseul"],
                "answer": "kkocheul",
                "explanation": "The final ㅊ moves to 을: 꼬츨, kkocheul.",
            },
            {
                "prompt": "Read this word: 한국말",
                "options": ["hangungmal", "hangunmal", "hangukmal", "hanmal"],
                "answer": "hangungmal",
                "explanation": "ㄱ before ㅁ nasalizes to ㅇ: 한궁말, hangungmal.",
            },
            {
                "prompt": "Read this word: 신라",
                "options": ["silla", "sinra", "sinna", "silra"],
                "answer": "silla",
                "explanation": "ㄴ + ㄹ becomes ㄹㄹ: 실라, silla.",
            },
            {
                "prompt": "Read this word: 같이",
                "options": ["gachi", "gati", "gaji", "gach"],
                "answer": "gachi",
                "explanation": "ㅌ before 이 palatalizes to ㅊ: 가치, gachi.",
            },
            {
                "prompt": "In 학교, how is the ㄱ of 교 pronounced?",
                "options": ["tense k", "plain g", "aspirated k", "n"],
                "answer": "tense k",
                "explanation": "The first ㄱ is unreleased [k], and the second tenses to [k͈]: 학꾜, close to hakkyo. RR still writes hakgyo.",
            },
        ],
        "notes": [
            "Batchim is not pronounced with a following vowel. 밥 is not bap-uh.",
            "The seven final sounds are a classroom simplification. Final consonant clusters and some words need individual attention.",
            "Liaison is normal, not sloppy: 한국어 is 한구거.",
            "These rules are simplified. Dialect and fast speech vary; listen and adjust.",
            "Do not try to apply every rule consciously while speaking. Learn a few patterns, then practice with audio.",
        ],
    },
    {
        "slug": "double-batchim",
        "day": 4,
        "title": "Double batchim and clusters",
        "subtitle": "Eleven final clusters, one surviving sound, and the vowel test",
        "goal": (
            "Read common words with double final consonants and predict "
            "whether the first or second consonant is heard."
        ),
        "summary": (
            "A double batchim packs two consonants into the final position. In "
            "isolation or before a consonant, only one of them is pronounced. "
            "Before a vowel, the second consonant often moves to the next "
            "syllable. Learn the eleven clusters through common words rather "
            "than as an abstract list."
        ),
        "can_do": (
            "I can read high-frequency double-final words such as 닭, 삶, 값, "
            "없다, 앉다, and 여덟, and I can explain why 닭 is [닥] but 닭이 is "
            "[달기]."
        ),
        "sections": [
            {
                "heading": "Two consonants, one final sound",
                "body": (
                    "A double batchim (겹받침) is a final cluster of two "
                    "consonants: ㄳ, ㄵ, ㄶ, ㄺ, ㄻ, ㄼ, ㄽ, ㄾ, ㄿ, ㅀ, ㅄ. "
                    "Korean does not pronounce both at the end of a syllable. "
                    "In careful speech one consonant is heard and the other is "
                    "silent. The choice is not random, but it is easier to learn "
                    "one word at a time than to memorize an abstract rule. The "
                    "next section gives the usual pattern, and the section after "
                    "that shows what changes before a vowel."
                ),
            },
            {
                "heading": "The eleven clusters in isolation",
                "body": (
                    "Read the example, then cover the last column. The sound in "
                    "brackets is the actual pronunciation, not a spelling "
                    "pronunciation. ㄳ, ㄽ, ㄾ, and ㄿ are rare in everyday "
                    "words; do not let them slow you down."
                ),
                "table": {
                    "headers": ["Cluster", "Final sound", "Example", "Sounds like"],
                    "rows": [
                        ["ㄳ", "[ㄱ]", "삯", "[삭]"],
                        ["ㄵ", "[ㄴ]", "앉다", "[안따]"],
                        ["ㄶ", "[ㄴ]", "많다", "[만타]"],
                        ["ㄺ", "[ㄱ]", "닭", "[닥]"],
                        ["ㄻ", "[ㅁ]", "삶", "[삼]"],
                        ["ㄼ", "[ㄹ]", "여덟", "[여덜]"],
                        ["ㄽ", "[ㄹ]", "돌솥", "[돌솔]"],
                        ["ㄾ", "[ㄹ]", "핥다", "[할따]"],
                        ["ㄿ", "[ㅂ]", "읊다", "[읍따]"],
                        ["ㅀ", "[ㄹ]", "잃다", "[일타]"],
                        ["ㅄ", "[ㅂ]", "값", "[갑]"],
                    ],
                },
            },
            {
                "heading": "Before a vowel, the second consonant moves",
                "body": (
                    "When the next syllable starts with ㅇ, the final cluster "
                    "splits. The first consonant stays as batchim and the second "
                    "moves to the next syllable. This is why the same word can "
                    "sound different in isolation and in a phrase. The ㅎ in ㄶ "
                    "and ㅀ does not move; it disappears or pushes an aspiration "
                    "onto the next consonant."
                ),
                "table": {
                    "headers": ["Written", "Sounds like", "Why"],
                    "rows": [
                        ["닭이", "[달기]", "ㄹ stays; ㄱ moves to 이."],
                        ["삶을", "[살믈]", "ㄹ stays; ㅁ moves to 을."],
                        ["앉아", "[안자]", "ㄴ stays; ㅈ moves to 아."],
                        ["많아", "[마나]", "ㄴ stays; ㅎ disappears."],
                        ["읽어", "[일거]", "ㄹ stays; ㄱ moves to 어."],
                        ["없어", "[업써]", "ㅂ stays; ㅅ moves and tenses to ㅆ."],
                        ["값이", "[갑씨]", "ㅂ stays; ㅅ moves and tenses to ㅆ."],
                    ],
                },
            },
            {
                "heading": "Ten words to keep",
                "body": (
                    "These ten words are common enough to meet in menus, signs, "
                    "and simple sentences. Read each one aloud before checking "
                    "the middle column."
                ),
                "table": {
                    "headers": ["Word", "Sounds like", "Meaning"],
                    "rows": [
                        ["닭", "[닥]", "chicken"],
                        ["삶", "[삼]", "life"],
                        ["값", "[갑]", "price"],
                        ["없다", "[업따]", "to not exist; to not have"],
                        ["앉다", "[안따]", "to sit"],
                        ["많다", "[만타]", "to be many"],
                        ["젊다", "[점따]", "to be young"],
                        ["읽다", "[익따]", "to read"],
                        ["여덟", "[여덜]", "eight"],
                        ["외곽", "[외곽]", "outskirts (a single ㄱ final, for contrast)"],
                    ],
                },
            },
            {
                "heading": "Two exceptions worth knowing",
                "body": (
                    "The usual pattern for ㄼ is [ㄹ], as in 여덟 [여덜] and "
                    "넓다 [널따]. 밟다 is the common exception: it is [밥따], "
                    "with the ㅂ heard instead. Some speakers also pronounce "
                    "넓다 as [널따] consistently, so trust the word, not the "
                    "cluster. This is the main reason to learn clusters inside "
                    "words."
                ),
            },
        ],
        "drills": [
            {
                "prompt": "Read this word: 닭",
                "options": ["dak", "dal", "dalk", "dang"],
                "answer": "dak",
                "explanation": "ㄺ is [ㄱ] at the end: 닭 sounds like 닥, dak.",
            },
            {
                "prompt": "Read this word: 삶",
                "options": ["sam", "sal", "salm", "sap"],
                "answer": "sam",
                "explanation": "ㄻ is [ㅁ]: 삶 sounds like 삼, sam.",
            },
            {
                "prompt": "Read this word: 값",
                "options": ["gap", "gal", "gaps", "gam"],
                "answer": "gap",
                "explanation": "ㅄ is [ㅂ]: 값 sounds like 갑, gap.",
            },
            {
                "prompt": "How does 없다 sound?",
                "options": ["업따", "업다", "엄따", "없다"],
                "answer": "업따",
                "explanation": "ㅄ is [ㅂ], and the following ㄷ tenses: [업따].",
            },
            {
                "prompt": "How does 앉다 sound?",
                "options": ["안따", "알따", "압따", "안타"],
                "answer": "안따",
                "explanation": "ㄵ is [ㄴ], and the ㄷ of 다 tenses to ㄸ: [안따].",
            },
            {
                "prompt": "How does 많다 sound?",
                "options": ["만타", "만따", "말타", "막타"],
                "answer": "만타",
                "explanation": "ㄶ is [ㄴ], and the ㅎ aspirates the next ㄷ to ㅌ: [만타].",
            },
            {
                "prompt": "How does 젊다 sound?",
                "options": ["점따", "절따", "접따", "점타"],
                "answer": "점따",
                "explanation": "ㄻ is [ㅁ], and the following ㄷ tenses: [점따].",
            },
            {
                "prompt": "How does 읽다 sound?",
                "options": ["익따", "일따", "잉따", "익다"],
                "answer": "익따",
                "explanation": "ㄺ is [ㄱ] before a consonant, and ㄷ tenses: [익따].",
            },
            {
                "prompt": "Read this word: 여덟",
                "options": ["yeodeol", "yeodeop", "yeodeot", "yeodeolp"],
                "answer": "yeodeol",
                "explanation": "ㄼ is usually [ㄹ]: 여덟 sounds like 여덜, yeodeol.",
            },
            {
                "prompt": "How does 읊다 sound?",
                "options": ["읍따", "을따", "엎따", "읍다"],
                "answer": "읍따",
                "explanation": "ㄿ is [ㅂ], and the following ㄷ tenses: [읍따].",
            },
            {
                "prompt": "How does 밟다 sound?",
                "options": ["밥따", "발따", "박따", "밥다"],
                "answer": "밥따",
                "explanation": "밟다 is the common exception to ㄼ = [ㄹ]; it is [밥따].",
            },
            {
                "prompt": "How does 읽어 sound?",
                "options": ["일거", "익어", "일어", "익거"],
                "answer": "일거",
                "explanation": "Before a vowel, ㄹ stays and ㄱ moves: [일거].",
            },
        ],
        "notes": [
            "Do not memorize all eleven clusters at once. Start with 삯, 앉다, 많다, 닭, 삶, 여덟, 값, and 없다; they cover most of what you will meet.",
            "The bracketed sound is the actual pronunciation. The spelling keeps both consonants for history and for the before-a-vowel case.",
            "ㄳ, ㄽ, ㄾ, and ㄿ are rare in daily text. Recognize them, then move on.",
            "Before a vowel, the second consonant often moves: 닭이 [달기], 값이 [갑씨].",
            "ㄼ is usually [ㄹ], but 밟다 is [밥따]. Learn the word, not just the rule.",
        ],
    },
    {
        "slug": "signs-menus-numbers",
        "day": 5,
        "title": "Read real text: signs, menus, numbers",
        "subtitle": "High-frequency public words and the two number systems",
        "goal": (
            "Read common signs and menu items, and choose the right number "
            "system for prices, phone numbers, dates, hours, and counters."
        ),
        "summary": (
            "Public Korean is repetitive, so a small vocabulary unlocks a lot "
            "of text. Sino-Korean numbers handle prices, phone numbers, dates, "
            "and minutes; native Korean numbers handle counters, hours, and "
            "age. Read known nouns and numbers first, then let context fill in "
            "the rest."
        ),
        "can_do": (
            "I can read common signs and menu words such as 출구, 화장실, 커피, "
            "and 영업시간, and I can read a price, a date, and a counter phrase "
            "with the right number system."
        ),
        "sections": [
            {
                "heading": "Start with public text",
                "body": (
                    "Signs and menus repeat the same nouns everywhere. You do "
                    "not need grammar to recognize 출구 or 화장실. Look for the "
                    "noun you know, then use the layout, the picture, and the "
                    "number to guess the rest. These ten words are a good "
                    "starter set for a first trip or a first menu."
                ),
                "table": {
                    "headers": ["Korean", "Meaning", "Where you see it"],
                    "rows": [
                        ["커피", "coffee", "Cafe signs and menus"],
                        ["아메리카노", "Americano", "Cafe menus"],
                        ["주차", "parking", "Parking signs and receipts"],
                        ["출구", "exit", "Subway, station, and building signs"],
                        ["입구", "entrance", "Doors and building signs"],
                        ["화장실", "restroom", "Public signs"],
                        ["영업시간", "business hours", "Doors and shop windows"],
                        ["할인", "discount", "Sale signs and receipts"],
                        ["무료", "free", "Admission and parking signs"],
                        ["매표소", "ticket office", "Stations, cinemas, and museums"],
                    ],
                },
            },
            {
                "heading": "Sino-Korean numbers: 1–10",
                "body": (
                    "Sino-Korean numbers came from Chinese and handle most "
                    "counting of money, dates, minutes, and phone digits. Zero "
                    "is 영 or 공; 공 is common when reading phone numbers aloud. "
                    "Large numbers are built in ten-thousands, so 3,000 is 삼천 "
                    "and 30,000 is 삼만."
                ),
                "table": {
                    "headers": ["Number", "Korean", "Romanization"],
                    "rows": [
                        ["1", "일", "il"],
                        ["2", "이", "i"],
                        ["3", "삼", "sam"],
                        ["4", "사", "sa"],
                        ["5", "오", "o"],
                        ["6", "육", "yuk"],
                        ["7", "칠", "chil"],
                        ["8", "팔", "pal"],
                        ["9", "구", "gu"],
                        ["10", "십", "sip"],
                    ],
                },
            },
            {
                "heading": "Native Korean numbers: 1–10",
                "body": (
                    "Native numbers are used with counters and for hours and "
                    "age. Before a counter, 하나 becomes 한, 둘 becomes 두, 셋 "
                    "becomes 세, and 넷 becomes 네: 한 잔, 두 명, 세 시, 네 살. "
                    "Twenty is 스물 alone but 스무 살 with the age counter."
                ),
                "table": {
                    "headers": ["Number", "Korean", "Romanization"],
                    "rows": [
                        ["1", "하나", "hana"],
                        ["2", "둘", "dul"],
                        ["3", "셋", "set"],
                        ["4", "넷", "net"],
                        ["5", "다섯", "daseot"],
                        ["6", "여섯", "yeoseot"],
                        ["7", "일곱", "ilgop"],
                        ["8", "여덟", "yeodeol"],
                        ["9", "아홉", "ahop"],
                        ["10", "열", "yeol"],
                    ],
                },
            },
            {
                "heading": "Numbers in the wild",
                "body": (
                    "The fastest way to choose a number system is to ask what "
                    "is being counted. Money, dates, and minutes are Sino. "
                    "Objects, people, hours, and age are native. Phone numbers "
                    "are read one digit at a time, with zero as 공."
                ),
                "table": {
                    "headers": ["Written", "Read aloud", "Why"],
                    "rows": [
                        ["3,000원", "삼천 원", "Prices use Sino-Korean; 원 is the currency."],
                        ["02-1234-5678", "공이 일이삼사 오육칠팔", "Phone digits are read one by one; 0 is 공."],
                        ["2026년 10월 19일", "이천이십육 년 시월 십구 일", "Dates use Sino-Korean; 10월 is 시월, 6월 is 유월."],
                        ["오후 세 시", "오후 세 시", "Hours use native numbers; 오후 means p.m."],
                        ["십오 분", "십오 분", "Minutes use Sino-Korean numbers."],
                        ["커피 두 잔", "커피 두 잔", "The counter 잔 takes native numbers; 둘 becomes 두."],
                    ],
                },
            },
            {
                "heading": "Spacing and punctuation",
                "body": (
                    "Korean puts spaces between words, but particles and verb "
                    "endings attach to the word in front: 학교에, 커피를, 먹어요. "
                    "Signs often drop spaces for visual reasons, so 영업시간 "
                    "appears as one block. Modern Korean uses Western "
                    "punctuation: periods, commas, question marks, and quotation "
                    "marks. Numbers and units usually stay together, as in "
                    "3,000원 or 10%. A middle dot (·) often separates items on a "
                    "sign. When spacing looks strange, read known chunks rather "
                    "than individual letters."
                ),
            },
            {
                "heading": "A field strategy for signs",
                "body": (
                    "Read the number first, then the noun. On a menu, prices "
                    "usually sit on the right, and the item name is on the left. "
                    "On a station sign, look for the arrow and the exit number. "
                    "Skip words you do not know; one recognized noun plus the "
                    "context is often enough to act. Carry a translation app for "
                    "the rest, and add the words you meet to your review deck."
                ),
            },
        ],
        "drills": [
            {
                "prompt": "What does this sign mean? 커피",
                "options": ["coffee", "tea", "water", "juice"],
                "answer": "coffee",
                "explanation": "커피 is coffee, one of the most common cafe words.",
            },
            {
                "prompt": "What does this sign mean? 주차",
                "options": ["parking", "entrance", "exit", "ticket office"],
                "answer": "parking",
                "explanation": "주차 means parking; 주차장 is a parking lot.",
            },
            {
                "prompt": "What does this sign mean? 출구",
                "options": ["exit", "entrance", "restroom", "discount"],
                "answer": "exit",
                "explanation": "출구 is an exit; 입구 is an entrance.",
            },
            {
                "prompt": "What does this sign mean? 영업시간",
                "options": ["business hours", "free", "discount", "parking"],
                "answer": "business hours",
                "explanation": "영업 means business or operation; 시간 means time or hours.",
            },
            {
                "prompt": "What does this sign mean? 무료",
                "options": ["free", "discount", "closed", "paid"],
                "answer": "free",
                "explanation": "무료 means free of charge; 유료 means paid.",
            },
            {
                "prompt": "What does this sign mean? 매표소",
                "options": ["ticket office", "restroom", "parking lot", "cafe"],
                "answer": "ticket office",
                "explanation": "표 is a ticket, so 매표소 is the place that sells tickets.",
            },
            {
                "prompt": "What does this menu item mean? 아메리카노",
                "options": ["Americano", "latte", "green tea", "orange juice"],
                "answer": "Americano",
                "explanation": "아메리카노 is a loanword from Americano, a common cafe order.",
            },
            {
                "prompt": "What does this sign mean? 화장실",
                "options": ["restroom", "ticket office", "exit", "business hours"],
                "answer": "restroom",
                "explanation": "화장실 is the restroom or bathroom.",
            },
            {
                "prompt": "How do you read this price? 3,000원",
                "options": ["삼천 원", "삼백 원", "삼만 원", "사천 원"],
                "answer": "삼천 원",
                "explanation": "3,000 is 삼천, and 원 is the currency: sam cheon won.",
            },
            {
                "prompt": "How many cups? 커피 두 잔",
                "options": ["two cups", "three cups", "one cup", "two bottles"],
                "answer": "two cups",
                "explanation": "두 is the counter form of 둘, and 잔 counts cups or glasses.",
            },
            {
                "prompt": "How do you read this year? 2026년",
                "options": ["이천이십육 년", "이천이십오 년", "이천육 년", "이십이육 년"],
                "answer": "이천이십육 년",
                "explanation": "2026 is 이천이십육; 년 means year.",
            },
            {
                "prompt": "What does 10% 할인 mean?",
                "options": ["10% off", "10% free", "10 minutes", "10,000 won"],
                "answer": "10% off",
                "explanation": "할인 means a discount, so 10% 할인 is 10 percent off.",
            },
        ],
        "notes": [
            "Start with high-frequency public text: exits, restrooms, hours, prices, and coffee.",
            "Do not decode every unknown word on a sign. Find the noun and the number first.",
            "Use Sino-Korean for prices, phone numbers, dates, and minutes; use native numbers for counters, hours, and age.",
            "Particles stick to words: 커피를, 학교에. Signs sometimes drop spaces completely.",
            "A menu is a vocabulary list, not a grammar test. Learn five items you will actually order.",
        ],
    },
    {
        "slug": "connected-speech",
        "day": 6,
        "title": "Connected speech: sound changes in context",
        "subtitle": "What happens when the rules meet a real phrase",
        "goal": (
            "Predict the pronunciation of common short phrases by applying "
            "liaison, assimilation, palatalization, aspiration, and "
            "tensification together."
        ),
        "summary": (
            "In isolation, a word follows one rule. In a phrase, several rules "
            "meet at once. The same batchim can sound different depending on "
            "the next syllable. Read phrases as chunks, not as separate "
            "blocks, and treat the rules as a first guess rather than a "
            "complete description of fast speech."
        ),
        "can_do": (
            "I can read short phrases such as 한국어를, 같이 가요, 좋아요, and "
            "없어요, and I can explain which sound change is happening."
        ),
        "sections": [
            {
                "heading": "Rules meet phrases",
                "body": (
                    "Day 3 introduced liaison, nasalization, lateralization, "
                    "palatalization, aspiration, and tensification one at a "
                    "time. Real phrases combine them. In 한국어를, the final ㄱ "
                    "of 국 moves to 어; in 학교에, the ㄱ of 교 tenses; in "
                    "좋아요, the ㅎ disappears. Do not read each block and then "
                    "stitch the sounds together. Read the whole phrase and let "
                    "the changes happen at the boundary."
                ),
            },
            {
                "heading": "Seven patterns to review",
                "body": (
                    "These examples cover the main classroom rules. The "
                    "bracketed form is the actual pronunciation. Notice that "
                    "some rules depend on the next sound, not just the spelling."
                ),
                "table": {
                    "headers": ["Pattern", "Written", "Sounds like", "What happens"],
                    "rows": [
                        ["Liaison", "한국어를", "[한구거를]", "Final ㄱ moves to 어."],
                        ["Nasalization", "국물", "[궁물]", "ㄱ before ㅁ becomes ㅇ."],
                        ["Lateralization", "연락", "[열락]", "ㄴ before ㄹ becomes ㄹ."],
                        ["Palatalization", "같이", "[가치]", "ㅌ before 이 becomes ㅊ."],
                        ["Aspiration", "축하해요", "[추카해요]", "ㄱ plus ㅎ becomes ㅋ."],
                        ["Tensification", "학교에", "[학꾜에]", "ㄱ before ㄱ becomes ㄲ."],
                        ["ㅎ deletion", "좋아요", "[조아요]", "ㅎ disappears between vowels."],
                    ],
                },
            },
            {
                "heading": "The ten phrases",
                "body": (
                    "Read each phrase aloud as one unit. The third column names "
                    "the main change; some phrases also have a smaller change "
                    "inside a word. 전화해요 is included as a control: it sounds "
                    "close to its spelling, which is a useful reminder that not "
                    "every phrase is dramatic."
                ),
                "table": {
                    "headers": ["Written", "Sounds like", "Main change"],
                    "rows": [
                        ["한국어를", "[한구거를]", "Liaison: ㄱ moves to 어."],
                        ["학교에", "[학꾜에]", "Tensification: ㄱ becomes ㄲ."],
                        ["같이 가요", "[가치 가요]", "Palatalization: ㅌ becomes ㅊ."],
                        ["좋아요", "[조아요]", "ㅎ deletion between vowels."],
                        ["먹어요", "[머거요]", "Liaison: ㄱ moves to 어."],
                        ["전화해요", "[전화해요]", "No major change here."],
                        ["괜찮아요", "[괜차나요]", "ㄶ becomes ㄴ and ㅎ disappears."],
                        ["앉아요", "[안자요]", "ㄵ becomes ㄴ; ㅈ moves to 아."],
                        ["읽어요", "[일거요]", "ㄺ becomes ㄹ before a vowel; ㄱ moves."],
                        ["없어요", "[업써요]", "ㅄ becomes ㅂ; ㅅ moves and tenses."],
                    ],
                },
            },
            {
                "heading": "Why the same letter gives different results",
                "body": (
                    "A rule is not a property of a letter; it is a relationship "
                    "between neighboring sounds. ㄺ is [ㄱ] in 닭 but its ㄹ "
                    "survives in 읽어요. The ㅎ in 좋아요 disappears, but the ㅎ "
                    "in 축하해요 turns the preceding ㄱ into ㅋ. This is why "
                    "memorizing a single table is less useful than reading "
                    "whole phrases and listening for the result."
                ),
            },
            {
                "heading": "Practice in phrases, not syllables",
                "body": (
                    "Take one phrase and read it three ways: slowly with clear "
                    "boundaries, at a normal speed, then fast enough to sound "
                    "natural. Record yourself and compare with a native audio "
                    "clip if you have one. Shadowing, repeating immediately "
                    "after the audio, is especially useful for connected "
                    "speech. Five phrases a day is enough; accuracy matters more "
                    "than volume."
                ),
            },
        ],
        "drills": [
            {
                "prompt": "How does 한국어를 sound?",
                "options": ["한구거를", "한국어를", "한구고를", "한궁어를"],
                "answer": "한구거를",
                "explanation": "The final ㄱ of 국 moves to 어: [한구거를].",
            },
            {
                "prompt": "How does 학교에 sound?",
                "options": ["학꾜에", "학교에", "학쿄에", "한교에"],
                "answer": "학꾜에",
                "explanation": "The ㄱ of 교 tenses after the final ㄱ: [학꾜에].",
            },
            {
                "prompt": "How does 같이 가요 sound?",
                "options": ["가치 가요", "가티 가요", "가지 가요", "갓이 가요"],
                "answer": "가치 가요",
                "explanation": "ㅌ before 이 palatalizes to ㅊ: [가치 가요].",
            },
            {
                "prompt": "How does 좋아요 sound?",
                "options": ["조아요", "좋아요", "조하요", "초아요"],
                "answer": "조아요",
                "explanation": "The ㅎ disappears between vowels: [조아요].",
            },
            {
                "prompt": "How does 먹어요 sound?",
                "options": ["머거요", "먹어요", "머고요", "먹거요"],
                "answer": "머거요",
                "explanation": "The final ㄱ moves to 어: [머거요].",
            },
            {
                "prompt": "How does 괜찮아요 sound?",
                "options": ["괜차나요", "괜찮아요", "괜찬하요", "괜차아요"],
                "answer": "괜차나요",
                "explanation": "ㄶ becomes ㄴ and the ㅎ disappears: [괜차나요].",
            },
            {
                "prompt": "How does 연락 sound?",
                "options": ["열락", "연락", "연낙", "열낙"],
                "answer": "열락",
                "explanation": "ㄴ before ㄹ becomes ㄹ: [열락], lateralization.",
            },
            {
                "prompt": "How does 읽어요 sound?",
                "options": ["일거요", "익어요", "일어요", "익거요"],
                "answer": "일거요",
                "explanation": "Before a vowel, ㄹ stays and ㄱ moves: [일거요].",
            },
            {
                "prompt": "How does 없어요 sound?",
                "options": ["업써요", "업서요", "없어요", "엄써요"],
                "answer": "업써요",
                "explanation": "ㅄ becomes ㅂ, and the moving ㅅ tenses: [업써요].",
            },
            {
                "prompt": "What does 전화해요 mean?",
                "options": [
                    "I call (on the phone)",
                    "I eat",
                    "I sit",
                    "I read",
                ],
                "answer": "I call (on the phone)",
                "explanation": "전화하다 means to telephone; 해요 is the polite present ending.",
            },
            {
                "prompt": "How does 국물 sound?",
                "options": ["궁물", "국물", "군물", "굼물"],
                "answer": "궁물",
                "explanation": "ㄱ before ㅁ nasalizes to ㅇ: [궁물].",
            },
            {
                "prompt": "How does 축하해요 sound?",
                "options": ["추카해요", "축하해요", "추하해요", "축카해요"],
                "answer": "추카해요",
                "explanation": "ㄱ plus ㅎ becomes ㅋ: [추카해요], aspiration.",
            },
        ],
        "notes": [
            "Fast speech varies. These are classroom approximations, not a complete phonology.",
            "Rules interact: ㄺ is [ㄱ] in 닭 but [ㄹ] before a vowel in 읽어요.",
            "Read phrases as chunks, not syllable by syllable.",
            "Listen to the same phrase at slow and normal speed; your ear will correct the rule.",
            "Do not stop a conversation to apply a rule. Guess, speak, and adjust.",
        ],
    },
    {
        "slug": "reading-check",
        "day": 7,
        "title": "Read anything check",
        "subtitle": "A 20-item decoding check, not a fluency certificate",
        "goal": (
            "Check your decoding across jamo, CV/CVC blocks, double finals, "
            "public text, and connected speech, then choose a realistic next "
            "practice routine."
        ),
        "summary": (
            "This is a mixed check, not a new rule lesson. It spans the "
            "alphabet, syllable blocks, final clusters, public vocabulary, and "
            "sound changes. A good score means the decoding layer is working. "
            "It does not mean you are fluent or that you can understand a "
            "newspaper."
        ),
        "can_do": (
            "I can decode common signs, menus, and simple sentences and make a "
            "reasonable guess at their meaning. I am not fluent: speed and "
            "vocabulary still need daily practice."
        ),
        "sections": [
            {
                "heading": "What this check covers",
                "body": (
                    "Twenty items, no time limit. Read each prompt aloud, choose "
                    "an answer, then read the explanation even when you are "
                    "right. The items cover jamo, CV and CVC blocks, double "
                    "finals, public text, and sound changes. This checks "
                    "decoding, not vocabulary size or grammar. A high score "
                    "means you can turn letters into sounds; it does not mean "
                    "you understand everything you can pronounce."
                ),
            },
            {
                "heading": "Score yourself honestly",
                "body": (
                    "Use the score to choose the next step, not to judge "
                    "yourself. One lucky guess is not mastery, and one mistake "
                    "is not failure. If you missed an item, say the correct "
                    "pronunciation aloud before moving on."
                ),
                "table": {
                    "headers": ["Score", "What it means", "Next step"],
                    "rows": [
                        ["18–20", "Solid decoding for the material in these lessons.", "Move to graded reading and typing."],
                        ["14–17", "Most patterns are there, but some are still slow.", "Re-read the weak lesson and repeat its drills."],
                        ["0–13", "The basics need another pass.", "Redo Days 1–3, then retake this check."],
                    ],
                },
            },
            {
                "heading": "What to do next",
                "body": (
                    "Decoding improves through short, regular contact. Pick one "
                    "reading source you can understand most of, and keep the "
                    "other two practices small enough that you will actually do "
                    "them. Ten accurate minutes a day beats a two-hour session "
                    "once a week."
                ),
                "table": {
                    "headers": ["Practice", "What to do", "Time"],
                    "rows": [
                        ["Graded reading", "Read short texts you understand about 80–90%; read aloud, then check the meaning.", "10 min/day"],
                        ["Typing", "Type the day's words in 2-beolsik; say each syllable as you type.", "5–10 min/day"],
                        ["Daily review", "Re-read one old lesson's drills and five old words.", "5 min/day"],
                    ],
                },
            },
            {
                "heading": "Type what you read: 2-beolsik",
                "body": (
                    "The standard Korean keyboard is 2-beolsik (두벌식). "
                    "Consonants sit on the left hand and vowels on the right. "
                    "The mapping is worth learning early because typing forces "
                    "you to break each block into its letters. Open a text "
                    "editor with the 2-beolsik layout, type 가나다, 한국어, 커피, "
                    "화장실, and 값 ten times each, and say each syllable aloud "
                    "as you type. Accuracy first; speed comes later."
                ),
                "table": {
                    "headers": ["Keys (QWERTY)", "Letters", "Note"],
                    "rows": [
                        ["r s e f a", "ㄱ ㄴ ㄷ ㄹ ㅁ", "Left hand, home row."],
                        ["q w t d g", "ㅂ ㅈ ㅅ ㅇ ㅎ", "ㅂ is q, not b; ㅇ is d."],
                        ["z x c v", "ㅋ ㅌ ㅊ ㅍ", "Left hand, bottom row."],
                        ["k i j u h y n b m l o p", "ㅏ ㅑ ㅓ ㅕ ㅗ ㅛ ㅜ ㅠ ㅡ ㅣ ㅐ ㅔ", "Right hand, all basic vowels."],
                        ["Shift + r e q t w", "ㄲ ㄸ ㅃ ㅆ ㅉ", "Tense consonants."],
                    ],
                },
            },
            {
                "heading": "A realistic expectation",
                "body": (
                    "A comfortable reading speed for simple text is often "
                    "given as 100–150 syllables per minute. Getting there "
                    "takes weeks of short daily sessions, not one week. At "
                    "first, 20–40 syllables per minute is normal. Decoding is "
                    "only one layer: vocabulary and grammar decide whether you "
                    "understand the sentence. Do not compare your speed with a "
                    "native speaker's."
                ),
            },
            {
                "heading": "What “read anything” really means",
                "body": (
                    "In this course, “read anything” means decode the letters "
                    "and make a reasonable guess at common public text such as "
                    "signs, menus, and short sentences. It does not mean read a "
                    "newspaper or a novel without study. Those need thousands "
                    "of words and a lot of grammar. You have learned the "
                    "alphabet layer, which is a real milestone and a good "
                    "foundation for the next one."
                ),
            },
        ],
        "drills": [
            {
                "prompt": "Which consonant sounds like a light tap between r and l?",
                "options": ["ㄹ", "ㄴ", "ㄷ", "ㅁ"],
                "answer": "ㄹ",
                "explanation": "ㄹ is a light tap, between English r and l; it is not the strong English r.",
            },
            {
                "prompt": "Which vowel is ㅓ?",
                "options": ["eo", "a", "o", "u"],
                "answer": "eo",
                "explanation": "ㅓ is romanized eo, a relaxed vowel between uh and aw.",
            },
            {
                "prompt": "Which letter is silent at the start of a syllable?",
                "options": ["ㅇ", "ㅎ", "ㄱ", "ㅅ"],
                "answer": "ㅇ",
                "explanation": "ㅇ is silent at the start and [ŋ] at the end of a syllable.",
            },
            {
                "prompt": "Which block is ma?",
                "options": ["마", "바", "나", "다"],
                "answer": "마",
                "explanation": "ㅁ + ㅏ = 마, pronounced ma.",
            },
            {
                "prompt": "Which block is han?",
                "options": ["한", "함", "항", "할"],
                "answer": "한",
                "explanation": "ㅎ + ㅏ + ㄴ = 한, pronounced han.",
            },
            {
                "prompt": "Read this block: 밥",
                "options": ["bap", "bat", "ban", "bam"],
                "answer": "bap",
                "explanation": "Final ㅂ is an unreleased [p]: 밥 sounds like bap.",
            },
            {
                "prompt": "Read this block: 강",
                "options": ["gang", "gan", "gam", "ga"],
                "answer": "gang",
                "explanation": "Final ㅇ is [ŋ], the ng in sing: gang.",
            },
            {
                "prompt": "Read this word: 닭",
                "options": ["dak", "dal", "dalk", "dang"],
                "answer": "dak",
                "explanation": "ㄺ reduces to [ㄱ]: 닭 sounds like 닥, dak.",
            },
            {
                "prompt": "Read this word: 삶",
                "options": ["sam", "sal", "salm", "sap"],
                "answer": "sam",
                "explanation": "ㄻ reduces to [ㅁ]: 삶 sounds like 삼, sam.",
            },
            {
                "prompt": "Read this word: 값",
                "options": ["gap", "gal", "gaps", "gam"],
                "answer": "gap",
                "explanation": "ㅄ reduces to [ㅂ]: 값 sounds like 갑, gap.",
            },
            {
                "prompt": "Read this word: 여덟",
                "options": ["yeodeol", "yeodeop", "yeodeot", "yeodeolp"],
                "answer": "yeodeol",
                "explanation": "ㄼ is usually [ㄹ]: 여덟 sounds like 여덜, yeodeol.",
            },
            {
                "prompt": "What does this sign mean? 출구",
                "options": ["exit", "entrance", "parking", "ticket office"],
                "answer": "exit",
                "explanation": "출구 is an exit; 입구 is an entrance.",
            },
            {
                "prompt": "What does this sign mean? 화장실",
                "options": ["restroom", "cafe", "ticket office", "business hours"],
                "answer": "restroom",
                "explanation": "화장실 is the restroom or bathroom.",
            },
            {
                "prompt": "What does this sign mean? 영업시간",
                "options": ["business hours", "free", "discount", "parking"],
                "answer": "business hours",
                "explanation": "영업 means business or operation; 시간 means time or hours.",
            },
            {
                "prompt": "How do you read this price? 3,000원",
                "options": ["삼천 원", "삼백 원", "삼만 원", "사천 원"],
                "answer": "삼천 원",
                "explanation": "3,000 is 삼천, and 원 is the currency.",
            },
            {
                "prompt": "What does this sign mean? 무료",
                "options": ["free", "discount", "closed", "paid"],
                "answer": "free",
                "explanation": "무료 means free of charge; 유료 means paid.",
            },
            {
                "prompt": "How does 한국어 sound?",
                "options": ["한구거", "한국어", "한구고", "한구크"],
                "answer": "한구거",
                "explanation": "The final ㄱ moves to 어: [한구거], liaison.",
            },
            {
                "prompt": "How does 같이 sound?",
                "options": ["가치", "가티", "가지", "갓이"],
                "answer": "가치",
                "explanation": "ㅌ before 이 palatalizes to ㅊ: [가치].",
            },
            {
                "prompt": "How does 좋아요 sound?",
                "options": ["조아요", "좋아요", "조하요", "초아요"],
                "answer": "조아요",
                "explanation": "The ㅎ disappears between vowels: [조아요].",
            },
            {
                "prompt": "How does 학교에 sound?",
                "options": ["학꾜에", "학교에", "학쿄에", "한교에"],
                "answer": "학꾜에",
                "explanation": "The ㄱ of 교 tenses after the final ㄱ: [학꾜에].",
            },
        ],
        "notes": [
            "This check measures decoding, not fluency. A high score does not mean you understand a newspaper.",
            "If you scored below 14, redo Days 1–3 before retaking the check; that is normal, not a failure.",
            "100–150 syllables per minute takes weeks of short daily practice; 20–40 is a reasonable start.",
            "Use graded reading, typing, and five-minute review as the next routine.",
            "Add new words to review as you meet them; decoding without vocabulary still leaves meaning out.",
        ],
    },
]
# fmt: on
