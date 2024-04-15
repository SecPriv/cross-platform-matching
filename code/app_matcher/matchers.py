import glob
from multiprocessing import current_process
import os
import time
import imagehash
import numpy
from scipy.sparse import spmatrix
from .tf_idf.tf_idf_shared_memory import (
    cleanup_similarities_sm,
    cleanup_height_sm,
    cleanup_width_sm,
    get_similarities_sm,
    get_height_sm,
    get_width_sm,
)
from database.analysis_results.preprocessing_result.android_preprocessing_result.android_preprocessing_result import (
    AndroidPreprocessingResult,
)

from database.analysis_results.preprocessing_result.ios_preprocessing_result.ios_preprocessing_result import (
    iOSPreprocessingResult,
)
from .comparators import (
    deep_link_comparison,
    hash_compare,
    hash_compare_multi,
    is_same_domain,
    normalized_levenshtein_distance,
    normalized_shared_prefix_length,
)

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

WORD_LIST_DIR = "./app_matcher/stop_word_lists" # relative to xpa

def prepare_tf_idf(
    ios_apps: list[iOSPreprocessingResult],
    android_apps: list[AndroidPreprocessingResult],
) -> None:
    global width_sm
    global height_sm
    global android_to_ios_similarities_sm
    global ios_to_android_similarities_sm

    print("[TF-IDF] Creating TF-IDF index...")
    
    stop_words = set()
    for file in glob.glob(os.path.join(WORD_LIST_DIR, "*")):
        print(file)
        if file.endswith("README"):
            continue
        else:
            with open(file, 'r') as fp:
                for word in fp.readlines():
                    stop_words.add(word.strip())


    vectorizer = TfidfVectorizer(stop_words=list(stop_words))
    android_descriptions = [
        android_app.metadata.get("description") for android_app in android_apps
    ]
    # This function runs after prepare_ios_descriptions, so we don't need to join the descriptions
    ios_descriptions = [ios_app.metadata.get("description") for ios_app in ios_apps]

    all_descriptions = android_descriptions + ios_descriptions

    descriptions_index = vectorizer.fit_transform(all_descriptions)
    assert descriptions_index.shape[0] == len(all_descriptions)
    android_vectors: spmatrix = descriptions_index[0 : len(android_descriptions), :]
    ios_vectors: spmatrix = descriptions_index[len(android_descriptions) :, :]

    print(f"[TF-IDF] TF-IDF indexes created")

    def assert_size(matrix: numpy.ndarray):
        assert matrix.dtype == numpy.double
        assert matrix.itemsize == 8  # Needed for shared memory allocation
        x, y = matrix.shape
        assert x == len(ios_apps)
        assert y == len(android_apps)

    print(f"[TF-IDF] Creating similarity matrix")
    all_similarities = cosine_similarity(
        ios_vectors,
        android_vectors,
    )
    assert_size(all_similarities)

    width, height = all_similarities.shape
    print(
        f"[TF-IDF] Similarities calculated - moving them to shared memory with shape {width}x{height}"
    )
    # Store width to shared memory
    width_sm = get_width_sm()
    width_sm[0] = width

    # Store height to shared memory
    height_sm = get_height_sm()
    height_sm[0] = height

    # Copy similarities into shared memory
    android_to_ios_sm = get_similarities_sm()
    numpy.copyto(android_to_ios_sm, all_similarities)

    print(f"[TF-IDF] Shared memory created")


def prepare_image_hashes(
    ios_apps: list[iOSPreprocessingResult],
    android_apps: list[AndroidPreprocessingResult],
) -> None:
    def _parse_hex(hexes: object, which: str):
        if hexes is None or hexes[which] is None:
            return
        hexes[which] = imagehash.hex_to_hash(hexes[which])

    def _parse_multi(hexes: object):
        if hexes is None or hexes["crhash"] is None:
            return
        hexes["crhash"] = imagehash.hex_to_multihash(hexes["crhash"])

    def _parse_all(hexes: object):
        _parse_hex(hexes, "ahash")
        _parse_hex(hexes, "phash")
        _parse_hex(hexes, "whash")
        _parse_multi(hexes)

    for ios_app in ios_apps:
        _parse_all(ios_app.icon)

    for android_app in android_apps:
        _parse_all(android_app.icon)


def prepare_ios_descriptions(
    ios_apps: list[iOSPreprocessingResult],
    android_apps: list[AndroidPreprocessingResult],
) -> None:
    for ios_app in ios_apps:
        ios_app.metadata["description"] = "\n".join(ios_app.metadata.get("description"))


