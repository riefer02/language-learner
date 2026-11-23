"""Hand-authored mission-based roleplay scenes.

Each scene is a short, self-contained exchange: the app shows one character
line, the learner answers in Korean (typed or spoken), and a tolerant matcher
checks the answer against ``expected``.  Finishing a scene turns the three
debrief cards into review material, so every card should be a reusable chunk
rather than a one-off sentence.

The module is deliberately data-only.  Korean is hand-checked, and
romanization follows Revised Romanization (RR) as a guide.  ``알렉스`` (Alex)
is a placeholder learner name that a route or template may replace with the
signed-in learner's name.

These scenes are practice aids, not a substitute for a teacher or native
audio.  See the Sound Gym content for the same caveat about synthesized
speech.
"""

# fmt: off
SCENES = [
    {
        "slug": "cafe-order",
        "title": "Order at a café",
        "subtitle": "One drink, one receipt",
        "level": 1,
        "goal": "Order one drink and ask for a receipt.",
        "persona": "Barista",
        "setting": "A busy café in Seoul",
        "can_do": "I can order a drink and ask for a receipt in polite Korean.",
        "steps": [
            {
                "character_text": "어서 오세요, 뭐 드릴까요?",
                "character_gloss": "Welcome, what can I get you?",
                "expected": [
                    "아이스 아메리카노 한 잔 주세요",
                    "아메리카노 한 잔 주세요",
                    "커피 한 잔 주세요",
                ],
                "hint": "Drink + 한 잔 + 주세요.",
                "success_note": "한 잔 is the counter for cups.",
                "target_item": {
                    "target_text": "아이스 아메리카노 한 잔 주세요",
                    "gloss": "One iced Americano, please",
                    "transliteration": "aiseu amerikano han jan juseyo",
                    "notes": "한 잔 = one cup; 주세요 = please give me.",
                },
            },
            {
                "character_text": (
                    "아이스로 드릴까요? 사이즈는 어떻게 해 드릴까요?"
                ),
                "character_gloss": (
                    "Would you like it iced? What size would you like?"
                ),
                "expected": [
                    "큰 사이즈로 주세요",
                    "레귤러 사이즈로 주세요",
                    "작은 사이즈로 주세요",
                ],
                "hint": "Size + 로 주세요.",
                "success_note": "로 marks the size or option you choose.",
                "target_item": {
                    "target_text": "큰 사이즈로 주세요",
                    "gloss": "A large size, please",
                    "transliteration": "keun saijeu-ro juseyo",
                    "notes": "큰 = large; 사이즈 = size; -로 = as / with.",
                },
            },
            {
                "character_text": (
                    "커피 여기 있습니다. 더 필요하신 거 있으세요?"
                ),
                "character_gloss": (
                    "Here's your coffee. Is there anything else you need?"
                ),
                "expected": [
                    "영수증 주세요",
                    "영수증도 주세요",
                    "영수증 받을 수 있을까요?",
                ],
                "hint": "영수증 + 주세요.",
                "success_note": "영수증 means receipt; 도 makes it 'also'.",
                "target_item": {
                    "target_text": "영수증도 주세요",
                    "gloss": "A receipt too, please",
                    "transliteration": "yeongsujeung-do juseyo",
                    "notes": "영수증 = receipt; 도 = also / too.",
                },
            },
        ],
        "debrief": {
            "strengths": [
                "You ordered a drink in Korean without switching to English.",
                "You used 주세요 to make polite requests.",
            ],
            "fix": (
                "Use 한 잔 for cups and 개 for general items; both follow "
                "the number."
            ),
            "cards": [
                {
                    "target_text": "아이스 아메리카노 한 잔 주세요",
                    "gloss": "One iced Americano, please",
                    "transliteration": "aiseu amerikano han jan juseyo",
                    "notes": "한 잔 = one cup; 주세요 = please give me.",
                },
                {
                    "target_text": "큰 사이즈로 주세요",
                    "gloss": "A large size, please",
                    "transliteration": "keun saijeu-ro juseyo",
                    "notes": "큰 = large; -로 marks the chosen option.",
                },
                {
                    "target_text": "영수증도 주세요",
                    "gloss": "A receipt too, please",
                    "transliteration": "yeongsujeung-do juseyo",
                    "notes": "영수증 = receipt; 도 = also / too.",
                },
            ],
        },
    },
    {
        "slug": "directions",
        "title": "Find the way",
        "subtitle": "Straight, left, and a quick check",
        "level": 1,
        "goal": "Ask where the bathroom or station is, understand the route, and confirm it.",
        "persona": "Passerby",
        "setting": "A sidewalk near a convenience store",
        "can_do": "I can ask for directions and repeat a simple route back.",
        "steps": [
            {
                "character_text": "네, 도와드릴까요?",
                "character_gloss": "Yes, can I help you?",
                "expected": [
                    "화장실이 어디예요?",
                    "지하철역이 어디예요?",
                    "역이 어디에 있어요?",
                ],
                "hint": "Place + 이/가 어디예요?",
                "success_note": (
                    "이/가 marks the thing you are asking about; 어디예요? "
                    "means 'where is it?'"
                ),
                "target_item": {
                    "target_text": "화장실이 어디예요?",
                    "gloss": "Where is the restroom?",
                    "transliteration": "hwajangsil-i eodiyeyo?",
                    "notes": (
                        "화장실 = restroom; 이 = subject marker; 어디예요? "
                        "= where is it?"
                    ),
                },
            },
            {
                "character_text": (
                    "여기서 쭉 가서 왼쪽으로 도세요. 그러면 바로 보여요."
                ),
                "character_gloss": (
                    "Go straight from here and turn left. Then you'll see it."
                ),
                "expected": [
                    "쭉 가서 왼쪽으로 도는 거죠?",
                    "쭉 가고 왼쪽으로 도는 거죠?",
                    "왼쪽으로 도는 거죠?",
                ],
                "hint": "Repeat the route + 는 거죠? to check.",
                "success_note": "-는 거죠? checks that you understood.",
                "target_item": {
                    "target_text": "쭉 가서 왼쪽으로 도는 거죠?",
                    "gloss": "I go straight and turn left, right?",
                    "transliteration": "jjuk gaseo oenjjok-euro doneun geojyo?",
                    "notes": (
                        "쭉 = straight; 왼쪽 = left; -는 거죠? = so I …, "
                        "right?"
                    ),
                },
            },
            {
                "character_text": (
                    "네, 맞아요. 저기 편의점 옆에 있어요."
                ),
                "character_gloss": (
                    "Yes, that's right. It's next to the convenience store "
                    "over there."
                ),
                "expected": [
                    "감사합니다. 편의점 옆이죠?",
                    "고맙습니다. 편의점 옆에 있는 거죠?",
                    "네, 감사합니다. 알겠습니다",
                ],
                "hint": "Thank the person, then confirm with 이죠?",
                "success_note": "이죠? asks 'it's …, right?' after a noun.",
                "target_item": {
                    "target_text": "감사합니다. 편의점 옆이죠?",
                    "gloss": (
                        "Thank you. It's next to the convenience store, right?"
                    ),
                    "transliteration": "gamsahamnida. pyeonuijeom yeop-ijyo?",
                    "notes": (
                        "편의점 = convenience store; 옆 = next to; 이죠? = "
                        "is it …?"
                    ),
                },
            },
        ],
        "debrief": {
            "strengths": [
                "You asked for directions in one short, polite question.",
                "You repeated the route back instead of nodding along.",
            ],
            "fix": (
                "Ask 'where is…?' with 이/가 어디예요?, then repeat the route "
                "with -는 거죠? to confirm."
            ),
            "cards": [
                {
                    "target_text": "화장실이 어디예요?",
                    "gloss": "Where is the restroom?",
                    "transliteration": "hwajangsil-i eodiyeyo?",
                    "notes": "화장실 = restroom; 어디예요? = where is it?",
                },
                {
                    "target_text": "쭉 가서 왼쪽으로 도는 거죠?",
                    "gloss": "I go straight and turn left, right?",
                    "transliteration": "jjuk gaseo oenjjok-euro doneun geojyo?",
                    "notes": "쭉 = straight; 왼쪽 = left; -는 거죠? = right?",
                },
                {
                    "target_text": "감사합니다. 편의점 옆이죠?",
                    "gloss": (
                        "Thank you. It's next to the convenience store, right?"
                    ),
                    "transliteration": "gamsahamnida. pyeonuijeom yeop-ijyo?",
                    "notes": "편의점 = convenience store; 옆 = next to.",
                },
            ],
        },
    },
    {
        "slug": "pharmacy",
        "title": "At the pharmacy",
        "subtitle": "A headache, a box of medicine, a question",
        "level": 2,
        "goal": "Explain a headache, ask for medicine, and ask how often to take it.",
        "persona": "Pharmacist",
        "setting": "A small pharmacy in a residential neighborhood",
        "can_do": "I can describe a symptom and ask about dosage in polite Korean.",
        "steps": [
            {
                "character_text": "어서 오세요, 어디가 불편하세요?",
                "character_gloss": "Welcome, what's bothering you?",
                "expected": [
                    "머리가 아파서 왔어요",
                    "두통이 있어서 약을 사러 왔어요",
                    "머리가 아파요",
                ],
                "hint": "Use -아/어서 to give the reason: 아프다 → 아파서.",
                "success_note": "-아/어서 links your symptom to why you came.",
                "target_item": {
                    "target_text": "머리가 아파서 왔어요",
                    "gloss": "I came because I have a headache.",
                    "transliteration": "meori-ga apaseo wasseoyo",
                    "notes": (
                        "머리 = head; 아파서 = because it hurts; 왔어요 = "
                        "I came."
                    ),
                },
            },
            {
                "character_text": "그럼 두통약을 드릴까요?",
                "character_gloss": "Then shall I give you a headache medicine?",
                "expected": [
                    "네, 두통약 좀 주세요",
                    "두통약 주세요",
                    "두통에 좋은 약 주세요",
                ],
                "hint": "Name the medicine + (좀) 주세요.",
                "success_note": "좀 softens a request so it does not sound demanding.",
                "target_item": {
                    "target_text": "두통약 좀 주세요",
                    "gloss": "Some headache medicine, please",
                    "transliteration": "dutongyak jom juseyo",
                    "notes": (
                        "두통 = headache; 약 = medicine; 좀 softens the "
                        "request."
                    ),
                },
            },
            {
                "character_text": "이 약은 식후에 드시면 됩니다.",
                "character_gloss": "Take this medicine after meals.",
                "expected": [
                    "하루에 몇 번 먹어요?",
                    "얼마나 자주 먹어야 돼요?",
                    "하루에 몇 번 먹으면 돼요?",
                ],
                "hint": "Ask 하루에 몇 번…? for 'how many times a day'.",
                "success_note": "하루에 몇 번 = how many times per day.",
                "target_item": {
                    "target_text": "하루에 몇 번 먹어요?",
                    "gloss": "How many times a day do I take it?",
                    "transliteration": "haru-e myeot beon meogeoyo?",
                    "notes": (
                        "하루 = one day; 에 = per; 몇 번 = how many times; "
                        "먹어요 = I eat / take."
                    ),
                },
            },
        ],
        "debrief": {
            "strengths": [
                "You explained your symptom in Korean.",
                "You asked a follow-up question about how often to take the medicine.",
            ],
            "fix": (
                "Give the reason first with -아/어서 (아프다 → 아파서) instead "
                "of making two separate sentences."
            ),
            "cards": [
                {
                    "target_text": "머리가 아파서 왔어요",
                    "gloss": "I came because I have a headache.",
                    "transliteration": "meori-ga apaseo wasseoyo",
                    "notes": "머리 = head; 아파서 = because it hurts.",
                },
                {
                    "target_text": "두통약 좀 주세요",
                    "gloss": "Some headache medicine, please",
                    "transliteration": "dutongyak jom juseyo",
                    "notes": "두통 = headache; 좀 softens the request.",
                },
                {
                    "target_text": "하루에 몇 번 먹어요?",
                    "gloss": "How many times a day do I take it?",
                    "transliteration": "haru-e myeot beon meogeoyo?",
                    "notes": "하루 = one day; 몇 번 = how many times.",
                },
            ],
        },
    },
    {
        "slug": "workplace-intro",
        "title": "First day at work",
        "subtitle": "Meet the team, find your desk",
        "level": 2,
        "goal": "Greet a colleague, say your role, and ask who to go to for help.",
        "persona": "Colleague",
        "setting": "An office kitchen on your first morning",
        "can_do": "I can introduce myself and ask a practical question in formal Korean.",
        "steps": [
            {
                "character_text": (
                    "안녕하세요, 처음 오셨죠? 저는 마케팅팀 김민수입니다."
                ),
                "character_gloss": (
                    "Hello, you're new here, right? I'm Kim Minsu from the "
                    "marketing team."
                ),
                "expected": [
                    "안녕하세요, 새로 온 알렉스입니다",
                    "처음 뵙겠습니다, 알렉스입니다",
                    "안녕하세요, 저는 알렉스입니다",
                ],
                "hint": "Greet, give your name, and add 잘 부탁드립니다 if you like.",
                "success_note": (
                    "새로 온 = newly arrived; 처음 뵙겠습니다 is a formal "
                    "first-meeting greeting."
                ),
                "target_item": {
                    "target_text": "안녕하세요, 새로 온 알렉스입니다",
                    "gloss": "Hello, I'm Alex, the new hire.",
                    "transliteration": "annyeonghaseyo, saero on allekseus-imnida",
                    "notes": (
                        "새로 온 = newly arrived; 입니다 is the formal copula."
                    ),
                },
            },
            {
                "character_text": "알렉스 씨는 어느 팀에서 일하세요?",
                "character_gloss": "Which team do you work on, Alex?",
                "expected": [
                    "저는 디자인팀에서 일합니다",
                    "디자인팀에서 일하고 있습니다",
                    "저는 개발팀 신입 사원입니다",
                ],
                "hint": "Team + 에서 일합니다.",
                "success_note": "에서 marks the place where an action happens.",
                "target_item": {
                    "target_text": "저는 디자인팀에서 일합니다",
                    "gloss": "I work on the design team.",
                    "transliteration": "jeoneun dijain-tim-eseo ilhamnida",
                    "notes": (
                        "에서 = at / in (workplace); 일합니다 = I work "
                        "(formal)."
                    ),
                },
            },
            {
                "character_text": "자리는 저쪽 빈자리에 앉으시면 됩니다.",
                "character_gloss": (
                    "You can sit at an empty desk over there."
                ),
                "expected": [
                    "업무 관련 질문은 누구에게 하면 됩니까?",
                    "궁금한 것은 누구에게 물어보면 됩니까?",
                    "일 관련해서는 누구에게 물어보면 됩니까?",
                ],
                "hint": "Person + 에게 물어보면 됩니까?",
                "success_note": (
                    "에게 marks the person you ask; -(으)면 됩니까? asks what "
                    "you should do."
                ),
                "target_item": {
                    "target_text": "업무 관련 질문은 누구에게 하면 됩니까?",
                    "gloss": (
                        "Who should I ask if I have a work-related question?"
                    ),
                    "transliteration": (
                        "eommu gwanryeon jilmun-eun nugu-ege hamyeon "
                        "doemnikka?"
                    ),
                    "notes": (
                        "업무 = work duties; 에게 = to (a person); 하면 "
                        "됩니까? = should I do?"
                    ),
                },
            },
        ],
        "debrief": {
            "strengths": [
                "You introduced yourself in formal workplace Korean.",
                "You asked who to go to instead of guessing.",
            ],
            "fix": (
                "Stay in 합니다체 at work: use -입니다 and -합니다 instead of "
                "mixing in 해요체 endings."
            ),
            "cards": [
                {
                    "target_text": "안녕하세요, 새로 온 알렉스입니다",
                    "gloss": "Hello, I'm Alex, the new hire.",
                    "transliteration": "annyeonghaseyo, saero on allekseus-imnida",
                    "notes": "새로 온 = newly arrived; 입니다 = formal copula.",
                },
                {
                    "target_text": "저는 디자인팀에서 일합니다",
                    "gloss": "I work on the design team.",
                    "transliteration": "jeoneun dijain-tim-eseo ilhamnida",
                    "notes": "에서 = at / in (workplace); 일합니다 = I work.",
                },
                {
                    "target_text": "업무 관련 질문은 누구에게 하면 됩니까?",
                    "gloss": (
                        "Who should I ask if I have a work-related question?"
                    ),
                    "transliteration": (
                        "eommu gwanryeon jilmun-eun nugu-ege hamyeon "
                        "doemnikka?"
                    ),
                    "notes": "업무 = work duties; 에게 = to (a person).",
                },
            ],
        },
    },
]
# fmt: on
