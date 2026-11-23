"""Starter Amharic content: a survival deck and a fidel bootcamp.

This is deliberately small and hand-curated. It is the first non-Korean pack,
and it exercises the language core: every item gets a Ge'ez form, a Latin
transliteration, an English gloss, and membership in the `am-core` deck.
"""

# (fidel, transliteration, english, item_type, level, note)
AMHARIC_ITEMS = [
    # Greetings and politeness
    ("ሰላም", "selam", "Hello / peace", "chunk", 1, "The everyday greeting; also means peace."),
    ("እንደምን ነህ?", "endemin neh?", "How are you? (to a man)", "chunk", 1, None),
    ("እንደምን ነሽ?", "endemin nesh?", "How are you? (to a woman)", "chunk", 1, None),
    ("ደህና ነኝ", "dehna negn", "I am fine", "chunk", 1, None),
    ("አመሰግናለሁ", "ameseginalehu", "Thank you", "chunk", 1, None),
    ("እባክህ", "ebakih", "Please (to a man)", "chunk", 1, None),
    ("እባክሽ", "ebakish", "Please (to a woman)", "chunk", 1, None),
    ("አዎ", "awo", "Yes", "lexeme", 1, None),
    ("አይ", "ay", "No", "lexeme", 1, None),
    ("ይቅርታ", "yikirta", "Sorry / excuse me", "chunk", 1, None),
    ("ደህና ሁን", "dehna hun", "Goodbye (to a man)", "chunk", 1, None),
    ("ደህና ሁኚ", "dehna huni", "Goodbye (to a woman)", "chunk", 1, None),
    ("ስሜ ማሪያም ነው", "sime Mariam new", "My name is Mariam", "sentence", 1, "Replace Mariam with your name."),
    ("ስምህ ማን ነው?", "simih man new?", "What is your name? (to a man)", "chunk", 1, None),
    ("እንኳን ደህና መጣህ", "enkuan dehna metah", "Welcome (to a man)", "chunk", 2, None),
    ("እንኳን ደህና መጣሽ", "enkuan dehna metash", "Welcome (to a woman)", "chunk", 2, None),
    # Food and drink
    ("ውሃ", "wiha", "Water", "lexeme", 1, None),
    ("ቡና", "buna", "Coffee", "lexeme", 1, "Ethiopian coffee ceremony: ጀበና (jebena) is the pot."),
    ("ሻይ", "shay", "Tea", "lexeme", 1, None),
    ("ዳቦ", "dabo", "Bread", "lexeme", 1, None),
    ("እንጀራ", "injera", "Injera (flatbread)", "lexeme", 1, None),
    ("ምግብ", "migib", "Food / meal", "lexeme", 1, None),
    ("ስጋ", "siga", "Meat", "lexeme", 1, None),
    ("እንቁላል", "enkulal", "Egg", "lexeme", 1, None),
    ("ወተት", "wetet", "Milk", "lexeme", 1, None),
    ("ስኳር", "sukwar", "Sugar", "lexeme", 1, None),
    ("ጨው", "chew", "Salt", "lexeme", 1, None),
    ("ቡና አንድ ኩባያ እባክህ", "buna and kubaya ebakih", "One cup of coffee, please", "sentence", 2, "ኩባያ = cup."),
    ("ውሃ እፈልጋለሁ", "wiha efelgalehu", "I want water", "sentence", 2, None),
    ("በጣም ጣፋጭ ነው", "betam tafach new", "It is very delicious", "sentence", 2, None),
    # Market and money
    ("ብር", "birr", "Birr (Ethiopian currency)", "lexeme", 1, None),
    ("ስንት ነው?", "sint new?", "How much is it?", "chunk", 1, None),
    ("ውድ ነው", "wid new", "It is expensive", "chunk", 1, None),
    ("ርካሽ ነው", "rikash new", "It is cheap", "chunk", 1, None),
    ("ገበያ", "gebya", "Market", "lexeme", 1, None),
    ("ሱቅ", "suq", "Shop", "lexeme", 1, None),
    ("ይህን እፈልጋለሁ", "yihin efelgalehu", "I want this one", "sentence", 2, None),
    # People and places
    ("ቤት", "bet", "House", "lexeme", 1, None),
    ("ትምህርት ቤት", "timhirt bet", "School", "lexeme", 1, "Literally 'place of learning'."),
    ("ሆስፒታል", "hospital", "Hospital", "lexeme", 1, None),
    ("መንገድ", "menged", "Road / street", "lexeme", 1, None),
    ("ቤተሰብ", "beteseb", "Family", "lexeme", 1, None),
    ("እናት", "enat", "Mother", "lexeme", 1, None),
    ("አባት", "abat", "Father", "lexeme", 1, None),
    ("ወንድም", "wendim", "Brother", "lexeme", 1, None),
    ("እህት", "ihit", "Sister", "lexeme", 1, None),
    ("ልጅ", "lij", "Child", "lexeme", 1, None),
    ("ጓደኛ", "gwadenya", "Friend", "lexeme", 1, None),
    # Directions
    ("ወደ ፊት", "wede fit", "Straight ahead", "chunk", 2, None),
    ("ግራ", "gira", "Left", "lexeme", 1, None),
    ("ቀኝ", "qeny", "Right", "lexeme", 1, None),
    ("የት ነው?", "yet new?", "Where is it?", "chunk", 1, None),
    ("ታክሲ", "taxi", "Taxi", "lexeme", 1, None),
    ("መኪና", "mekina", "Car", "lexeme", 1, None),
    # Numbers
    ("አንድ", "and", "One", "lexeme", 1, None),
    ("ሁለት", "hulet", "Two", "lexeme", 1, None),
    ("ሶስት", "sost", "Three", "lexeme", 1, None),
    ("አራት", "arat", "Four", "lexeme", 1, None),
    ("አምስት", "amist", "Five", "lexeme", 1, None),
    ("ስድስት", "sidist", "Six", "lexeme", 1, None),
    ("ሰባት", "sebat", "Seven", "lexeme", 1, None),
    ("ስምንት", "simint", "Eight", "lexeme", 1, None),
    ("ዘጠኝ", "zetegn", "Nine", "lexeme", 1, None),
    ("አስር", "asir", "Ten", "lexeme", 1, None),
]

