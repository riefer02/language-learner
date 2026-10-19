"""Seed content for the first vertical slice.

This is deliberately small and hand-curated. The production content pipeline
will replace it with a frequency-ordered, native-reviewed database.
"""

from app import db
from app.learning.service import ensure_review_cards, get_or_create_local_user
from app.models import Item

# fmt: off
SEED_ITEMS = [
    # Survival chunks
    {"item_type": "chunk", "korean": "안녕하세요", "english": "Hello", "romanization": "annyeonghaseyo", "level": 1, "default_skill": "produce", "notes": "The default polite greeting. Use it with strangers and adults."},
    {"item_type": "chunk", "korean": "감사합니다", "english": "Thank you", "romanization": "gamsahamnida", "level": 1, "default_skill": "produce", "notes": "Formal polite thanks. 고마워요 is more casual."},
    {"item_type": "lexeme", "korean": "네", "english": "Yes", "romanization": "ne", "level": 1, "default_skill": "recognize", "notes": "Also used to acknowledge that you are listening."},
    {"item_type": "lexeme", "korean": "아니요", "english": "No", "romanization": "aniyo", "level": 1, "default_skill": "recognize", "notes": "Polite no. 아니 is casual."},
    {"item_type": "chunk", "korean": "저는 학생이에요", "english": "I am a student", "romanization": "jeoneun haksaeng-ieyo", "level": 1, "default_skill": "produce", "notes": "저는 = as for me; 학생 = student; 이에요 = polite copula after a consonant."},
    {"item_type": "chunk", "korean": "커피 한 잔 주세요", "english": "One coffee, please", "romanization": "keopi han jan juseyo", "level": 1, "default_skill": "produce", "notes": "한 잔 is the counter for cups. 주세요 = please give me."},
    {"item_type": "chunk", "korean": "이거 얼마예요?", "english": "How much is this?", "romanization": "igeo eolmayeyo?", "level": 1, "default_skill": "produce", "notes": "이거 = this thing; 얼마 = how much."},
    {"item_type": "chunk", "korean": "화장실이 어디예요?", "english": "Where is the bathroom?", "romanization": "hwajangsiri eodiyeyo?", "level": 1, "default_skill": "produce", "notes": "화장실 = bathroom; 이 = subject marker; 어디 = where."},
    {"item_type": "chunk", "korean": "물 주세요", "english": "Water, please", "romanization": "mul juseyo", "level": 1, "default_skill": "produce", "notes": "A minimal, useful request. 주세요 is the polite request ending."},
    {"item_type": "chunk", "korean": "맛있어요", "english": "It is delicious", "romanization": "masisseoyo", "level": 1, "default_skill": "produce", "notes": "Use it about food. 맛없어요 means it does not taste good."},
    {"item_type": "chunk", "korean": "괜찮아요", "english": "It is okay / I am fine", "romanization": "gwaenchanayo", "level": 1, "default_skill": "produce", "notes": "Also used to decline an offer politely."},
    {"item_type": "chunk", "korean": "죄송합니다", "english": "I am sorry", "romanization": "joesonghamnida", "level": 1, "default_skill": "produce", "notes": "Formal polite apology. 미안해요 is more casual."},
    {"item_type": "chunk", "korean": "잠시만요", "english": "Just a moment, please", "romanization": "jamsimanyo", "level": 1, "default_skill": "produce", "notes": "Useful on the phone or when asking someone to wait."},
    {"item_type": "chunk", "korean": "천천히 말해 주세요", "english": "Please speak slowly", "romanization": "cheoncheonhi malhae juseyo", "level": 1, "default_skill": "produce", "notes": "A repair phrase. 천천히 = slowly; 말하다 = to speak."},
    {"item_type": "chunk", "korean": "다시 한번 말해 주세요", "english": "Please say that again", "romanization": "dasi hanbeon malhae juseyo", "level": 1, "default_skill": "produce", "notes": "다시 = again; 한번 = one time."},
    {"item_type": "chunk", "korean": "한국어를 배우고 있어요", "english": "I am learning Korean", "romanization": "hangugeoreul baeugo isseoyo", "level": 2, "default_skill": "produce", "notes": "한국어 = Korean; 를 = object marker; -고 있어요 = present progressive."},
    # Core nouns
    {"item_type": "lexeme", "korean": "친구", "english": "friend", "romanization": "chingu", "level": 1, "default_skill": "recognize", "notes": "A peer or close acquaintance; not a romantic partner."},
    {"item_type": "lexeme", "korean": "학교", "english": "school", "romanization": "hakgyo", "level": 1, "default_skill": "recognize", "notes": "Sino-Korean 학 (study) + 교 (teach)."},
    {"item_type": "lexeme", "korean": "집", "english": "home / house", "romanization": "jip", "level": 1, "default_skill": "recognize", "notes": "Also used for a restaurant or shop in compounds."},
    {"item_type": "lexeme", "korean": "밥", "english": "rice / meal", "romanization": "bap", "level": 1, "default_skill": "recognize", "notes": "밥을 먹다 = to eat; literally to eat rice."},
    {"item_type": "lexeme", "korean": "물", "english": "water", "romanization": "mul", "level": 1, "default_skill": "recognize", "notes": "Do not confuse with 물건 (thing)."},
    {"item_type": "lexeme", "korean": "개", "english": "dog", "romanization": "gae", "level": 1, "default_skill": "recognize", "notes": "The counter 개 is written the same but means 'items'."},
    {"item_type": "lexeme", "korean": "고양이", "english": "cat", "romanization": "goyangi", "level": 1, "default_skill": "recognize", "notes": "A native Korean word, not Sino-Korean."},
    {"item_type": "lexeme", "korean": "오늘", "english": "today", "romanization": "oneul", "level": 1, "default_skill": "recognize", "notes": "오늘은 = as for today."},
    {"item_type": "lexeme", "korean": "내일", "english": "tomorrow", "romanization": "naeil", "level": 1, "default_skill": "recognize", "notes": "내일 봐요 = see you tomorrow."},
    # Grammar patterns
    {"item_type": "grammar", "korean": "은/는", "english": "topic / contrast marker", "romanization": "eun/neun", "level": 1, "default_skill": "recognize", "notes": "Attaches to the topic. 은 after a consonant, 는 after a vowel. It often signals 'as for X' or a contrast."},
    {"item_type": "grammar", "korean": "이/가", "english": "subject marker", "romanization": "i/ga", "level": 1, "default_skill": "recognize", "notes": "Marks the subject, often new or identifying information. 이 after a consonant, 가 after a vowel."},
    {"item_type": "grammar", "korean": "을/를", "english": "object marker", "romanization": "eul/reul", "level": 1, "default_skill": "recognize", "notes": "Marks the direct object. 을 after a consonant, 를 after a vowel."},
    {"item_type": "grammar", "korean": "에/에서", "english": "location particles", "romanization": "e/eseo", "level": 1, "default_skill": "recognize", "notes": "에 marks destination, time, or existence; 에서 marks where an action happens or a source."},
    {"item_type": "grammar", "korean": "-아/어요", "english": "polite present ending", "romanization": "-a/eoyo", "level": 1, "default_skill": "recognize", "notes": "The default informal-polite ending. The vowel harmony choice depends on the stem."},
]
# fmt: on


def seed_content():
    """Idempotently insert seed items and create the learner's cards."""
    user = get_or_create_local_user()
    created_items = 0
    for entry in SEED_ITEMS:
        existing = Item.query.filter_by(
            korean=entry["korean"],
            english=entry["english"],
            item_type=entry["item_type"],
        ).first()
        if existing:
            continue
        db.session.add(Item(**entry))
        created_items += 1
    if created_items:
        db.session.commit()
    created_cards = ensure_review_cards(user.id)
    return user, created_items, created_cards
