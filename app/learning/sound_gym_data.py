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
            {"korean": "불", "romanization": "bul", "english": "fire"},
            {"korean": "뿔", "romanization": "ppul", "english": "horn"},
            {"korean": "풀", "romanization": "pul", "english": "grass"},
        ],
        "contrast": "plain ㅂ / tense ㅃ / aspirated ㅍ",
        "tip": "ㅂ is relaxed, ㅃ is tight with no air, ㅍ has a strong puff.",
        "level": 1,
    },
    {
        "id": "dal-ttal-tal",
        "words": [
            {"korean": "달", "romanization": "dal", "english": "moon"},
            {"korean": "딸", "romanization": "ttal", "english": "daughter"},
            {"korean": "탈", "romanization": "tal", "english": "mask"},
        ],
        "contrast": "plain ㄷ / tense ㄸ / aspirated ㅌ",
        "tip": "Stop the air completely for ㄸ; let a strong puff out after ㅌ.",
        "level": 1,
    },
    {
        "id": "ja-jja-cha",
        "words": [
            {"korean": "자", "romanization": "ja", "english": "ruler (measuring stick)"},
            {"korean": "짜", "romanization": "jja", "english": "salty (stem of 짜다)"},
            {"korean": "차", "romanization": "cha", "english": "tea"},
        ],
        "contrast": "plain ㅈ / tense ㅉ / aspirated ㅊ",
        "tip": "ㅉ is a tight release with no air; ㅊ ends with a clear puff.",
        "level": 2,
    },
    {
        "id": "bap-ppang",
        "words": [
            {"korean": "밥", "romanization": "bap", "english": "rice / meal"},
            {"korean": "빵", "romanization": "ppang", "english": "bread"},
        ],
        "contrast": "plain ㅂ / tense ㅃ (different vowels, so listen for the onset)",
        "tip": "Say 빵 with tense lips and no puff; 밥 is relaxed and short.",
        "level": 1,
    },
    {
        "id": "sal-ssal",
        "words": [
            {"korean": "살", "romanization": "sal", "english": "flesh / years of age"},
            {"korean": "쌀", "romanization": "ssal", "english": "uncooked rice"},
        ],
        "contrast": "plain ㅅ / tense ㅆ",
        "tip": "Hold the hiss tighter and longer for ㅆ; ㅅ is lighter and shorter.",
        "level": 1,
    },
    {
        "id": "al-mal",
        "words": [
            {"korean": "알", "romanization": "al", "english": "egg"},
            {"korean": "말", "romanization": "mal", "english": "horse"},
        ],
        "contrast": "word-initial ㅇ (silent) vs ㅁ, with the same final ㄹ coda",
        "tip": "Hold the final ㄹ with the tongue tip on the ridge; do not tap it like an English r.",
        "level": 2,
    },
    {
        "id": "geori-gori",
        "words": [
            {"korean": "거리", "romanization": "geori", "english": "street / distance"},
            {"korean": "고리", "romanization": "gori", "english": "ring"},
        ],
        "contrast": "mid-back vowel ㅓ vs high-back vowel ㅗ",
        "tip": "Say 거리 with a relaxed, open jaw; 고리 needs rounded lips and a higher tongue.",
        "level": 1,
    },
    {
        "id": "geuri-guri",
        "words": [
            {"korean": "그리", "romanization": "geuri", "english": "so / in that way (literary)"},
            {"korean": "구리", "romanization": "guri", "english": "copper"},
        ],
        "contrast": "unrounded high vowel ㅡ vs rounded high vowel ㅜ",
        "tip": "Do not round your lips for 그리; round them firmly for 구리.",
        "level": 2,
    },
    {
        "id": "bae-be",
        "words": [
            {"korean": "배", "romanization": "bae", "english": "pear"},
            {"korean": "베", "romanization": "be", "english": "hemp cloth"},
        ],
        "contrast": "ㅐ vs ㅔ (often merged in modern Seoul speech)",
        "tip": "Many speakers say these the same, so lean on context; ㅐ is a slightly more open e.",
        "level": 2,
    },
    {
        "id": "bam-bang-ban",
        "words": [
            {"korean": "밤", "romanization": "bam", "english": "night"},
            {"korean": "방", "romanization": "bang", "english": "room"},
            {"korean": "반", "romanization": "ban", "english": "half"},
        ],
        "contrast": "final nasals ㅁ / ㅇ / ㄴ",
        "tip": "Close your lips for 밤, raise the back of the tongue for 방, touch the ridge for 반.",
        "level": 1,
    },
    {
        "id": "san-sam-sap",
        "words": [
            {"korean": "산", "romanization": "san", "english": "mountain"},
            {"korean": "삼", "romanization": "sam", "english": "three"},
            {"korean": "삽", "romanization": "sap", "english": "shovel"},
        ],
        "contrast": "final codas ㄴ / ㅁ / ㅂ",
        "tip": "For 삽, close your lips and stop the air with no puff; keep 삼 nasal.",
        "level": 2,
    },
]

