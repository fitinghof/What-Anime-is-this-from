import re
import pykakasi
from fuzzywuzzy import fuzz
from typing import Callable

def jaccard_similarity(str1, str2):
    set1, set2 = set(str1), set(str2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union != 0 else 0

testingList = [
    ("デート ・ ア ・ ライブ", "Date A Live"),
    ("モンスター ハンター", "Monster Hunter"),
    ("ファイナル ファンタジー", "Final Fantasy"),
    ("オンライン ゲーム", "Online Game"),
    ("レジェンド オブ ゼルダ", "Legend of Zelda"),
    ("ポケット モンスター", "Pocket Monster"),
    ("ドラゴン クエスト", "Dragon Quest"),
    ("キングダム ハーツ", "Kingdom Hearts"),
    ("ストリート ファイター", "Street Fighter"),
    ("スーパーマリオ", "Super Mario"),
    ("トーキョーズ・ウェイ！", "Tokyo's Way!"),
    ("グランド ・ セフト ・ オート", "Grand Theft Auto"),
    ("コール オブ デューティー", "Call of Duty"),
    ("カウンター ストライク", "Counter Strike"),
    ("エルデン リング", "Elden Ring"),
    ("デッド バイ デイライト", "Dead by Daylight"),
    ("ダーク ソウル", "Dark Souls"),
    ("メタル ギア ソリッド", "Metal Gear Solid"),
    ("アサシン クリード", "Assassin's Creed"),
    ("ワールド オブ ウォークラフト", "World of Warcraft"),
    ("ブラッドサーキュレーター", "Blood Circulator"),
]

testListFail = [
    ("又三郎", "Shayou"),  # Completely different word
    ("こんにちは", "Hello"),  # A common greeting, not a game title
    ("さようなら", "Goodbye"),  # Another greeting
    ("ありがとう", "Thank you"),  # Common phrase
    ("おはよう", "Good morning"),  # Common phrase
    ("バイオハザード", "Resident Evil"),
    ("ライラック", "Aiue"),
    ("アップル", "April"),       # Apple -> April
    ("バナナ", "Bandana"),      # Banana -> Bandana
    ("コーヒー", "Cough"),      # Coffee -> Cough
    ("ホテル", "Hostel"),        # Hotel -> Hostel
    ("コンピュータ", "Commute"),  # Computer -> Commute
    ("ゲーム", "Gain"),           # Game -> Gain
    ("カメラ", "Camper"),       # Camera -> Camper
    ("ハンバーガー", "Hammer"),  # Hamburger -> Hammer
    ("ジュース", "Joust"),       # Juice -> Joust
    ("ミュージック", "Mosaic"),  # Music -> Mosaic
    ("テレビ", "Telephone"),  # Television -> Telephone
    ("パソコン", "Passion"),  # PC -> Passion
    ("エレベーター", "Elaborate"),  # Elevator -> Elaborate
    ("エスカレーター", "Escapade"),  # Escalator -> Escapade
    ("レストラン", "Resonant"),  # Restaurant -> Resonant
    ("チョコレート", "Choke"),  # Chocolate -> Choke
    ("サンドイッチ", "Sandpit"),  # Sandwich -> Sandpit
    ("バイク", "Back"),  # Bike -> Back
    ("スピーカー", "Spiker"),  # Speaker -> Spiker
    ("マイク", "Mice"),  # Microphone -> Mice
    ("チェック", "Chick"),  # Check -> Chick
    ("ニュース", "New"),  # News -> New
    ("バッグ", "Back"),  # Bag -> Back
    ("トレーナー", "Trainee"),  # Trainer -> Trainee
    ("シャツ", "Short"),  # Shirt -> Short
    ("アイスクリーム", "Icy Dream"),  # Ice Cream -> Icy Dream
    ("ドア", "Duo"),  # Door -> Duo
    ("ソファ", "Software"),  # Sofa -> Software
    ("ペン", "Pain"),  # Pen -> Pain
    ("テスト", "Taste"),  # Test -> Taste
    ("バンド", "Bond"),  # Band -> Bond
    ("マスク", "Musk"),  # Mask -> Musk
    ("スーパー", "Soup"),  # Super -> Soup
    ("ポイント", "Paint"),  # Point -> Paint
    ("ウイルス", "Wireless"),  # Virus -> Wireless
]

def processPossibleJapanese(japanese: str) -> str:
    kakasi = pykakasi.Kakasi()
    # First, do a basic romanization
    japanese_regex = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF65-\uFF9F]")
    romanized = japanese
    if bool(japanese_regex.search(japanese)):
        romanized = " ".join([word["hepburn"] for word in kakasi.convert(romanized)])

    # Normalize spaces
    romanized = re.sub(r'\s+', ' ', romanized).strip()
    #print(romanized)

    return romanized

