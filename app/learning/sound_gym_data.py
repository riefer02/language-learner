"""Hand-authored Sound Gym content for perception and production practice.

The module is deliberately data-only: plain lists and dicts that a route or
template can render without touching models or the database.  Korean is
hand-checked, and romanization follows Revised Romanization (RR) as a guide,
with pronunciation cues taking priority over strict RR where the two differ.

These drills are meant to supplement native audio and a teacher, not replace
them.  See ``DISCLAIMER``.
"""

DISCLAIMER = (
    "Sound Gym drills are training aids, not a substitute for native audio or "
    "a teacher. Browser or TTS voices may not reliably distinguish tense and "
    "aspirated consonants, so do not treat a synthesized voice as a model for "
    "those contrasts. Production scoring is transcript-based: it checks whether "
    "your speech was recognized as the target words, not whether your "
    "pronunciation was accurate."
)

# fmt: off
MINIMAL_PAIRS = [
    {
        "id": "bul-ppul-pul",
        "words": [
            {"target_text": "불", "transliteration": "bul", "gloss": "fire"},
            {"target_text": "뿔", "transliteration": "ppul", "gloss": "horn"},
            {"target_text": "풀", "transliteration": "pul", "gloss": "grass"},
        ],
        "contrast": "plain ㅂ / tense ㅃ / aspirated ㅍ",
        "tip": "ㅂ is relaxed, ㅃ is tight with no air, ㅍ has a strong puff.",
        "level": 1,
    },
    {
        "id": "dal-ttal-tal",
        "words": [
            {"target_text": "달", "transliteration": "dal", "gloss": "moon"},
            {"target_text": "딸", "transliteration": "ttal", "gloss": "daughter"},
            {"target_text": "탈", "transliteration": "tal", "gloss": "mask"},
        ],
        "contrast": "plain ㄷ / tense ㄸ / aspirated ㅌ",
        "tip": "Stop the air completely for ㄸ; let a strong puff out after ㅌ.",
        "level": 1,
    },
    {
        "id": "ja-jja-cha",
        "words": [
            {"target_text": "자", "transliteration": "ja", "gloss": "ruler (measuring stick)"},
            {"target_text": "짜", "transliteration": "jja", "gloss": "salty (stem of 짜다)"},
            {"target_text": "차", "transliteration": "cha", "gloss": "tea"},
        ],
        "contrast": "plain ㅈ / tense ㅉ / aspirated ㅊ",
        "tip": "ㅉ is a tight release with no air; ㅊ ends with a clear puff.",
        "level": 2,
    },
    {
        "id": "bap-ppang",
        "words": [
            {"target_text": "밥", "transliteration": "bap", "gloss": "rice / meal"},
            {"target_text": "빵", "transliteration": "ppang", "gloss": "bread"},
        ],
        "contrast": "plain ㅂ / tense ㅃ (different vowels, so listen for the onset)",
        "tip": "Say 빵 with tense lips and no puff; 밥 is relaxed and short.",
        "level": 1,
    },
    {
        "id": "sal-ssal",
        "words": [
            {"target_text": "살", "transliteration": "sal", "gloss": "flesh / years of age"},
            {"target_text": "쌀", "transliteration": "ssal", "gloss": "uncooked rice"},
        ],
        "contrast": "plain ㅅ / tense ㅆ",
        "tip": "Hold the hiss tighter and longer for ㅆ; ㅅ is lighter and shorter.",
        "level": 1,
    },
    {
        "id": "al-mal",
        "words": [
            {"target_text": "알", "transliteration": "al", "gloss": "egg"},
            {"target_text": "말", "transliteration": "mal", "gloss": "horse"},
        ],
        "contrast": "word-initial ㅇ (silent) vs ㅁ, with the same final ㄹ coda",
        "tip": "Hold the final ㄹ with the tongue tip on the ridge; do not tap it like an English r.",
        "level": 2,
    },
    {
        "id": "geori-gori",
        "words": [
            {"target_text": "거리", "transliteration": "geori", "gloss": "street / distance"},
            {"target_text": "고리", "transliteration": "gori", "gloss": "ring"},
        ],
        "contrast": "mid-back vowel ㅓ vs high-back vowel ㅗ",
        "tip": "Say 거리 with a relaxed, open jaw; 고리 needs rounded lips and a higher tongue.",
        "level": 1,
    },
    {
        "id": "geuri-guri",
        "words": [
            {"target_text": "그리", "transliteration": "geuri", "gloss": "so / in that way (literary)"},
            {"target_text": "구리", "transliteration": "guri", "gloss": "copper"},
        ],
        "contrast": "unrounded high vowel ㅡ vs rounded high vowel ㅜ",
        "tip": "Do not round your lips for 그리; round them firmly for 구리.",
        "level": 2,
    },
    {
        "id": "bae-be",
        "words": [
            {"target_text": "배", "transliteration": "bae", "gloss": "pear"},
            {"target_text": "베", "transliteration": "be", "gloss": "hemp cloth"},
        ],
        "contrast": "ㅐ vs ㅔ (often merged in modern Seoul speech)",
        "tip": "Many speakers say these the same, so lean on context; ㅐ is a slightly more open e.",
        "level": 2,
    },
    {
        "id": "bam-bang-ban",
        "words": [
            {"target_text": "밤", "transliteration": "bam", "gloss": "night"},
            {"target_text": "방", "transliteration": "bang", "gloss": "room"},
            {"target_text": "반", "transliteration": "ban", "gloss": "half"},
        ],
        "contrast": "final nasals ㅁ / ㅇ / ㄴ",
        "tip": "Close your lips for 밤, raise the back of the tongue for 방, touch the ridge for 반.",
        "level": 1,
    },
    {
        "id": "san-sam-sap",
        "words": [
            {"target_text": "산", "transliteration": "san", "gloss": "mountain"},
            {"target_text": "삼", "transliteration": "sam", "gloss": "three"},
            {"target_text": "삽", "transliteration": "sap", "gloss": "shovel"},
        ],
        "contrast": "final codas ㄴ / ㅁ / ㅂ",
        "tip": "For 삽, close your lips and stop the air with no puff; keep 삼 nasal.",
        "level": 2,
    },
]

