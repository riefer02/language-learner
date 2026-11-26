"""Curated register choices and alternate forms per language.

The starter decks teach one default register per phrase. This module supplies
the other everyday forms so Look up can ask how formal the learner wants to be
and review cards can show the contrast. These are hand-curated starter forms,
not native-checked recordings.
"""

import hashlib
import os

# (value, learner-facing label) in display order. The first entry is the
# default for that language when the learner does not choose.
REGISTER_CHOICES = {
    "ko": [
        ("polite", "Everyday polite (해요)"),
        ("formal", "Formal (합니다)"),
        ("casual", "Casual (반말)"),
    ],
    "am": [
        ("formal", "Formal (እርስዎ)"),
        ("casual", "Everyday (አንተ / አንቺ)"),
    ],
}

REGISTER_LABELS = {
    "ko": {
        "polite": "Everyday polite",
        "formal": "Formal",
        "casual": "Casual",
    },
    "am": {
        "casual": "Everyday",
        "formal": "Formal",
    },
}

# Formal first, then polite, then casual. Used to order review alternates.
REGISTER_ORDER = {"formal": 0, "polite": 1, "casual": 2}

# Alternate forms keyed by the language and the item's exact target text.
# Each entry is a form the learner might hear instead of the default.
ALTERNATES = {
    "ko": {
        "안녕하세요": [
            {
                "label": "Formal",
                "register": "formal",
                "text": "안녕하십니까",
                "transliteration": "annyeonghasimnikka",
            },
            {
                "label": "Casual",
                "register": "casual",
                "text": "안녕",
                "transliteration": "annyeong",
            },
        ],
        "감사합니다": [
            {
                "label": "Everyday polite",
                "register": "polite",
                "text": "고마워요",
                "transliteration": "gomawoyo",
            },
            {
                "label": "Casual",
                "register": "casual",
                "text": "고마워",
                "transliteration": "gomawo",
            },
        ],
        "죄송합니다": [
            {
                "label": "Everyday polite",
                "register": "polite",
                "text": "죄송해요",
                "transliteration": "joesonghaeyo",
            },
            {
                "label": "Casual",
                "register": "casual",
                "text": "미안해",
                "transliteration": "mianhae",
            },
        ],
        "네": [
            {
                "label": "Casual",
                "register": "casual",
                "text": "응",
                "transliteration": "eung",
            },
        ],
        "아니요": [
            {
                "label": "Casual",
                "register": "casual",
                "text": "아니",
                "transliteration": "ani",
            },
        ],
        "저는 학생이에요": [
            {
                "label": "Formal",
                "register": "formal",
                "text": "저는 학생입니다",
                "transliteration": "jeoneun haksaeng-imnida",
            },
            {
                "label": "Casual",
                "register": "casual",
                "text": "나는 학생이야",
                "transliteration": "naneun haksaeng-iya",
            },
        ],
        "커피 한 잔 주세요": [
            {
                "label": "Casual",
                "register": "casual",
                "text": "커피 한 잔 줘",
                "transliteration": "keopi han jan jwo",
            },
        ],
        "물 주세요": [
            {
                "label": "Casual",
                "register": "casual",
                "text": "물 줘",
                "transliteration": "mul jwo",
            },
        ],
        "이거 얼마예요?": [
            {
                "label": "Casual",
                "register": "casual",
                "text": "이거 얼마야?",
                "transliteration": "igeo eolmaya?",
            },
        ],
        "화장실이 어디예요?": [
            {
                "label": "Casual",
                "register": "casual",
                "text": "화장실이 어디야?",
                "transliteration": "hwajangsiri eodiya?",
            },
        ],
        "맛있어요": [
            {
                "label": "Casual",
                "register": "casual",
                "text": "맛있어",
                "transliteration": "masisseo",
            },
        ],
        "괜찮아요": [
            {
                "label": "Casual",
                "register": "casual",
                "text": "괜찮아",
                "transliteration": "gwaenchana",
            },
        ],
        "잠시만요": [
            {
                "label": "Casual",
                "register": "casual",
                "text": "잠시만",
                "transliteration": "jamsiman",
            },
        ],
        "천천히 말해 주세요": [
            {
                "label": "Casual",
                "register": "casual",
                "text": "천천히 말해 줘",
                "transliteration": "cheoncheonhi malhae jwo",
            },
        ],
        "다시 한번 말해 주세요": [
            {
                "label": "Casual",
                "register": "casual",
                "text": "다시 한번 말해 줘",
                "transliteration": "dasi hanbeon malhae jwo",
            },
        ],
        "한국어를 배우고 있어요": [
            {
                "label": "Formal",
                "register": "formal",
                "text": "한국어를 배우고 있습니다",
                "transliteration": "hangugeoreul baeugo isseumnida",
            },
            {
                "label": "Casual",
                "register": "casual",
                "text": "나는 한국어를 배우고 있어",
                "transliteration": "naneun hangugeoreul baeugo isseo",
            },
        ],
    },
    "am": {
        "እንደምን ነህ?": [
            {
                "label": "Formal",
                "register": "formal",
                "text": "እንደምን ነዎት?",
                "transliteration": "endemin newot?",
            },
        ],
        "እንደምን ነሽ?": [
            {
                "label": "Formal",
                "register": "formal",
                "text": "እንደምን ነዎት?",
                "transliteration": "endemin newot?",
            },
        ],
        "እባክህ": [
            {
                "label": "Formal",
                "register": "formal",
                "text": "እባክዎን",
                "transliteration": "ebakiwon",
            },
        ],
        "እባክሽ": [
            {
                "label": "Formal",
                "register": "formal",
                "text": "እባክዎን",
                "transliteration": "ebakiwon",
            },
        ],
        "ደህና ሁን": [
            {
                "label": "Formal",
                "register": "formal",
                "text": "ደህና ይሁኑ",
                "transliteration": "dehna yihunu",
            },
        ],
        "ደህና ሁኚ": [
            {
                "label": "Formal",
                "register": "formal",
                "text": "ደህና ይሁኑ",
                "transliteration": "dehna yihunu",
            },
        ],
        "ስምህ ማን ነው?": [
            {
                "label": "Formal",
                "register": "formal",
                "text": "ስምዎ ማን ነው?",
                "transliteration": "simwo man new?",
            },
        ],
        "ስምሽ ማን ነው?": [
            {
                "label": "Formal",
                "register": "formal",
                "text": "ስምዎ ማን ነው?",
                "transliteration": "simwo man new?",
            },
        ],
        "እንኳን ደህና መጣህ": [
            {
                "label": "Formal",
                "register": "formal",
                "text": "እንኳን ደህና መጡ",
                "transliteration": "enkuan dehna metu",
            },
        ],
        "እንኳን ደህና መጣሽ": [
            {
                "label": "Formal",
                "register": "formal",
                "text": "እንኳን ደህና መጡ",
                "transliteration": "enkuan dehna metu",
            },
        ],
    },
}