def normalize_text(text: str):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)  # Remove non-alphanumeric characters
    return text

def remove_vowels(word):
    vowels = "aeiouAEIOU"
    return "".join(letter for letter in word if letter not in vowels)

def remove_consonants(word):
    vowels = "aeiouAEIOU"
    return "".join(letter for letter in word if letter in vowels)

# fuzz functions:
# fuzz.ratio
# fuzz.partial_ratio
# fuzz.token_sort_ratio
# fuzz.token_set_ratio
# fuzz.partial_token_sort_ratio
# fuzz.partial_token_set_ratio
# fuzz.UQRatio
# fuzz.UWRatio
# fuzz.WRatio


def processSimilarity(japanese_text: str, romaji_text: str) -> float:
    japanese_regex = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF65-\uFF9F]")
    if(bool(japanese_regex.search(japanese_text))):
        romanized_japanese = processPossibleJapanese(japanese_text)
        normalized_japanese = normalize_text(romanized_japanese)
        normalized_romaji = normalize_text(romaji_text)

        # print(normalized_japanese, ":::", normalized_romaji)

        fuzz_value_full = fuzz.ratio(normalized_japanese, normalized_romaji)

        normalized_japanese_consonants = remove_vowels(normalized_japanese).replace("r", "l").replace("b", "v")
        normalized_romaji_consonants = remove_vowels(normalized_romaji).replace("r", "l").replace("b", "v")

        print(normalized_japanese_consonants, normalized_romaji_consonants)

        fuzz_value_consonants = fuzz.ratio(normalized_japanese_consonants, normalized_romaji_consonants)

        normalized_japanese_vowels = re.sub(r"(.)\1+", r"\1", "".join(sorted(remove_consonants(normalized_japanese))))
        normalized_romaji_vowels = re.sub(r"(.)\1+", r"\1", "".join(sorted(remove_consonants(normalized_romaji))))

        consonantWeight = 0.9
        fullWeight = 1 - consonantWeight

        return (fuzz_value_consonants * consonantWeight + fuzz_value_full * fullWeight)
    else:
        normalized_japanese = normalize_text(japanese_text)
        normalized_romaji = normalize_text(romaji_text)
        return fuzz.ratio(normalized_japanese, normalized_romaji)

def processSimilarity2(japanese_text: str, romaji_text: str) -> int:
    romanized_japanese = processPossibleJapanese(japanese_text)
    normalized_japanese = normalize_text(romanized_japanese)
    normalized_romaji = normalize_text(romaji_text)

    print(normalized_japanese, ":::", normalized_romaji)

    return fuzz.token_sort_ratio(normalized_japanese, normalized_romaji)

def testSimilarity(test: tuple[str,str], successFunction: Callable[[int], bool]) -> float:
    score = processSimilarity2(test[0], test[1])
    if not successFunction(score):
        print("Failed Test:", test, ", Score", score)
    return score

def testAll(tests: list[tuple[str,str]], successFunction: Callable[[int], bool]) -> float:
    totalScore = 0
    fails = 0
    for test in tests:
        score = testSimilarity(test, successFunction)
        totalScore += score
        #fails += 0 if evalfunc(score) else 1
    return totalScore / len(tests)

if __name__ == "__main__":
    failLimit = 60
    #for func in [fuzz.partial_ratio, fuzz.partial_token_set_ratio, fuzz.partial_token_sort_ratio, fuzz.ratio, fuzz.UQRatio, fuzz.token_sort_ratio, fuzz.token_set_ratio]:
    print(" --------------- Doing match tests --------------- ")
    averageSuccessScore = testAll(testingList, lambda a: a > failLimit)

    print(" --------------- Doing False Match tests --------------- ")
    averageFailScore = testAll(testListFail, lambda a: a < failLimit)

    print(" --------------- Doing single tests --------------- ")
    test = ("ライラック", "Aiue")
    print(f"Test: {test}, Score {testSimilarity(test, lambda a: a < failLimit)}")

    print("Average Success Score: ", averageSuccessScore)
    print("Average Fail Score: ", averageFailScore)
    print("Delta:", averageSuccessScore - averageFailScore)


