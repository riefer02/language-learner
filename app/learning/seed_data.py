"""Seed content for the first vertical slice.

This is deliberately small and hand-curated. The production content pipeline
will replace it with a frequency-ordered, native-reviewed database.
"""

from app import db
from app.learning.service import ensure_review_cards, get_or_create_local_user
from app.models import Item
from app.models_language import Language

# fmt: off
SEED_ITEMS = [
    # Survival chunks
    {"item_type": "chunk", "target_text": "안녕하세요", "gloss": "Hello", "transliteration": "annyeonghaseyo", "level": 1, "default_skill": "produce", "notes": "The default polite greeting. Use it with strangers and adults."},
    {"item_type": "chunk", "target_text": "감사합니다", "gloss": "Thank you", "transliteration": "gamsahamnida", "level": 1, "default_skill": "produce", "notes": "Formal polite thanks. 고마워요 is more casual."},
    {"item_type": "lexeme", "target_text": "네", "gloss": "Yes", "transliteration": "ne", "level": 1, "default_skill": "recognize", "notes": "Also used to acknowledge that you are listening."},
    {"item_type": "lexeme", "target_text": "아니요", "gloss": "No", "transliteration": "aniyo", "level": 1, "default_skill": "recognize", "notes": "Polite no. 아니 is casual."},
    {"item_type": "chunk", "target_text": "저는 학생이에요", "gloss": "I am a student", "transliteration": "jeoneun haksaeng-ieyo", "level": 1, "default_skill": "produce", "notes": "저는 = as for me; 학생 = student; 이에요 = polite copula after a consonant."},
    {"item_type": "chunk", "target_text": "커피 한 잔 주세요", "gloss": "One coffee, please", "transliteration": "keopi han jan juseyo", "level": 1, "default_skill": "produce", "notes": "한 잔 is the counter for cups. 주세요 = please give me."},
    {"item_type": "chunk", "target_text": "이거 얼마예요?", "gloss": "How much is this?", "transliteration": "igeo eolmayeyo?", "level": 1, "default_skill": "produce", "notes": "이거 = this thing; 얼마 = how much."},
    {"item_type": "chunk", "target_text": "화장실이 어디예요?", "gloss": "Where is the bathroom?", "transliteration": "hwajangsiri eodiyeyo?", "level": 1, "default_skill": "produce", "notes": "화장실 = bathroom; 이 = subject marker; 어디 = where."},
    {"item_type": "chunk", "target_text": "물 주세요", "gloss": "Water, please", "transliteration": "mul juseyo", "level": 1, "default_skill": "produce", "notes": "A minimal, useful request. 주세요 is the polite request ending."},
    {"item_type": "chunk", "target_text": "맛있어요", "gloss": "It is delicious", "transliteration": "masisseoyo", "level": 1, "default_skill": "produce", "notes": "Use it about food. 맛없어요 means it does not taste good."},
    {"item_type": "chunk", "target_text": "괜찮아요", "gloss": "It is okay / I am fine", "transliteration": "gwaenchanayo", "level": 1, "default_skill": "produce", "notes": "Also used to decline an offer politely."},
    {"item_type": "chunk", "target_text": "죄송합니다", "gloss": "I am sorry", "transliteration": "joesonghamnida", "level": 1, "default_skill": "produce", "notes": "Formal polite apology. 미안해요 is more casual."},
    {"item_type": "chunk", "target_text": "잠시만요", "gloss": "Just a moment, please", "transliteration": "jamsimanyo", "level": 1, "default_skill": "produce", "notes": "Useful on the phone or when asking someone to wait."},
    {"item_type": "chunk", "target_text": "천천히 말해 주세요", "gloss": "Please speak slowly", "transliteration": "cheoncheonhi malhae juseyo", "level": 1, "default_skill": "produce", "notes": "A repair phrase. 천천히 = slowly; 말하다 = to speak."},
    {"item_type": "chunk", "target_text": "다시 한번 말해 주세요", "gloss": "Please say that again", "transliteration": "dasi hanbeon malhae juseyo", "level": 1, "default_skill": "produce", "notes": "다시 = again; 한번 = one time."},
    {"item_type": "chunk", "target_text": "한국어를 배우고 있어요", "gloss": "I am learning Korean", "transliteration": "hangugeoreul baeugo isseoyo", "level": 2, "default_skill": "produce", "notes": "한국어 = Korean; 를 = object marker; -고 있어요 = present progressive."},
    # Core nouns
    {"item_type": "lexeme", "target_text": "친구", "gloss": "friend", "transliteration": "chingu", "level": 1, "default_skill": "recognize", "notes": "A peer or close acquaintance; not a romantic partner."},
    {"item_type": "lexeme", "target_text": "학교", "gloss": "school", "transliteration": "hakgyo", "level": 1, "default_skill": "recognize", "notes": "Sino-Korean 학 (study) + 교 (teach)."},
    {"item_type": "lexeme", "target_text": "집", "gloss": "home / house", "transliteration": "jip", "level": 1, "default_skill": "recognize", "notes": "Also used for a restaurant or shop in compounds."},
    {"item_type": "lexeme", "target_text": "밥", "gloss": "rice / meal", "transliteration": "bap", "level": 1, "default_skill": "recognize", "notes": "밥을 먹다 = to eat; literally to eat rice."},
    {"item_type": "lexeme", "target_text": "물", "gloss": "water", "transliteration": "mul", "level": 1, "default_skill": "recognize", "notes": "Do not confuse with 물건 (thing)."},
    {"item_type": "lexeme", "target_text": "개", "gloss": "dog", "transliteration": "gae", "level": 1, "default_skill": "recognize", "notes": "The counter 개 is written the same but means 'items'."},
    {"item_type": "lexeme", "target_text": "고양이", "gloss": "cat", "transliteration": "goyangi", "level": 1, "default_skill": "recognize", "notes": "A native Korean word, not Sino-Korean."},
    {"item_type": "lexeme", "target_text": "오늘", "gloss": "today", "transliteration": "oneul", "level": 1, "default_skill": "recognize", "notes": "오늘은 = as for today."},
    {"item_type": "lexeme", "target_text": "내일", "gloss": "tomorrow", "transliteration": "naeil", "level": 1, "default_skill": "recognize", "notes": "내일 봐요 = see you tomorrow."},
    # Grammar patterns
    {"item_type": "grammar", "target_text": "은/는", "gloss": "topic / contrast marker", "transliteration": "eun/neun", "level": 1, "default_skill": "recognize", "notes": "Attaches to the topic. 은 after a consonant, 는 after a vowel. It often signals 'as for X' or a contrast."},
    {"item_type": "grammar", "target_text": "이/가", "gloss": "subject marker", "transliteration": "i/ga", "level": 1, "default_skill": "recognize", "notes": "Marks the subject, often new or identifying information. 이 after a consonant, 가 after a vowel."},
    {"item_type": "grammar", "target_text": "을/를", "gloss": "object marker", "transliteration": "eul/reul", "level": 1, "default_skill": "recognize", "notes": "Marks the direct object. 을 after a consonant, 를 after a vowel."},
    {"item_type": "grammar", "target_text": "에/에서", "gloss": "location particles", "transliteration": "e/eseo", "level": 1, "default_skill": "recognize", "notes": "에 marks destination, time, or existence; 에서 marks where an action happens or a source."},
    {"item_type": "grammar", "target_text": "-아/어요", "gloss": "polite present ending", "transliteration": "-a/eoyo", "level": 1, "default_skill": "recognize", "notes": "The default informal-polite ending. The vowel harmony choice depends on the stem."},
]
# fmt: on


def seed_content():
    """Idempotently insert tagged Korean seed items and their cards."""
    user = get_or_create_local_user()
    language = Language.query.filter_by(code="ko").first()
    if language is None:
        language = Language(code="ko", name="Korean", native_name="한국어")
        db.session.add(language)
        db.session.flush()

    created_items = 0
    for entry in SEED_ITEMS:
        existing = Item.query.filter_by(
            target_text=entry["target_text"],
            gloss=entry["gloss"],
            item_type=entry["item_type"],
        ).first()
        if existing:
            if existing.language_id is None:
                existing.language_id = language.id
            continue
        db.session.add(Item(**entry, language_id=language.id))
        created_items += 1
    if created_items:
        db.session.commit()
    created_cards = ensure_review_cards(user.id, language.id)
    return user, created_items, created_cards
