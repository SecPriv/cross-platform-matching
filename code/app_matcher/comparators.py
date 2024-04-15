

from urllib.parse import urlparse
from imagehash import ImageHash, ImageMultiHash
from rapidfuzz.distance import Prefix, Levenshtein

def is_same_domain(url1: str, url2: str) -> bool:
    parsedUrl1 = urlparse(url1).hostname
    parsedUrl2 = urlparse(url2).hostname
    return parsedUrl1 == parsedUrl2

def normalized_shared_prefix_length(a: str, b: str) -> float:
    return Prefix.normalized_distance(a.lower(), b.lower())

def normalized_levenshtein_distance(a: str, b: str) -> float:
    return Levenshtein.normalized_distance(a.lower(), b.lower())

def deep_link_comparison(a: list, b: list) -> int:
    if len(a) == 0 or len(b) == 0:
        return 0
    
    a = set(a)
    b = set(b)

    return len(set.intersection(a, b))

def hash_compare(a: ImageHash, b: ImageHash) -> float:
    return 1.0-abs(a - b)/max(len(a), len(b))

def hash_compare_multi(a: ImageMultiHash, b: ImageMultiHash) -> float:
    if a.matches(b):
        return 1.0
    return 0