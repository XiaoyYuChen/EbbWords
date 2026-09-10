# -*- coding: utf-8 -*-
"""Parse KET / PET / PEP vocab and emit a self-contained index.html."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "data" / "ket.txt"
TPL = ROOT / "template.html"
OUT = ROOT / "index.html"
RAW = ROOT / "data" / "raw"

POS_TOKEN = r"(?:phr\s*v|n\s*pl|art|adj|adv|prep|pron|det|conj|num|exclaim|aux|n|v)"
POS_INNER = rf"{POS_TOKEN}(?:\s*(?:&|and|,)\s*{POS_TOKEN})*"
POS_RE = re.compile(rf"\(({POS_INNER})\)", re.I)
CN_RE = re.compile(r"[\u4e00-\u9fff]")

GROUPS = [
    ("family", "家庭人物", "#e07a5f"),
    ("body", "身体外貌", "#c05621"),
    ("clothes", "服装配饰", "#9b6b9e"),
    ("food", "食物饮料", "#dd6b20"),
    ("home", "家居生活", "#2f855a"),
    ("school", "学校学习", "#2b6cb0"),
    ("work", "工作职业", "#4a5568"),
    ("travel", "交通旅行", "#3182ce"),
    ("places", "城镇场所", "#6b46c1"),
    ("sport", "运动爱好", "#38a169"),
    ("fun", "娱乐媒体", "#d53f8c"),
    ("nature", "天气自然", "#319795"),
    ("animals", "动物宠物", "#b7791f"),
    ("time", "时间日期", "#805ad5"),
    ("number", "数字度量", "#4c51bf"),
    ("color", "颜色材质", "#e53e3e"),
    ("shop", "购物金钱", "#d69e2e"),
    ("health", "健康医疗", "#c53030"),
    ("tech", "科技通讯", "#2c7a7b"),
    ("social", "社交用语", "#b83280"),
    ("feel", "情感描述", "#dd6b20"),
    ("action", "常用动词", "#2b6cb0"),
    ("place", "方位位置", "#718096"),
    ("grammar", "功能语法", "#4a5568"),
    ("other", "其他", "#a0aec0"),
]

# First match wins. More specific topics listed first.
TOPIC_WORDS = {
    "animals": """
        animal bear bird cat cow dog dolphin elephant horse insect
        lion monkey mouse pet zoo
    """,
    "food": """
        apple banana barbecue biscuit boil bottle bowl bread breakfast burger
        butter cafe café cake carrot cheese chicken chips chocolate coffee
        cook cooker cream cup dinner dish drink eat egg food fork fridge fried
        fruit fry grape grill grilled hungry ice "ice cream" jam juice knife
        lemon lemonade lunch meal meat menu milk "mineral water" omelette onion
        pasta pepper picnic pizza plate potato restaurant rice roast salad
        salt sandwich snack soup spoon steak sugar supper sweet tea thirsty
        tomato vegetable waiter waitress "wash up" water glass slice fish orange
    """,
    "clothes": """
        belt blouse boot clothes coat dress hat jacket jeans pocket raincoat
        shirt shoe shorts skirt sock suit sweater tights trainers trousers
        t-shirt uniform wear "put on" "try on" size leather wool
        bag umbrella comb watch
    """,
    "family": """
        adult aunt baby boy brother child cousin dad daddy daughter family
        father friend girl grandchild granddad grandad granddaughter
        grandfather grandma grandmother grandpa grandparent grandson guest
        husband man married miss mother mr mrs ms mum mummy name neighbour
        parent people person sister son surname teenager uncle wife woman
        "grow up" born life classmate colleague age king queen
        "pen-friend" nationality
    """,
    "body": """
        arm back blond blonde body ear face fair fat foot glasses hair hand
        head heart leg mouth neck nose stomach thin tooth toothbrush tall
        pretty beautiful hairdryer
    """,
    "health": """
        accident ambulance careful chemist cold danger dangerous dead dentist
        die doctor fall hospital hurt ill insurance medicine nurse pain
        pharmacy sick temperature terrible tired appointment
        "police officer"
    """,
    "school": """
        beginner class classroom college course dictionary diploma exam
        examination example homework language learn lesson library practise
        practice project pupil question school spell student studies study
        subject teach test university write book pen pencil page paper
        sentence word level mistake remember understand know read draw
        drawing beginner bookshelf bookshop board diary difference
        envelope form instructions letter information
    """,
    "work": """
        boss business businessman businesswoman company customer department
        earn engineer factory job journalist manager mechanic meeting
        occupation office receptionist secretary staff work assistant
        "shop assistant" hairdresser actor artist chemist occupation
        member pilot "police officer"
    """,
    "sport": """
        ball baseball basketball climb competition football game golf hockey
        jump match play race run ski sport stadium swim team
        tennis table-tennis volleyball win pool "sports centre"
    """,
    "fun": """
        adventure art artist band camera cassette cd cinema concert dance
        disco drum dvd exhibition film fun guitar hobby magazine music
        newspaper opera photo photograph photography piano picture pop radio
        show sing song story television theatre toy video website programme
        congratulations party activity advertisement conversation news poster
        present prize "cassette player" "cassette recorder" "DVD player"
        "video recorder"
    """,
    "travel": """
        aeroplane airport bicycle bike boat brake bridge bus car catch coach
        crossing crossroads drive engine flight fly garage helicopter journey
        lorry motorway passenger petrol plane platform railway ride road
        roundabout ship station taxi ticket traffic train tram trip tyre
        underground wheel adventure camp campsite hotel luggage map passport
        suitcase tent tour tourist travel visit visitor holiday holidays
        guidebook guest-house island delay pack return postcard seat guide
        licence "bus station" "bus stop" "driving licence" "petrol station"
        "police car" "traffic lights" "tour guide" "travel agent"
        "tourist information centre" "get off" "get on" "take off"
    """,
    "home": """
        apartment bath bathroom bed bedroom blanket chair clock cupboard desk
        door downstairs flat floor furniture garden gate hall heating house
        home indoor indoors key kitchen lamp lift mirror pillow roof room
        shelf shower sofa stairs table toilet towel upstairs wall window soap
        shampoo tidy cooker fridge sheet address gas oil box
        "dining room" "living room" "sitting room"
    """,
    "places": """
        bank beach bookshop building castle cathedral centre church city club
        corner country countryside entrance exit farm field forest hill lake
        market mountain museum park path place river ruin sea shop square
        store street supermarket town village world canal garage hospital
        library restaurant school university factory office station
        airport crowd police "police station" "post office"
    """,
    "nature": """
        air autumn beach cloud cloudy countryside dry field fire flower fog
        foggy forest grass grow hill ice island lake moon mountain plant
        rain river rock sea sky snow spring star storm summer sun sunny
        thunderstorm tree warm weather wet wind windy         winter wood space
    """,
    "shop": """
        bill buy cash cent cheap cheque cost customer dollar expensive euro
        market money pence penny pound price purse sale sell shop store
        supermarket wallet change newsagent stamp card "credit card"
        "shop assistant" "pay for"
    """,
    "tech": """
        call camera cassette cd click computer dvd email internet laptop
        message mobile phone radio telephone television video website machine
        electricity electric "laptop (computer)" "mobile (phone)"
    """,
    "time": """
        a.m. afternoon afterwards ago already always birthday century daily
        date day early evening hour later midnight minute moment month
        monthly morning night noon now o'clock once p.m. past quarter
        second sometimes soon then time today tomorrow tonight twice week
        weekday weekend weekly year yesterday yet ever never often during
        since until till when while first last next today
    """,
    "number": """
        add bit centimetre degree double extra few gram gramme half kilo
        kilogram kilogramme kilometre large less litre little lot lots many
        metre mile million more most much number pair per piece quarter
        several size small total zero one first second whole
    """,
    "color": """
        black blue brown colour dark gold green grey orange pink purple red
        silver white yellow light fair blond blonde plastic paper glass
        leather wool wood gold silver
    """,
    "social": """
        alright cheers congratulations goodbye hallo hello how please pardon
        sorry thank welcome yes no ok okay excuse dear wishes sincerely "all right"
    """,
    "place": """
        about above across among around round at behind below between by down
        from in inside into near of off on opposite out outdoor outdoors
        outside over through to under up with without here there where left
        right middle top bottom front side way far "in front of" "next to"
        "straight on" "close to" east west north south
    """,
    "grammar": """
        a an all also another any anybody anyone anything anyway anywhere
        as "as well" "as well as" both but because can could do each else
        enough even every everybody everyone everything everywhere except
        for he her hers herself him himself his i if it its itself just
        like me mine must myself not of or our ours ourselves own shall
        she should so some somebody someone something still such than
        that the their theirs them themselves these they this those too
        we what which who whose why will would you your yours yourself
        "a few" "a lot" thing group part type line problem idea "no one"
        "at all" somewhere nowhere
    """,
    "feel": """
        able afraid angry bad beautiful boring busy certain clever
        comfortable correct crowded different dirty easy empty excellent
        famous favourite fine free fresh friendly funny glad good great
        happy hard heavy high important interested interesting kind late
        long loud lovely lucky modern nice noisy old only open pleasant
        poor popular possible pretty quiet quick ready real rich right sad
        safe same short slow soft special strange strong sure surprised
        useful usual well wonderful wrong young new full closed clear
        cheap expensive hot cold warm wet dry hungry thirsty ill sick
        national international foreign single special real really
        actually certainly perhaps probably quite rather luck pity
        surprise trouble
    """,
    "action": """
        add agree arrive ask become begin believe belong break bring build
        burn buy call carry catch change check choose clean climb close come
        cost cross cry cut dance decide delay describe die do draw drink drive
        eat end enjoy explain fail fall feel fill find finish fly follow
        forget fry get give go grow happen hate have hear help hit hope hurry
        hurt improve invite join jump keep know laugh learn leave let like
        listen live look lose love make matter mean meet mind move need open
        pack paint park pass pay play point post prefer pull push put read
        remember rent repair rest return ride run say see sell send shampoo
        shout show shut sing sit ski sleep smoke snow sound speak spell spend
        stand start stay steal stop study suppose swim take talk teach tell
        thank think throw tidy try turn understand use visit wait walk want
        wash watch wear welcome win work write "fill in" "get off" "get on"
        "get up" "go out" "grow up" "have got" "have to" "lie down" "look after"
        "look at" "look for" "look out" "pay for" "put on" "sit down" "take off"
        "try on" "turn off" "turn on" "wake up" "wash up" "write down"
    """,
}


def parse_entry_line(line: str):
    s = str(line or "").replace("\ufeff", "")
    s = re.sub(r"\s+", " ", s).strip()
    if not s or s.startswith("#") or s.startswith("//"):
        return None
    if re.fullmatch(r"[A-Z]", s):
        return None

    headword = ""
    pos = ""
    phonetic = ""
    meaning = ""

    pos_match = POS_RE.search(s)
    if pos_match:
        idx = pos_match.start()
        before = s[:idx].strip()
        if before:
            headword = before
            pos = re.sub(r"\s+", " ", pos_match.group(1)).strip()
            s = s[pos_match.end() :].strip()

    ipas = []
    while s:
        stripped = re.sub(r"^[；;/,]\s*", "", s)
        if stripped == s and ipas:
            break
        s = stripped
        m = re.match(r"^\[?\s*([^\]]+?)\s*\]\s*", s)
        if not m:
            break
        piece = re.sub(r"\s+", " ", m.group(1)).strip()
        if piece:
            ipas.append(piece)
        s = s[m.end() :].strip()
    phonetic = "; ".join(ipas)

    if not headword:
        cn = CN_RE.search(s)
        if cn and cn.start() > 0:
            headword = s[: cn.start()].strip()
            meaning = s[cn.start() :].strip()
        else:
            headword = s
            meaning = ""
    else:
        meaning = s

    headword = headword.strip()
    if not headword:
        return None
    return {
        "headword": headword,
        "pos": pos.strip(),
        "phonetic": phonetic.strip(),
        "meaning": meaning.strip(),
    }


def variants(head: str) -> set[str]:
    raw = (head or "").lower().strip()
    raw = raw.rstrip("!.")
    out: set[str] = set()

    def add(x: str):
        x = re.sub(r"\s+", " ", x).strip(" ,/")
        if not x:
            return
        out.add(x)
        out.add(x.replace("-", " "))
        out.add(x.replace(" ", ""))
        out.add(x.replace(".", ""))

    add(raw)
    for part in re.split(r"[/,]", raw):
        add(part)
    included = re.sub(r"\(([a-z]+)\)", r"\1", raw)
    excluded = re.sub(r"\([^)]*\)", "", raw)
    add(included)
    add(excluded)
    # dad(dy) -> daddy
    m = re.search(r"([a-z]+)\(([a-z]+)\)", raw)
    if m:
        add(m.group(1) + m.group(2))
    return {x for x in out if x}


def audio_key(head: str) -> str:
    s = (head or "").strip().rstrip("!")
    s = s.replace("(a)", "a").replace("(d)", "d")
    s = re.sub(r"\([^)]*\)", "", s)
    s = s.split("/")[0].split(",")[0]
    s = s.replace("£", "").replace(".", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s or (head or "").strip()


def letter_of(head: str) -> str:
    ch = re.sub(r"[^A-Za-z]", "", head or "")[:1].upper()
    return ch if ch else "#"


def pos_bucket(pos: str) -> str:
    p = (pos or "").lower()
    if "phr" in p:
        return "短语动词"
    if "exclaim" in p:
        return "感叹"
    if "n pl" in p:
        return "名词复数"
    if re.search(r"\bn\b", p):
        if "v" in p and not p.startswith("n"):
            return "名/动"
        return "名词"
    if re.search(r"\bv\b", p) or p.startswith("v"):
        return "动词"
    if "adj" in p:
        return "形容词"
    if "adv" in p:
        return "副词"
    if "prep" in p:
        return "介词"
    if "pron" in p:
        return "代词"
    if "det" in p:
        return "限定词"
    if "conj" in p:
        return "连词"
    if "art" in p:
        return "冠词"
    if "num" in p:
        return "数词"
    return "其他词性"


def topic_keys(raw: str) -> set[str]:
    keys = set()
    phrases = re.findall(r'"([^"]+)"', raw)
    rest = re.sub(r'"[^"]+"', " ", raw)
    for w in rest.split() + phrases:
        keys |= variants(w)
    return keys


def compile_topic_sets():
    return [(gid, topic_keys(TOPIC_WORDS.get(gid, ""))) for gid, _n, _c in GROUPS]


def assign_topic(word: dict, compiled) -> str:
    skip = ("feel", "action", "grammar", "other")
    full = variants(word["headword"])
    for gid, bag in compiled:
        if gid in skip:
            continue
        if full & bag:
            return gid
    pos = (word["pos"] or "").lower()
    for gid in ("place", "grammar", "feel", "action"):
        bag = next(b for g, b in compiled if g == gid)
        if full & bag:
            return gid
    if any(x in pos for x in ("prep", "conj", "det", "pron", "art")):
        return "grammar"
    if "exclaim" in pos:
        return "social"
    if "phr v" in pos or pos.startswith("v") or re.search(r"\bv\b", pos):
        return "action"
    if "adj" in pos:
        return "feel"
    if "adv" in pos:
        return "time"
    return "other"


UNIT_COLORS = [
    "#e07a5f", "#2b6cb0", "#2f855a", "#6b46c1", "#dd6b20", "#c53030",
    "#3182ce", "#d53f8c", "#805ad5", "#319795", "#4a5568", "#b7791f",
    "#9b6b9e", "#38a169",
]

PET_POS_RE = re.compile(
    r"^(?P<pos>(?:phr\s*v|n\s*pl|art|adj|adv|prep|pron|det|conj|num|exclam|exclaim|aux|n|v|phr)"
    r"(?:\s*(?:&|and|,|/)\s*(?:phr\s*v|n\s*pl|art|adj|adv|prep|pron|det|conj|num|exclam|exclaim|aux|n|v|phr))*)\.?\s+",
    re.I,
)

# Youdao / qwerty-learner PEP books, split by first word of each unit (textbook order).
PEP_YOUDAO = [
    {
        "file": "PEPXiaoXue4_1_T.json",
        "grade": 4,
        "term": 1,
        "term_name": "上册",
        "name": "PEP 四年级上册",
        "short": "pep4a",
        "units": [
            ("classroom", "Unit 1 My classroom"),
            ("schoolbag", "Unit 2 My schoolbag"),
            ("cute", "Unit 3 My friends"),
            ("bedroom", "Unit 4 My home"),
            ("beef", "Unit 5 Dinner's ready"),
            ("parents", "Unit 6 Meet my family!"),
        ],
    },
    {
        "file": "PEPXiaoXue4_2_T.json",
        "grade": 4,
        "term": 2,
        "term_name": "下册",
        "name": "PEP 四年级下册",
        "short": "pep4b",
        "units": [
            ("first floor", "Unit 1 My school"),
            ("breakfast", "Unit 2 What time is it?"),
            ("cold", "Unit 3 Weather"),
            ("tomato", "Unit 4 At the farm"),
            ("clothes", "Unit 5 My clothes"),
            ("pretty", "Unit 6 Shopping"),
        ],
    },
    {
        "file": "PEPXiaoXue5_1_T.json",
        "grade": 5,
        "term": 1,
        "term_name": "上册",
        "name": "PEP 五年级上册",
        "short": "pep5a",
        "units": [
            ("old", "Unit 1 What's he like?"),
            ("Monday", "Unit 2 My week"),
            ("sandwich", "Unit 3 What would you like?"),
            ("sing", "Unit 4 What can you do?"),
            ("clock", "Unit 5 There is a big bed"),
            ("nature", "Unit 6 In a nature park"),
        ],
    },
    {
        "file": "PEPXiaoXue5_2_T.json",
        "grade": 5,
        "term": 2,
        "term_name": "下册",
        "name": "PEP 五年级下册",
        "short": "pep5b",
        "units": [
            ("eat breakfast", "Unit 1 My day"),
            ("spring", "Unit 2 My favourite season"),
            ("January", "Unit 3 My school calendar"),
            ("first", "Unit 4 When is the art show?"),
            ("climbing", "Unit 5 Whose dog is it?"),
            ("keep", "Unit 6 Work quietly!"),
        ],
    },
    {
        "file": "PEPXiaoXue6_1_T.json",
        "grade": 6,
        "term": 1,
        "term_name": "上册",
        "name": "PEP 六年级上册",
        "short": "pep6a",
        "units": [
            ("science", "Unit 1 How can I get there?"),
            ("on foot", "Unit 2 Ways to go to school"),
            ("visit", "Unit 3 My weekend"),
            ("pen pal", "Unit 4 I have a pen pal"),
            ("factory", "Unit 5 What does he do?"),
            ("angry", "Unit 6 How do you feel?"),
        ],
    },
    {
        "file": "PEPXiaoXue6_2_T.json",
        "grade": 6,
        "term": 2,
        "term_name": "下册",
        "name": "PEP 六年级下册",
        "short": "pep6b",
        "units": [
            ("younger", "Unit 1 How tall are you?"),
            ("cleaned", "Unit 2 Last weekend"),
            ("went", "Unit 3 Where did you go?"),
            ("dining hall", "Unit 4 Then and now"),
        ],
    },
    {
        "file": "PEPChuZhong7_1_T.json",
        "grade": 7,
        "term": 1,
        "term_name": "上册",
        "name": "PEP 七年级上册",
        "short": "pep7a",
        "units": [
            ("good", "Starter 1 Good morning!"),
            ("what", "Starter 2 What's this in English?"),
            ("color", "Starter 3 What color is it?"),
            ("my", "Unit 1 My name's Gina."),
            ("sister", "Unit 2 This is my sister."),
            ("pencil", "Unit 3 Is this your pencil?"),
            ("where", "Unit 4 Where's my schoolbag?"),
            ("tennis", "Unit 5 Do you have a soccer ball?"),
            ("banana", "Unit 6 Do you like bananas?"),
            ("sock", "Unit 7 How much are these socks?"),
            ("when", "Unit 8 When is your birthday?"),
            ("favorite", "Unit 9 My favorite subject is science."),
        ],
    },
    {
        "file": "PEPChuZhong7_2_T.json",
        "grade": 7,
        "term": 2,
        "term_name": "下册",
        "name": "PEP 七年级下册",
        "short": "pep7b",
        "units": [
            ("guitar", "Unit 1 Can you play the guitar?"),
            ("up", "Unit 2 What time do you go to school?"),
            ("train", "Unit 3 How do you get to school?"),
            ("rule", "Unit 4 Don't eat in class."),
            ("panda", "Unit 5 Why do you like pandas?"),
            ("newspaper", "Unit 6 I'm watching TV."),
            ("rain", "Unit 7 It's raining!"),
            ("post", "Unit 8 Is there a post office near here?"),
            ("curly", "Unit 9 What does he look like?"),
            ("noodle", "Unit 10 I'd like some noodles."),
            ("milk", "Unit 11 How was your school trip?"),
            ("camp", "Unit 12 What did you do last weekend?"),
        ],
    },
    {
        "file": "PEPChuZhong8_1_T.json",
        "grade": 8,
        "term": 1,
        "term_name": "上册",
        "name": "PEP 八年级上册",
        "short": "pep8a",
        "units": [
            ("anyone", "Unit 1 Where did you go on vacation?"),
            ("housework", "Unit 2 How often do you exercise?"),
            ("outgoing", "Unit 3 I'm more outgoing than my sister."),
            ("theater", "Unit 4 What's the best movie theater?"),
            ("sitcom", "Unit 5 Do you want to watch a game show?"),
            ("grow up", "Unit 6 I'm going to study computer science."),
            ("paper", "Unit 7 Will people have robots?"),
            ("shake", "Unit 8 How do you make a banana milk shake?"),
            ("exam", "Unit 9 Can you come to my party?"),
            ("potato chips", "Unit 10 If you go to the party..."),
        ],
    },
    {
        "file": "PEPChuZhong8_2_T.json",
        "grade": 8,
        "term": 2,
        "term_name": "下册",
        "name": "PEP 八年级下册",
        "short": "pep8b",
        "units": [
            ("matter", "Unit 1 What's the matter?"),
            ("clean up", "Unit 2 I'll help to clean up the city parks."),
            ("rubbish", "Unit 3 Could you please clean your room?"),
            ("allow", "Unit 4 Why don't you talk to your parents?"),
            ("rainstorm", "Unit 5 What were you doing when the rainstorm came?"),
            ("shoot", "Unit 6 An old man tried to move the mountains."),
            ("square", "Unit 7 What's the highest mountain in the world?"),
            ("treasure", "Unit 8 Have you read Treasure Island yet?"),
            ("amusement", "Unit 9 Have you ever been to a museum?"),
            ("yard", "Unit 10 I've had this bike for three years."),
        ],
    },
    {
        "file": "PEPChuZhong9_1_T.json",
        "grade": 9,
        "term": 1,
        "term_name": "全册",
        "name": "PEP 九年级全册",
        "short": "pep9",
        "units": [
            ("textbook", "Unit 1 How can we become good learners?"),
            ("lantern", "Unit 2 I think that mooncakes are delicious!"),
            ("restroom", "Unit 3 Could you please tell me where the restrooms are?"),
            ("humorous", "Unit 4 I used to be afraid of the dark."),
            ("material", "Unit 5 What are the shirts made of?"),
            ("electricity", "Unit 6 When was it invented?"),
            ("smoke", "Unit 7 Teenagers should be allowed to choose their own clothes."),
            ("whose", "Unit 8 It must belong to Carla."),
            ("prefer", "Unit 9 I like music that I can dance to."),
            ("custom", "Unit 10 You're supposed to shake hands."),
            ("the more ... the more", "Unit 11 Sad movies make me cry."),
            ("backpack", "Unit 12 Life is full of the unexpected."),
            ("litter", "Unit 13 We're trying to save the earth!"),
            ("standard", "Unit 14 I remember meeting all of you in Grade 7."),
        ],
    },
]


def make_word(seq, headword, pos, phonetic, meaning, topic):
    return {
        "id": seq,
        "w": headword,
        "p": pos,
        "i": phonetic,
        "c": meaning,
        "a": audio_key(headword),
        "t": topic,
        "l": letter_of(headword),
        "g": pos_bucket(pos),
    }


def load_ket(compiled):
    words = []
    for i, line in enumerate(SRC.read_text(encoding="utf-8").splitlines(), 1):
        parsed = parse_entry_line(line)
        if not parsed:
            continue
        topic = assign_topic(parsed, compiled)
        words.append(
            make_word(
                i,
                parsed["headword"],
                parsed["pos"],
                parsed["phonetic"],
                parsed["meaning"],
                topic,
            )
        )
    return words


def split_pet_trans(trans: str):
    s = re.sub(r"\s+", " ", str(trans or "")).strip()
    if not s:
        return "", ""
    m = PET_POS_RE.match(s)
    if m:
        pos = re.sub(r"\s+", " ", m.group("pos")).strip()
        return pos, s[m.end() :].strip()
    return "", s


def load_pet(compiled):
    src = json.loads((RAW / "pet-2024.json").read_text(encoding="utf-8"))
    words = []
    for i, item in enumerate(src, 1):
        head = str(item.get("name") or "").strip()
        if not head:
            continue
        trans = item.get("trans") or []
        raw = trans[0] if trans else ""
        pos, meaning = split_pet_trans(raw)
        ipa = str(item.get("ukphone") or item.get("usphone") or "").strip()
        parsed = {"headword": head, "pos": pos, "phonetic": ipa, "meaning": meaning}
        topic = assign_topic(parsed, compiled)
        words.append(make_word(i, head, pos, ipa, meaning, topic))
    return words


def assign_units_by_starts(items, unit_starts):
    """items: list of dict with 'w'. unit_starts: [(start_word, uid, uname, color), ...]"""
    next_i = 1
    current = unit_starts[0]
    for item in items:
        key = re.sub(r"\s+", " ", item["w"]).strip().lower()
        if next_i < len(unit_starts):
            want = re.sub(r"\s+", " ", unit_starts[next_i][0]).strip().lower()
            if key == want:
                current = unit_starts[next_i]
                next_i += 1
        item["t"] = current[1]
    return next_i == len(unit_starts)


def pack_pep_book(name, short, grade, term, term_name, unit_defs, items):
    groups = []
    for i, (uid, uname, color) in enumerate(
        [(u[1], u[2], u[3]) for u in unit_defs]
    ):
        groups.append({"id": uid, "name": uname, "color": color})
    words = []
    for i, it in enumerate(items, 1):
        words.append(
            make_word(i, it["w"], it.get("p", ""), it.get("i", ""), it.get("c", ""), it["t"])
        )
    return {
        "id": f"pep-{grade}-{term}",
        "name": name,
        "short": short,
        "kind": "unit",
        "grade": grade,
        "term": term,
        "termName": term_name,
        "groups": groups,
        "words": words,
    }


def load_g3_2024():
    units = json.loads((RAW / "pep_g3_2024.json").read_text(encoding="utf-8"))
    books = []
    specs = [
        (units[:6], 3, 1, "上册", "PEP 三年级上册（2024）", "pep3a"),
        (units[6:], 3, 2, "下册", "PEP 三年级下册（2024）", "pep3b"),
    ]
    for chunk, grade, term, term_name, name, short in specs:
        unit_defs = []
        items = []
        for ui, u in enumerate(chunk):
            uid = f"u{ui + 1}"
            color = UNIT_COLORS[ui % len(UNIT_COLORS)]
            title = u["name"]
            if u.get("zh"):
                title = f'{u["name"]} · {u["zh"]}'
            unit_defs.append(("", uid, title, color))
            for w in u["words"]:
                items.append({"w": w["w"], "c": w.get("c", ""), "p": "", "i": "", "t": uid})
        books.append(pack_pep_book(name, short, grade, term, term_name, unit_defs, items))
    return books


def load_youdao_pep():
    books = []
    for spec in PEP_YOUDAO:
        path = RAW / spec["file"]
        raw_words = json.loads(path.read_text(encoding="utf-8"))
        items = []
        for row in raw_words:
            head = str(row.get("name") or "").strip()
            if not head:
                continue
            trans = row.get("trans") or []
            meaning = trans[0] if trans else ""
            ipa = str(row.get("ukphone") or row.get("usphone") or "").strip()
            items.append({"w": head, "c": meaning, "p": "", "i": ipa})
        unit_defs = []
        for ui, (start, title) in enumerate(spec["units"]):
            uid = f"u{ui + 1}"
            color = UNIT_COLORS[ui % len(UNIT_COLORS)]
            unit_defs.append((start, uid, title, color))
        ok = assign_units_by_starts(items, unit_defs)
        if not ok:
            print(f"warn: unit split incomplete for {spec['file']}")
        books.append(
            pack_pep_book(
                spec["name"],
                spec["short"],
                spec["grade"],
                spec["term"],
                spec["term_name"],
                unit_defs,
                items,
            )
        )
    return books


def book_payload(kind, name, short, words, groups):
    return {
        "id": short,
        "name": name,
        "short": short,
        "kind": kind,
        "groups": groups,
        "words": words,
    }


def main():
    compiled = compile_topic_sets()
    topic_groups = [{"id": g, "name": n, "color": c} for g, n, c in GROUPS]
    ket = load_ket(compiled)
    pet = load_pet(compiled)
    pep_books = load_g3_2024() + load_youdao_pep()
    pep_map = {f"{b['grade']}-{b['term']}": b for b in pep_books}

    payload = {
        "libs": {
            "ket": book_payload("topic", "KET 高频词汇", "ket", ket, topic_groups),
            "pet": book_payload("topic", "PET / B1 Preliminary", "pet", pet, topic_groups),
        },
        "pep": pep_map,
    }
    tpl = TPL.read_text(encoding="utf-8")
    html = tpl.replace(
        "/*__EBB_DATA__*/",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )
    OUT.write_text(html, encoding="utf-8")
    print(f"ket={len(ket)} pet={len(pet)} pep_books={len(pep_books)}")
    print(f"html={OUT} bytes={OUT.stat().st_size}")
    for b in pep_books:
        print(f"  {b['name']:24} {len(b['words']):4} units={len(b['groups'])}")


if __name__ == "__main__":
    main()