# Ge'ez fidel: 33 consonant families. Each family has seven vowel orders.
FIDEL_FAMILIES = [
    ("ሀ", ["ሀ", "ሁ", "ሂ", "ሃ", "ሄ", "ህ", "ሆ"], "h"),
    ("ለ", ["ለ", "ሉ", "ሊ", "ላ", "ሌ", "ል", "ሎ"], "l"),
    ("ሐ", ["ሐ", "ሑ", "ሒ", "ሓ", "ሔ", "ሕ", "ሖ"], "ḥ"),
    ("መ", ["መ", "ሙ", "ሚ", "ማ", "ሜ", "ም", "ሞ"], "m"),
    ("ሠ", ["ሠ", "ሡ", "ሢ", "ሣ", "ሤ", "ሥ", "ሦ"], "ś"),
    ("ረ", ["ረ", "ሩ", "ሪ", "ራ", "ሬ", "ር", "ሮ"], "r"),
    ("ሰ", ["ሰ", "ሱ", "ሲ", "ሳ", "ሴ", "ስ", "ሶ"], "s"),
    ("ሸ", ["ሸ", "ሹ", "ሺ", "ሻ", "ሼ", "ሽ", "ሾ"], "š"),
    ("ቀ", ["ቀ", "ቁ", "ቂ", "ቃ", "ቄ", "ቅ", "ቆ"], "q"),
    ("በ", ["በ", "ቡ", "ቢ", "ባ", "ቤ", "ብ", "ቦ"], "b"),
    ("ተ", ["ተ", "ቱ", "ቲ", "ታ", "ቴ", "ት", "ቶ"], "t"),
    ("ቸ", ["ቸ", "ቹ", "ቺ", "ቻ", "ቼ", "ች", "ቾ"], "č"),
    ("ኀ", ["ኀ", "ኁ", "ኂ", "ኃ", "ኄ", "ኅ", "ኆ"], "ḫ"),
    ("ነ", ["ነ", "ኑ", "ኒ", "ና", "ኔ", "ን", "ኖ"], "n"),
    ("ኘ", ["ኘ", "ኙ", "ኚ", "ኛ", "ኜ", "ኝ", "ኞ"], "ñ"),
    ("አ", ["አ", "ኡ", "ኢ", "ኣ", "ኤ", "እ", "ኦ"], "ʼ"),
    ("ከ", ["ከ", "ኩ", "ኪ", "ካ", "ኬ", "ክ", "ኮ"], "k"),
    ("ኸ", ["ኸ", "ኹ", "ኺ", "ኻ", "ኼ", "ኽ", "ኾ"], "x"),
    ("ወ", ["ወ", "ዉ", "ዊ", "ዋ", "ዌ", "ው", "ዎ"], "w"),
    ("ዐ", ["ዐ", "ዑ", "ዒ", "ዓ", "ዔ", "ዕ", "ዖ"], "ʿ"),
    ("ዘ", ["ዘ", "ዙ", "ዚ", "ዛ", "ዜ", "ዝ", "ዞ"], "z"),
    ("ዠ", ["ዠ", "ዡ", "ዢ", "ዣ", "ዤ", "ዥ", "ዦ"], "ž"),
    ("የ", ["የ", "ዩ", "ዪ", "ያ", "ዬ", "ይ", "ዮ"], "y"),
    ("ደ", ["ደ", "ዱ", "ዲ", "ዳ", "ዴ", "ድ", "ዶ"], "d"),
    ("ጀ", ["ጀ", "ጁ", "ጂ", "ጃ", "ጄ", "ጅ", "ጆ"], "j"),
    ("ገ", ["ገ", "ጉ", "ጊ", "ጋ", "ጌ", "ግ", "ጎ"], "g"),
    ("ጠ", ["ጠ", "ጡ", "ጢ", "ጣ", "ጤ", "ጥ", "ጦ"], "ṭ"),
    ("ጨ", ["ጨ", "ጩ", "ጪ", "ጫ", "ጬ", "ጭ", "ጮ"], "č̣"),
    ("ጰ", ["ጰ", "ጱ", "ጲ", "ጳ", "ጴ", "ጵ", "ጶ"], "p̣"),
    ("ጸ", ["ጸ", "ጹ", "ጺ", "ጻ", "ጼ", "ጽ", "ጾ"], "ṣ"),
    ("ፀ", ["ፀ", "ፁ", "ፂ", "ፃ", "ፄ", "ፅ", "ፆ"], "ḍ"),
    ("ፈ", ["ፈ", "ፉ", "ፊ", "ፋ", "ፌ", "ፍ", "ፎ"], "f"),
    ("ፐ", ["ፐ", "ፑ", "ፒ", "ፓ", "ፔ", "ፕ", "ፖ"], "p"),
]

