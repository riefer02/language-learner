"""Hand-authored Hangul curriculum for the first three lessons.

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
]
# fmt: on