def match_privacy_url(
    ios_app: iOSPreprocessingResult, android_app: AndroidPreprocessingResult
) -> dict[str, float]:
    ios_urls = ios_app.metadata.get("urls")
    p_url1 = ""
    for url in ios_urls:
        if (
            "datenschutzrichtlinie" in url.get("link_name", "").lower()
            or "privacy policy" in url.get("link_name", "").lower()
        ):
            p_url1 = url.get("link", "") or ""

    p_url2 = android_app.metadata.get("urls", {}).get("privacy_policies", "") or ""
    if p_url2 is None:
        # print(f'How: {android_app.metadata.get("urls", {})}')
        p_url2 = ""
    maxLength = max(len(p_url1), len(p_url2), 1)

    same_domain = 1 if is_same_domain(p_url1, p_url2) else 0
    shared_prefix = 1 - normalized_shared_prefix_length(p_url1, p_url2)
    levenshtein_dist = 1 - normalized_levenshtein_distance(p_url1, p_url2)
    max_score = max(same_domain, shared_prefix, levenshtein_dist)

    return {
        # "privacy_url_same_domain": same_domain,
        # "privacy_url_shared_prefix": shared_prefix,
        # "privacy_url_levenshtein_distance": levenshtein_dist,
        #'privacy_url_ios': p_url1,
        #'privacy_url_android': p_url2,
        "privacy_url_max": max_score
    }

def match_developer_url(
    ios_app: iOSPreprocessingResult, android_app: AndroidPreprocessingResult
) -> dict[str, float]:
    ios_urls = ios_app.metadata.get("urls")
    p_url1 = ""
    for url in ios_urls:
        if (
            "website des entwicklers" in url.get("link_name", "").lower()
            or "developer website" in url.get("link_name", "").lower()
        ):
            p_url1 = url.get("link", "") or ""

    p_url2 = android_app.metadata.get("urls", {}).get("developer_website", "") or ""
    if p_url2 is None:
        # print(f'How: {android_app.metadata.get("urls", {})}')
        p_url2 = ""
    maxLength = max(len(p_url1), len(p_url2), 1)

    same_domain = 1 if is_same_domain(p_url1, p_url2) else 0
    shared_prefix = 1 - normalized_shared_prefix_length(p_url1, p_url2)
    levenshtein_dist = 1 - normalized_levenshtein_distance(p_url1, p_url2)
    max_score = max(same_domain, shared_prefix, levenshtein_dist)

    return {
        "developer_url_max": max_score
    }


def match_developer(
    ios_app: iOSPreprocessingResult, android_app: AndroidPreprocessingResult
) -> dict[str, float]:
    dev1 = ios_app.metadata.get("developer_name", "")
    dev2 = android_app.metadata.get("developer_name", "")
    maxLength = max(len(dev1), len(dev2), 1)

    shared_prefix = 1 - normalized_shared_prefix_length(dev1, dev2)
    levenshtein_dist = 1 - normalized_levenshtein_distance(dev1, dev2)
    max_score = max(shared_prefix, levenshtein_dist)

    return {
        #'developer_shared_prefix': shared_prefix,
        #'developer_levenshtein_distance': levenshtein_dist,
        #'developer_ios': dev1,
        #'developer_android': dev2,
        "developer_max": max_score
    }


def match_app_id(
    ios_app: iOSPreprocessingResult, android_app: AndroidPreprocessingResult
) -> dict[str, float]:
    # some use the representation .com.my.id and some others com.my.id
    # --> we normalize this by removing the dot to give the prefix metric a chance
    app_id1 = ios_app.app_id.removeprefix(".")
    app_id2 = android_app.app_id.removeprefix(".")
    maxLength = max(len(app_id1), len(app_id2), 1)

    shared_prefix = 1 - normalized_shared_prefix_length(app_id1, app_id2)
    levenshtein_dist = 1 - normalized_levenshtein_distance(app_id1, app_id2)
    max_score = max(shared_prefix, levenshtein_dist)

    return {
        #'app_id_shared_prefix': shared_prefix,
        #'app_id_levenshtein_distance': levenshtein_dist,
        #'app_id_ios': app_id1,
        #'app_id_android': app_id2,
        "app_id_max": max_score
    }


def match_app_name(
    ios_app: iOSPreprocessingResult, android_app: AndroidPreprocessingResult
) -> dict[str, float]:
    name1 = ios_app.metadata.get("name", "")
    name2 = android_app.metadata.get("app_name", "")
    maxLength = max(len(name1), len(name2), 1)

    shared_prefix = 1 - normalized_shared_prefix_length(name1, name2)
    levenshtein_dist = 1 - normalized_levenshtein_distance(name1, name2)
    max_score = max(shared_prefix, levenshtein_dist)

    return {
        #'app_name_shared_prefix': shared_prefix,
        #'app_name_levenshtein_distance': levenshtein_dist,
        #'app_name_ios': name1,
        #'app_name_android': name2,
        "app_name_max": max_score
    }


