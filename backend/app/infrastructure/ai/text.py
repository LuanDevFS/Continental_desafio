import re
import unicodedata

# Stopwords en español, las suficientes para que el retrieval no se
# ensucie con ruido. No pretende ser exhaustiva.
STOPWORDS = frozenset(
    """
    de la el en que y a los del se las por un para con no una su al es lo
    como mas o pero sus le ya o este esta si porque esta entre cuando muy
    sin sobre también me hasta hay donde quien desde todo nos durante todos
    uno les ni contra otros ese eso ante ellos e esto mi antes algunos unos
    yo otro otras otra el tanto esa estos mucho quienes nada muchos cual
    poco ella estar estas algunas algo nosotros mi mis tu te ti tus ellas
    nosotras vosotros vosotras os mío mía míos mías tuyo tuya tuyos tuyas
    suyo suya suyos suyas nuestro nuestra nuestros nuestras vuestro vuestra
    vuestros vuestras esos esas estoy estás está estamos estáis están esté
    estés estemos estéis estén estaré estará estaremos estaréis estarán
    estaría estarías estaríamos estaríais estarían estaba estabas estábamos
    estabais estaban estuve estuviste estuvo estuvimos estuvisteis estuvieron
    estuviera estuvieras estuviéramos estuvierais estuvieran estuviese
    estuvieses estuviésemos estuvieseis estuviesen estando estado estada
    estados estadas estad he has ha hemos habéis han haya hayas hayamos
    hayáis hayan habré habrá habremos habréis habrán habría habrías habríamos
    habríais habrían había habías habíamos habíais habían hube hubiste hubo
    hubimos hubisteis hubieron hubiera hubieras hubiéramos hubierais hubieran
    hubiese hubieses hubiésemos hubieseis hubiesen habiendo habido habida
    habidos habidas soy eres es somos sois son sea seas seamos seáis sean
    seré será seremos seréis serán sería serías seríamos seríais serían era
    eras éramos erais eran fui fuiste fue fuimos fuisteis fueron fuera fueras
    fuéramos fuerais fueran fuese fueses fuésemos fueseis fuesen siendo sido
    tiene tienen tengo tienes tenemos tenéis
    """.split()
)

_TOKEN_RE = re.compile(r"[a-z0-9ñü]+")
_SENTENCE_RE = re.compile(r"(?<=[.!?;])\s+|\n+")


def normalize(text: str) -> str:
    # minúsculas + sin tildes para que "informacion" matchee "información"
    text = text.lower()
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(normalize(text)) if t not in STOPWORDS]


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]
