# -*- coding: utf-8 -*-
"""Fill part-of-speech tags for PEP (and other) headwords."""
from __future__ import annotations

import re
from collections import defaultdict

NUM_WORDS = {
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty",
    "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "million",
}

FUNCTION_POS = {
    "a": "art", "an": "art", "the": "art",
    "i": "pron", "you": "pron", "he": "pron", "she": "pron", "it": "pron",
    "we": "pron", "they": "pron", "me": "pron", "him": "pron", "her": "pron",
    "us": "pron", "them": "pron", "my": "det", "your": "det", "his": "det",
    "its": "det", "our": "det", "their": "det", "mine": "pron", "yours": "pron",
    "hers": "pron", "ours": "pron", "theirs": "pron", "myself": "pron",
    "yourself": "pron", "himself": "pron", "herself": "pron", "itself": "pron",
    "ourselves": "pron", "themselves": "pron", "this": "det", "that": "det & pron",
    "these": "det", "those": "det", "who": "pron", "whom": "pron", "whose": "det",
    "which": "pron", "what": "pron", "where": "adv", "when": "adv", "why": "adv",
    "how": "adv", "and": "conj", "but": "conj", "or": "conj", "so": "conj",
    "because": "conj", "if": "conj", "although": "conj", "unless": "conj",
    "whether": "conj", "whenever": "conj", "nor": "conj", "than": "conj",
    "in": "prep", "on": "prep", "at": "prep", "to": "prep", "for": "prep",
    "of": "prep", "from": "prep", "with": "prep", "about": "prep", "into": "prep",
    "onto": "prep", "upon": "prep", "over": "prep", "under": "prep", "near": "prep",
    "beside": "prep", "besides": "prep", "between": "prep", "among": "prep",
    "through": "prep", "across": "prep", "behind": "prep", "before": "prep",
    "after": "prep", "during": "prep", "without": "prep", "against": "prep",
    "towards": "prep", "toward": "prep", "around": "prep", "along": "prep",
    "not": "adv", "yes": "exclaim", "no": "det", "ok": "exclaim", "okay": "exclaim",
    "please": "exclaim", "hello": "exclaim", "hi": "exclaim", "hey": "exclaim",
    "yum": "exclaim", "bye": "exclaim",
    "is": "v", "am": "v", "are": "v", "was": "v", "were": "v", "be": "v",
    "been": "v", "being": "v", "do": "v", "does": "v", "did": "v", "done": "v",
    "have": "v", "has": "v", "had": "v", "having": "v",
    "will": "aux", "would": "aux", "can": "aux", "could": "aux", "may": "aux",
    "might": "aux", "must": "aux", "shall": "aux", "should": "aux",
    "isn't": "v", "aren't": "v", "wasn't": "v", "weren't": "v", "don't": "v",
    "doesn't": "v", "didn't": "v", "haven't": "v", "hasn't": "v", "hadn't": "v",
    "won't": "aux", "wouldn't": "aux", "can't": "aux", "couldn't": "aux",
    "let's": "v", "we'll": "aux", "i'm": "v", "you're": "v", "they're": "v",
    "it's": "pron & v",
}

PLACE_HINTS = ("山", "广场", "博物馆", "长城", "瀑布", "城市", "海洋", "运动会",
               "协会", "基金会", "作家", "女名", "男名", "姓氏", "公园", "办公室")


def _norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def lookup_from_words(words) -> dict[str, str]:
    table: dict[str, str] = {}
    for w in words:
        pos = (w.get("p") or "").strip()
        if not pos:
            continue
        key = _norm(w.get("w") or "")
        if key and key not in table:
            table[key] = pos
    return table


def wordnet_table(heads: list[str]) -> dict[str, str]:
    try:
        from nltk.corpus import wordnet as wn
    except Exception:
        return {}
    mapping = {"n": "n", "v": "v", "a": "adj", "s": "adj", "r": "adv"}
    rank = {"n": 0, "v": 1, "adj": 2, "adv": 3}
    out: dict[str, str] = {}
    for head in heads:
        key = _norm(head).replace(" ", "_").replace("-", "_")
        counts: dict[str, int] = defaultdict(int)
        syns = wn.synsets(key)
        if not syns and "_" in key:
            syns = wn.synsets(key.split("_")[0])
        for syn in syns:
            counts[mapping.get(syn.pos(), "")] += 1
        counts.pop("", None)
        if not counts:
            continue
        ordered = sorted(counts.items(), key=lambda x: -x[1])
        tags = [p for p, c in ordered if c >= max(2, int(ordered[0][1] * 0.35)) or p == ordered[0][0]]
        tags = sorted(set(tags), key=lambda x: rank.get(x, 9))[:2]
        out[_norm(head)] = tags[0] if len(tags) == 1 else " & ".join(tags)
    return out


def heuristic_pos(head: str, meaning: str) -> str:
    h = (head or "").strip()
    c = (meaning or "").strip()
    low = _norm(h)
    if not low:
        return ""
    if low in FUNCTION_POS:
        return FUNCTION_POS[low]
    if low in NUM_WORDS:
        return "num"
    if any(x in c for x in PLACE_HINTS):
        return "n"
    if re.search(r"[?？]$", h) or (h[:1].isupper() and h.endswith(".")):
        return "exclaim"
    if c.endswith("？") or "怎么样" in c or "怎么了" in c:
        if " " in h or "..." in h or "…" in h or "?" in h or "？" in h:
            return "phr"
        return "exclaim"
    if c.endswith("的") or c.endswith("的。"):
        return "adj"
    if c.endswith("地"):
        return "adv"
    if "..." in h or "…" in h:
        first = re.split(r"[\s.…" + "\u2026]+", low)[0]
        first = first.strip("()")
        if first in {"be", "have", "get", "go", "take", "look", "put", "turn", "keep", "ask", "compare"}:
            return "phr v"
        return "phr"
    if re.search(r"\s", h):
        if low.startswith("(be)") or re.match(
            r"^(be|have|get|go|take|look|put|turn|keep|ask|would)\b", low
        ):
            return "phr v"
        if low.startswith("the ") or h[:1].isupper():
            return "n"
        return "phr"
    if h.isupper() and 1 < len(h) <= 6:
        return "n"
    if h[:1].isupper() and h[1:].islower() and " " not in h:
        return "n"
    return ""


def guess_pos(head: str, meaning: str, known: dict[str, str], wn_map: dict[str, str]) -> str:
    low = _norm(head)
    heur = heuristic_pos(head, meaning)
    if low in NUM_WORDS or low in FUNCTION_POS:
        return heur
    if low in known:
        return known[low]
    if heur:
        return heur
    if low in wn_map:
        return wn_map[low]
    if (meaning or "").endswith("的"):
        return "adj"
    return "n"


def fill_words(words, known: dict[str, str], wn_map: dict[str, str]) -> int:
    filled = 0
    for w in words:
        if w.get("p"):
            continue
        w["p"] = guess_pos(w.get("w") or "", w.get("c") or "", known, wn_map)
        filled += 1
    return filled
