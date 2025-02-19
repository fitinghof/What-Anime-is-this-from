import fugashi
import Levenshtein
import re
import pykakasi
from Levenshtein import jaro_winkler
from collections import Counter
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

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
]

testListFail = [
    ("又三郎", "Shayou"),
    ("こんにちは", "Hello"),
    ("さようなら", "Goodbye"),
    ("ありがとう", "Thank you"),
    ("おはよう", "Good morning"),
]

def processPossibleJapanese(japanese: str) -> str:
    kakasi = pykakasi.Kakasi()
    # First, do a basic romanization
    japanese_regex = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF65-\uFF9F]")
    romanized = japanese
    if bool(japanese_regex.search(japanese)):
        romanized = "".join([word["hepburn"] for word in kakasi.convert(romanized)])

    # Normalize spaces
    romanized = re.sub(r'\s+', ' ', romanized).strip()

    return romanized

def normalize_text(text: str):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]', '', text)  # Remove non-alphanumeric characters
    return text

def processSimilarity(japanese_text: str, romaji_text: str) -> int:
    romanized_japanese = processPossibleJapanese(japanese_text)
    normalized_japanese = normalize_text(romanized_japanese)
    normalized_romaji = normalize_text(romaji_text)

    print(normalized_japanese, ":::", normalized_romaji)

    return fuzz.token_sort_ratio(normalized_japanese, normalized_romaji)

if __name__ == "__main__":
    failLimit = 0.5
    totalScore = 0
    for test in testingList:
        score = processSimilarity(test[0], test[1])
        if score < failLimit:
            print("Failed Test:", test, ", Score", score)
        totalScore += score

    for test in testListFail:
        score = processSimilarity(testListFail[0], testListFail[1])
        if score > failLimit:
            print("Failed fail Test:", test, ", Score", score)
        print(test, ", Score", score)
    averageScore = totalScore / len(testingList)
    print("Average Score: ", averageScore)