PRODUCTION_PROMPTS = [
    {
        "id": "annyeong",
        "target_text": "안녕하세요",
        "transliteration": "annyeonghaseyo",
        "gloss": "Hello",
        "focus": "four even syllables; no English stress",
        "tip": "Keep the vowels short and even. Do not add a glide.",
        "level": 1,
    },
    {
        "id": "gamsahamnida",
        "target_text": "감사합니다",
        "transliteration": "gamsahamnida",
        "gloss": "Thank you",
        "focus": "nasal ㅁ in the -ㅂ니다 ending",
        "tip": "Say gam-sa-ham-ni-da, not gam-sa-hab-ni-da.",
        "level": 1,
    },
    {
        "id": "keopi-han-jan",
        "target_text": "커피 한 잔 주세요",
        "transliteration": "keopi han jan juseyo",
        "gloss": "One coffee, please",
        "focus": "aspirated ㅋ and ㅍ with a real puff",
        "tip": "Feel a puff of air on 커 and 피, but not on 주.",
        "level": 1,
    },
    {
        "id": "hwajangsil-eodiyeyo",
        "target_text": "화장실이 어디예요?",
        "transliteration": "hwajangsiri eodiyeyo?",
        "gloss": "Where is the bathroom?",
        "focus": "linking the subject marker after a final ㄹ",
        "tip": "Link 화장실 and 이 with no pause: hwajangsiri.",
        "level": 1,
    },
    {
        "id": "cheoncheonhi",
        "target_text": "천천히 말해 주세요",
        "transliteration": "cheoncheonhi malhae juseyo",
        "gloss": "Please speak slowly",
        "focus": "aspirated ㅊ and even stress across 천천",
        "tip": "Treat ㅊ as ch plus air, and do not stress the first 천.",
        "level": 1,
    },
    {
        "id": "hangugeoreul-baeugo",
        "target_text": "한국어를 배우고 있어요",
        "transliteration": "hangugeoreul baeugo isseoyo",
        "gloss": "I am learning Korean",
        "focus": "ㄹ flap between vowels in 어를",
        "tip": "Let the tongue tap once, lightly, like the t in American 'water'.",
        "level": 2,
    },
    {
        "id": "mul-juseyo",
        "target_text": "물 주세요",
        "transliteration": "mul juseyo",
        "gloss": "Water, please",
        "focus": "final ㄹ is held, not tapped",
        "tip": "Finish 물 with the tongue tip resting on the ridge; do not let it bounce.",
        "level": 1,
    },
    {
        "id": "igeo-eolmayeyo",
        "target_text": "이거 얼마예요?",
        "transliteration": "igeo eolmayeyo?",
        "gloss": "How much is this?",
        "focus": "open ㅓ vowel in 거 and 얼",
        "tip": "Open the jaw and relax the lips for ㅓ; do not round it into ㅗ.",
        "level": 1,
    },
]
# fmt: on
