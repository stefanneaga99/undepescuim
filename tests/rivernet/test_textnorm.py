import pytest

from rivernet.textnorm import fix_diacritics, fold, river_key, river_keys
from rivernet import textnorm


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Râul Mureş", "Râul Mureș"),  # cedilla s -> comma-below
        ("Ţarcu", "Țarcu"),  # cedilla T
        ("Råul Geoagiu", "Râul Geoagiu"),  # a-ring mis-rendering of â
        ("ţinut şi Åre", "ținut și Âre"),
        ("Bistrița", "Bistrița"),  # already correct: unchanged
        ("", ""),
        (None, ""),
    ],
)
def test_fix_diacritics_repairs_legacy_forms_and_keeps_case(raw, expected):
    assert fix_diacritics(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Râul Buzău", "raul buzau"),
        ("  Lacul   Vidraru ", "lacul vidraru"),
        ("Mureş", "mures"),  # cedilla
        ("Mureș", "mures"),  # comma-below
        ("Ţibleş", "tibles"),
        ("Råul Geoagiu Inferior", "raul geoagiu inferior"),
        ("Pr. Valea Mare", "pr valea mare"),  # dot removed
        ("conf. cu Râul Olt", "conf cu raul olt"),
        ("Bumbești-Jiu", "bumbesti-jiu"),  # hyphen kept
        ("Siret – Prut", "siret prut"),  # en dash is punctuation
        ("pîrîul", "piriul"),  # old orthography for pârâul
        ("Апшиця", "апшиця"),  # Cyrillic passes through, lower-cased
        ("snake_case", "snake case"),
        ("", ""),
        (None, ""),
    ],
)
def test_fold(raw, expected):
    assert fold(raw) == expected


def test_fold_is_idempotent():
    for raw in ["Râul Mureş", "Ţibleş", "Bumbești-Jiu", "Valea Iadului", "Апшиця"]:
        assert fold(fold(raw)) == fold(raw)


@pytest.mark.parametrize(
    "name, keys",
    [
        ("Râul Geoagiu Inferior", ["geoagiu"]),
        ("Råul Geoagiu Inferior", ["geoagiu"]),  # legacy a-ring
        ("Crișul Repede Mijlociu", ["crisul repede"]),
        ("Valea Iadului", ["valea iadului", "iadului"]),
        ("Jiul de Vest", ["jiul de vest", "jiul"]),
        ("Pârâul Buzăul Mijlociu", ["buzaul"]),
        ("Mureș", ["mures"]),
        ("Râul Mare inferior II", ["mare"]),  # two trailing qualifiers
        ("Bistrița Aurie III", ["bistrita aurie"]),
        ("Pr. Teleajen", ["teleajen"]),
        ("Pîrîul Mare", ["mare"]),  # old orthography prefix
        ("R. Olt", ["olt"]),
        ("Râul Pârâul Mic", ["mic"]),  # stacked generic prefixes
        ("Olt sector Făgăraș", ["olt"]),  # free-text tail
        ("Târnava Mare", ["tarnava mare"]),  # 'mare' is part of the name
        ("Valea Râul Mare", ["valea mare", "mare"]),
        ("Pârâul Valea Mare", ["valea mare", "mare"]),
        ("Jiul de Est Superior", ["jiul de est", "jiul"]),
        ("Cerna de Nord", ["cerna de nord", "cerna"]),
        ("Râul", ["raul"]),  # nothing left after stripping -> keep the word
        ("Inferior", ["inferior"]),
        ("Апшиця", ["апшиця"]),
        ("", []),
        (None, []),
    ],
)
def test_river_keys(name, keys):
    assert river_keys(name) == keys


def test_river_key_is_the_most_specific_key():
    assert river_key("Valea Iadului") == "valea iadului"
    assert river_key("Jiul de Vest") == "jiul de vest"
    assert river_key("Râul Geoagiu Inferior") == "geoagiu"
    assert river_key("") == ""
    assert river_key(None) == ""


def test_river_keys_have_no_duplicates():
    for name in ["Valea Mare", "Jiul de Vest", "Râul Râul Olt", "Pr. Pr. Mic"]:
        keys = river_keys(name)
        assert len(keys) == len(set(keys))


def test_same_river_written_differently_shares_a_key():
    variants = ["Râul Mureș", "Mureş", "Pr. Mureș Inferior", "Râul Mureș II"]
    assert {river_key(v) for v in variants} == {"mures"}


def test_feminine_qualifiers_and_afluenti_tail():
    from rivernet.textnorm import river_keys

    assert river_keys("Râul Prahova mijlocie ") == ["prahova"]
    assert river_keys("Râul Prahova superioară") == ["prahova"]
    assert river_keys("Râul Cibinul Inferioară") == ["cibinul"]
    assert river_keys("Râul Jiul de vest – superior cu afluenții") == ["jiul de vest", "jiul"]
    assert river_keys("Valea Călinești cu pâraiele Călinești, Sulița") == ["valea calinesti", "calinesti"]
    assert river_keys("Valea cu Apă") == ["valea cu apa", "cu apa"]  # 'cu' alone is not a tail


def test_article_variants_and_match_keys():
    from rivernet.textnorm import article_variants, river_match_keys

    assert article_variants("gurghiul") == ["gurghiu", "gurghi"]
    assert article_variants("buzaului") == ["buzau"]
    assert article_variants("valea cibinul") == ["valea cibinu", "valea cibin"]
    assert article_variants("olt") == [] and article_variants("") == []
    assert river_match_keys("Râul Gurghiul mijlociu")[0] == "gurghiul"
    assert "gurghiu" in river_match_keys("Râul Gurghiul mijlociu")


@pytest.mark.parametrize("a,b", [
    ("Valea Pojorâtei", "Pojorâta"),
    ("Râul Lesuntu", "Lesuntul"),
    ("Valea Slănicului", "Slanic"),
    ("Gârla Huțanilor", "Huțani"),
    ("Râul Bistricioara II", "Bistricioara"),
    ("Pâraiele Boia Mare", "Boia Mare"),
    ("Izvorul Mureș", "Mureș"),
])
def test_stem_key_agrees_across_inflections(a, b):
    assert textnorm.stem_key(a) == textnorm.stem_key(b) != ""


def test_stem_key_keeps_distinct_names_apart_and_short_tokens():
    assert textnorm.stem_key("Valea Sâmbetei") != textnorm.stem_key("Sâmbăta")  # vowel change: fuzzy tier
    assert textnorm.stem_key("Valea") == "val"  # a lone generic word is the name
    assert textnorm.stem_key("Ier") == "ier"  # never shorter than 3 letters
    assert textnorm.stem_key("") == "" and textnorm.stem_key(None) == ""


@pytest.mark.parametrize("name,key", [
    ("Prut– fără lacul Stânca", "prut"),
    ("Râul Prut și revărsări", "prut"),
    ("Râul Olt și afluenții săi", "olt"),
    ("Râul Jiu și afluenții săi", "jiu"),
    ("Râul Șomuzul Mare și afluenții", "somuzul mare"),
    ("Râul Mureș, cu afluenții", "mures"),
    ("Valea Urii cu pâraiele Uria și Murgoci", "valea urii"),
    ("Izvoarele Moldovei și Sucevei", "izvoarele moldovei si sucevei"),  # "și" + a river: not an extra
])
def test_contract_extras_are_cut_from_the_name(name, key):
    assert textnorm.river_key(name) == key