PRODUCTION_PROMPTS = [
    {
        "id": "annyeong",
        "korean": "안녕하세요",
        "romanization": "annyeonghaseyo",
        "english": "Hello",
        "focus": "four even syllables; no English stress",
        "tip": "Keep the vowels short and even. Do not add a glide.",
        "level": 1,
    },
    {
        "id": "gamsahamnida",
        "korean": "감사합니다",
        "romanization": "gamsahamnida",
        "english": "Thank you",
        "focus": "nasal ㅁ in the -ㅂ니다 ending",
        "tip": "Say gam-sa-ham-ni-da, not gam-sa-hab-ni-da.",
        "level": 1,
    },
    {
        "id": "keopi-han-jan",
        "korean": "커피 한 잔 주세요",
        "romanization": "keopi han jan juseyo",
        "english": "One coffee, please",
        "focus": "aspirated ㅋ and ㅍ with a real puff",
        "tip": "Feel a puff of air on 커 and 피, but not on 주.",
        "level": 1,
    },
    {
        "id": "hwajangsil-eodiyeyo",
        "korean": "화장실이 어디예요?",
        "romanization": "hwajangsiri eodiyeyo?",
        "english": "Where is the bathroom?",
        "focus": "linking the subject marker after a final ㄹ",
        "tip": "Link 화장실 and 이 with no pause: hwajangsiri.",
        "level": 1,
    },
    {
        "id": "cheoncheonhi",
        "korean": "천천히 말해 주세요",
        "romanization": "cheoncheonhi malhae juseyo",
        "english": "Please speak slowly",
        "focus": "aspirated ㅊ and even stress across 천천",
        "tip": "Treat ㅊ as ch plus air, and do not stress the first 천.",
        "level": 1,
    },
    {
        "id": "hangugeoreul-baeugo",
        "korean": "한국어를 배우고 있어요",
        "romanization": "hangugeoreul baeugo isseoyo",
        "english": "I am learning Korean",
        "focus": "ㄹ flap between vowels in 어를",
        "tip": "Let the tongue tap once, lightly, like the t in American 'water'.",
        "level": 2,
    },
    {
        "id": "mul-juseyo",
        "korean": "물 주세요",
        "romanization": "mul juseyo",
        "english": "Water, please",
        "focus": "final ㄹ is held, not tapped",
        "tip": "Finish 물 with the tongue tip resting on the ridge; do not let it bounce.",
        "level": 1,
    },
    {
        "id": "igeo-eolmayeyo",
        "korean": "이거 얼마예요?",
        "romanization": "igeo eolmayeyo?",
        "english": "How much is this?",
        "focus": "open ㅓ vowel in 거 and 얼",
        "tip": "Open the jaw and relax the lips for ㅓ; do not round it into ㅗ.",
        "level": 1,
    },
]
# fmt: on