def register_choices(code):
    """Return ``(value, label)`` pairs for a language, or an empty list."""
    return REGISTER_CHOICES.get(code, [])


def default_register(code):
    choices = REGISTER_CHOICES.get(code)
    if not choices:
        return None
    return choices[0][0]


def normalize_register(code, value):
    """Clamp a register to one the language actually offers.

    Unknown languages have no register, so the stored value is ``None`` rather
    than a label the library would display incorrectly.
    """
    choices = REGISTER_CHOICES.get(code)
    if not choices:
        return None
    allowed = {choice for choice, _ in choices}
    return value if value in allowed else default_register(code)


# Languages whose second person changes with the addressee's gender or number.
ADDRESSEE_LANGUAGES = {"am"}

ADDRESSEE_LABELS = {
    "male": "To a man",
    "female": "To a woman",
    "group": "To a group",
}


def normalize_addressee(code, value):
    if code in ADDRESSEE_LANGUAGES and value in {"male", "female", "group"}:
        return value
    return "any"


def addressee_label(code, value):
    if code not in ADDRESSEE_LANGUAGES:
        return ""
    return ADDRESSEE_LABELS.get(value, "")


def register_label(code, value):
    return REGISTER_LABELS.get(code, {}).get(value, "")


def alternates_for(code, target_text):
    """Return the curated alternate forms for one item, formal first."""
    forms = ALTERNATES.get(code, {}).get(target_text, [])
    return sorted(
        forms, key=lambda form: REGISTER_ORDER.get(form.get("register"), 99)
    )


def _audio_code(language_code):
    return "".join(char for char in str(language_code) if char.isalnum()) or "xx"


def variant_audio_filename(language_code, text):
    """A stable filename for one form, independent of which card shows it."""
    code = _audio_code(language_code)
    digest = hashlib.sha256(f"{code}\0{text}".encode()).hexdigest()[:12]
    return f"variant_{code}_{digest}.mp3"


def variant_audio_url(audio_dir, language_code, text):
    """Return the public URL when the stored variant audio exists and is non-empty."""
    filename = variant_audio_filename(language_code, text)
    try:
        if os.path.getsize(os.path.join(audio_dir, filename)) > 0:
            return f"/static/audio/{filename}"
    except OSError:
        return None
    return None


def all_variant_audio_filenames(audio_dir):
    """Existing variant files, so ``media-gc`` does not treat them as orphans."""
    filenames = set()
    for code, groups in ALTERNATES.items():
        for forms in groups.values():
            for form in forms:
                filename = variant_audio_filename(code, form["text"])
                try:
                    if os.path.getsize(os.path.join(audio_dir, filename)) > 0:
                        filenames.add(filename)
                except OSError:
                    continue
    return sorted(filenames)