VOWEL_ORDERS = [
    ("1st", "ä", "as in 'father'"),
    ("2nd", "u", "as in 'boot'"),
    ("3rd", "i", "as in 'feet'"),
    ("4th", "a", "as in 'cat', longer"),
    ("5th", "e", "as in 'bed'"),
    ("6th", "ə", "a short central vowel"),
    ("7th", "o", "as in 'go'"),
]

FIDEL_LESSONS = [
    {
        "slug": "fidel-1",
        "title": "Meet the fidel",
        "summary": "One consonant family, seven vowel orders. Learn how the grid works.",
        "families": [0, 1, 3],
    },
    {
        "slug": "fidel-2",
        "title": "The h and s families",
        "summary": "ሀ, ሐ, ኀ and ሰ, ሠ, ጸ look alike; the vowel order is what changes.",
        "families": [0, 2, 12, 6, 4, 29],
    },
    {
        "slug": "fidel-3",
        "title": "Everyday consonants",
        "summary": "በ, ተ, ነ, ደ, ዘ — the shapes behind most Amharic words.",
        "families": [9, 10, 13, 23, 20],
    },
    {
        "slug": "fidel-4",
        "title": "Ejectives and hush sounds",
        "summary": "ቀ, ጠ, ጨ, ጰ, ጸ — sharp sounds with no English equivalent.",
        "families": [8, 26, 27, 28, 29],
    },
    {
        "slug": "fidel-5",
        "title": "Rounded and glide families",
        "summary": "ረ, ለ, ወ, የ — the families you will see on every menu.",
        "families": [5, 1, 18, 22],
    },
    {
        "slug": "fidel-6",
        "title": "The last families",
        "summary": "ከ, ገ, ፈ, ፐ, ቸ, ጠ and the rest of the grid.",
        "families": [16, 25, 9, 31, 11, 17],
    },
]


def fidel_lessons():
    """Return lessons with resolved family and drill data."""
    lessons = []
    for lesson in FIDEL_LESSONS:
        families = [FIDEL_FAMILIES[index] for index in lesson["families"]]
        drills = [
            {
                "glyph": forms[order],
                "roman": f"{label}{VOWEL_ORDERS[order][1]}",
            }
            for _base, forms, label in families
            for order in range(7)
        ]
        lessons.append({**lesson, "families": families, "drills": drills})
    return lessons