def match_deep_links(
    ios_app: iOSPreprocessingResult, android_app: AndroidPreprocessingResult
) -> dict[str, float]:
    # TODO: fix me
    # return {}
    custom_url_schemes_list = ios_app.plist.get("custom_url_schemes", [])
    app_links_1 = set(
        [
            entitlement.removeprefix("applinks:")
            .removeprefix("*.")
            .removeprefix("www.")
            for entitlement in ios_app.entitlements.get("universal_links", [])
        ]
    )
    i = ""
    i.removeprefix
    custom_url_schemes_1 = set()
    for list_item in custom_url_schemes_list:
        if list_item is None:
            continue
        for item in list_item:
            if item is None or type(item) is str:
                continue
            scheme = item.get("CFBundleURLSchemes", None)
            if (
                scheme is not None
                and scheme != "http"
                and scheme != "https"
                and type(scheme) is str
            ):
                custom_url_schemes_1 |= set(scheme)

    custom_url_schemes_2 = android_app.apk_info.get("intent_filters", {}).get(
        "custom_schemes", []
    )
    app_links_2 = set(
        [
            app_link
            .removeprefix("*.")
            .removeprefix("www.")
            for app_link in android_app.apk_info.get("intent_filters", {}).get("app_links", [])
        ]
    )

    maxLength_cus = max(len(custom_url_schemes_1.union(custom_url_schemes_2)), 1)
    maxLength_al = max(len(app_links_1.union(app_links_2)), 1)

    custom_url_scheme_matches = deep_link_comparison(
        custom_url_schemes_1, custom_url_schemes_2
    )
    app_link_matches = deep_link_comparison(app_links_1, app_links_2)

    cus_comparison = custom_url_scheme_matches / maxLength_cus
    app_link_comparison = app_link_matches / maxLength_al
    max_score = max(cus_comparison, app_link_comparison)

    return {
        #'deep_link_custom_url_scheme_comparison': cus_comparison,
        #'deep_link_scheme_calc': f'{custom_url_scheme_matches} out of max {maxLength_cus} match',
        #'deep_link_custom_url_scheme_android': sorted(list(custom_url_schemes_2)),
        #'deep_link_custom_url_scheme_ios': sorted(list(custom_url_schemes_1)),
        #'deep_link_app_link_comparison': app_link_comparison,
        #'deep_link_app_link_calc': f'{app_link_matches} out of max {maxLength_al} match',
        #'deep_link_app_link_android': sorted(list(app_links_2)),
        #'deep_link_app_link_ios': sorted(list(app_links_1)),
        "deep_link_max": max_score
    }


def match_icon_hash(
    ios_app: iOSPreprocessingResult, android_app: AndroidPreprocessingResult
):
    icon_hashes_ios = ios_app.icon
    icon_hashes_android = android_app.icon

    def _compare_hash(which: str) -> float:
        if icon_hashes_ios is None or icon_hashes_android is None:
            return 0
        return hash_compare(icon_hashes_ios[which], icon_hashes_android[which])

    # def _compare_multi_hash() -> float:
    #     if icon_hashes_ios is None or icon_hashes_android is None:
    #         return 0
    #     return hash_compare_multi(
    #         icon_hashes_ios["crhash"], icon_hashes_android["crhash"]
    #     )

    #crhash_score = _compare_multi_hash()
    #if crhash_score == 1:
    #    max_score = 1
    #else:
    ahash_score = _compare_hash("ahash")
    phash_score = _compare_hash("phash")
    whash_score = _compare_hash("whash")
    max_score = max(ahash_score, phash_score, whash_score)

    return {
        # "icon_hash_ahash_score": ahash_score,
        # "icon_hash_phash_score": phash_score,
        # "icon_hash_whash_score": whash_score,
        # "icon_hash_crhash_score": crhash_score,
        "icon_hash_max": max_score
    }

def match_language(ios_app: iOSPreprocessingResult, android_app: AndroidPreprocessingResult) -> dict[str, float]:
    ios_lang = ios_app.metadata.get('description_language')
    android_lang = android_app.metadata.get('description_language')

    return {
        "description_language_matches": ios_lang == android_lang
    }


def match_description(ios_index: int, android_index: int) -> dict[str, float]:
    description_similarity = get_similarities_sm()
    return {
        "description_cosine_similarity": description_similarity[
            ios_index, android_index
        ]
    }


def cleanup_tf_idf():
    cleanup_width_sm()
    cleanup_height_sm()
    cleanup_similarities_sm()


ALL_PREPARES = [prepare_ios_descriptions, prepare_tf_idf, prepare_image_hashes]
ALL_MATCHERS = [
    match_privacy_url,
    match_developer,
    # match_developer_url,
    match_app_name,
    match_app_id,
    match_deep_links,
    match_icon_hash,
]
ALL_WEIGHT_MODIFIERS = [
    match_language,
]
ALL_INDEXED_MATCHERS = [match_description]
ALL_CLEANUPS = [cleanup_tf_idf]
