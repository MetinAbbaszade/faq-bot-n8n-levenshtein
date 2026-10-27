"""
Python version of the "Find best match" logic, for learning and threshold tuning.
Same algorithm as the JavaScript Code node in n8n.

Usage:
    python3 faq_similarity.py                      # runs the built-in test questions
    python3 faq_similarity.py "how do i reset my pasword"

Expects faq_mock_data.csv (columns: id, question, answer) in the same folder.
Uses only the Python standard library.
"""

import csv
import re
import sys

THRESHOLD = 0.7


def normalize(text):
    """Lowercase, remove punctuation, collapse spaces.
    [^\\w\\s] removes everything except letters, digits, underscore and spaces;
    in Python 3, \\w already includes Unicode letters (ə, ş, ж...)."""
    text = str(text or "").lower()
    text = re.sub(r"[^\w\s]|_", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def levenshtein(a, b):
    """Minimum number of single-character insertions, deletions and
    replacements to turn a into b.
    dp[i][j] = distance between the first i chars of a and the first j chars of b."""
    rows, cols = len(a) + 1, len(b) + 1
    dp = [[0] * cols for _ in range(rows)]

    # Base cases: turning a string into an empty one (and back) costs its length
    for i in range(rows):
        dp[i][0] = i
    for j in range(cols):
        dp[0][j] = j

    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,         # delete
                dp[i][j - 1] + 1,         # insert
                dp[i - 1][j - 1] + cost,  # replace (free if the characters match)
            )

    return dp[len(a)][len(b)]


def similarity(a, b):
    """0..1 score: 1 = identical, 0 = completely different."""
    longest = max(len(a), len(b))
    if longest == 0:
        return 1.0  # both empty
    return 1 - levenshtein(a, b) / longest


def load_faq(path="faq_mock_data.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if row.get("question") and row.get("answer")]


def find_best_match(user_text, faq_rows):
    user_question = normalize(user_text)
    best = {"score": 0.0, "question": None, "answer": None}

    for row in faq_rows:
        score = similarity(user_question, normalize(row["question"]))
        if score > best["score"]:
            best = {"score": score, "question": row["question"], "answer": row["answer"]}

    best["matched"] = best["score"] >= THRESHOLD
    return best


TEST_QUESTIONS = [
    "How do I reset my password?",       # exact
    "how do i reset my password",        # lowercase, no punctuation
    "How do I reset my pasword?",        # typo
    "reset password",                    # short phrasing
    "password reset how?",               # reordered
    "How do I change my address?",       # close to two different FAQs
    "Do you sell gift cards?",           # unrelated
]


def main():
    faq = load_faq()
    questions = sys.argv[1:] or TEST_QUESTIONS

    print(f"Threshold: {THRESHOLD}\n")
    for q in questions:
        r = find_best_match(q, faq)
        status = "MATCH   " if r["matched"] else "ESCALATE"
        print(f"{status} {r['score']:.3f}  {q!r}")
        print(f"         best: {r['question']!r}\n")


if __name__ == "__main__":
    main()