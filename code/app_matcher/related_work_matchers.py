import difflib
import os
import re
import glob

from unidecode import unidecode
from app_matcher.matchers import (
    cleanup_tf_idf,
    prepare_ios_descriptions,
    prepare_tf_idf,
)
from database.analysis_results.preprocessing_result.android_preprocessing_result.android_preprocessing_result import (
    AndroidPreprocessingResult,
)
from database.analysis_results.preprocessing_result.ios_preprocessing_result.ios_preprocessing_result import (
    iOSPreprocessingResult,
)

from .tf_idf.tf_idf_shared_memory import get_similarities_sm

WORD_LIST_DIR = "./app_matcher/stop_word_lists"  # relative to xpa


def prepare_hu_strings(
    ios_apps: list[iOSPreprocessingResult],
    android_apps: list[AndroidPreprocessingResult],
) -> None:
    #### load stop words #####
    stop_words = set()
    for file in glob.glob(os.path.join(WORD_LIST_DIR, "*")):
        print(file)
        if file.endswith("README"):
            continue
        else:
            with open(file, "r") as fp:
                for word in fp.readlines():
                    stop_words.add(word.strip())
    ##########################

    for ios_app in ios_apps:
        ios_title = ios_app.metadata.get("name", "")
        ios_developer_name = ios_app.metadata.get("developer_name", "")

        # preprocessing
        # translate non-English characters and set everything to lower case
        ios_title = unidecode(ios_title).lower()
        ios_developer_name = unidecode(ios_developer_name).lower()
        # remove everything that is not a-z or 0-9 or spaces
        ios_title = re.sub(r"[^\w]", "", ios_title)
        ios_developer_name = re.sub(r"[^\w]", "", ios_developer_name)
        # remove stop words from developer names, e.g., "co", "ltd"
        # note that use a german word list, as we scraped german stores
        ios_developer_name = ios_developer_name.split()
        ios_developer_result = [
            word for word in ios_developer_name if word not in stop_words
        ]
        ios_developer_name = " ".join(ios_developer_result)

        ios_app.metadata["name_hu"] = ios_title
        ios_app.metadata["developer_name_hu"] = ios_developer_name

    for android_app in android_apps:
        android_title = android_app.metadata.get("app_name", "")
        android_developer_name = android_app.metadata.get("developer_name", "")
        # preprocessing
        # translate non-English characters and set everything to lower case
        android_title = unidecode(android_title).lower()
        android_developer_name = unidecode(android_developer_name).lower()
        # remove everything that is not a-z or 0-9 or spaces
        android_title = re.sub(r"[^\w]", "", android_title)
        android_developer_name = re.sub(r"[^\w]", "", android_developer_name)
        # remove stop words from developer names, e.g., "co", "ltd"
        # note that use a german word list, as we scraped german stores
        android_developer_name = android_developer_name.split()
        android_developer_result = [
            word for word in android_developer_name if word not in stop_words
        ]
        android_developer_name = " ".join(android_developer_result)

        android_app.metadata["app_name_hu"] = android_title
        android_app.metadata["developer_name_hu"] = android_developer_name


# implementation of exact matches based on
# Mohamed Ali, Mona Erfani Joorabchi, and Ali Mesbah. 2017. Same App, Different App Stores: A Comparative Study. In Proceedings of the 2017 IEEE/ACM 4th International Conference on Mobile Software Engineering and Systems (MOBILESoft 2017). IEEE, Los Alamitos, CA, USA. https://doi.org/10.1109/MOBILESoft.2017.32, 3, 5
def ali_exact_match(
    ios_app: iOSPreprocessingResult, android_app: AndroidPreprocessingResult
) -> dict[str, float]:
    ios_title = ios_app.metadata.get("name", "")
    android_title = re.escape(android_app.metadata.get("app_name", ""))
    ios_developer_name = ios_app.metadata.get("developer_name", "")
    android_developer_name = re.escape(android_app.metadata.get("developer_name", ""))

    # source: https://github.com/saltlab/Minning-App-Stores/blob/master/scripts/createAppPairs/mergeExactName-Dev.py
    title_regx = re.compile("^" + android_title + "$", re.IGNORECASE)
    dev_regx = re.compile("^" + android_developer_name + "$", re.IGNORECASE)

    match_title = len(re.findall(title_regx, ios_title))
    match_developer = len(re.findall(dev_regx, ios_developer_name))

    if match_title > 0 and match_developer > 0:
        return {"ali_exact_match": 1.0}
    else:
        return {"ali_exact_match": 0.0}


def ali_exact_match_fixed(
    ios_app: iOSPreprocessingResult, android_app: AndroidPreprocessingResult
) -> dict[str, float]:
    ios_title = ios_app.metadata.get("name", "")
    android_title = android_app.metadata.get("app_name", "")
    ios_developer_name = ios_app.metadata.get("developer_name", "")
    android_developer_name = android_app.metadata.get("developer_name", "")

    match_title = ios_title.lower() == android_title.lower()
    match_developer = ios_developer_name.lower() == android_developer_name.lower()

    if match_title and match_developer:
        return {"ali_exact_match_fixed": 1.0}
    else:
        return {"ali_exact_match_fixed": 0.0}


# implementation of cross platform app matching based on
# Jin Han, Qiang Yan, Debin Gao, Jianying Zhou, and Robert Deng. 2013. Comparing Mobile Privacy Protection through Cross-Platform Applications. In Proceedings of the 20th Annual Network & Distributed System Security Symposium (NDSS ’13). Internet Society, Reston, VA, USA. https://www.ndss-symposium.org/ndss2013/ndss-2013-programme/comparing-mobile-privacy-protection-through-cross-platform-applications/ 2,3, 5
# we used our tf-idf setup as tf-idf is a weighting scheme for the Vector Space Model and the paper did not provide any source code
def han_exact_match_similar_description(
    ios_app: iOSPreprocessingResult,
    android_app: AndroidPreprocessingResult,
    ios_index: int,
    android_index: int,
) -> dict[str, float]:
    ios_title = ios_app.metadata.get("name", "")
    android_title = android_app.metadata.get("app_name", "")
    ios_developer_name = ios_app.metadata.get("developer_name", "")
    android_developer_name = android_app.metadata.get("developer_name", "")

    description_similarity = get_similarities_sm()[ios_index, android_index]

    match_title = ios_title.lower() == android_title.lower()
    match_develper_name = ios_developer_name.lower() == android_developer_name.lower()

    if match_title and match_develper_name and description_similarity >= 0.45:
        return {"han_exact_match_similar_description": 1.0}
    else:
        return {"han_exact_match_similar_description": 0.0}


# implementation of cross platform app matching based on


# we had to make assumptions regarding the preprocessing, as the code is not available and the paper does not discuss which stop word list was used.
def hu_similarity_match(
    ios_app: iOSPreprocessingResult, android_app: AndroidPreprocessingResult
) -> dict[str, float]:
    ios_title = ios_app.metadata.get("name_hu", "")
    android_title = android_app.metadata.get("app_name_hu", "")
    ios_developer_name = ios_app.metadata.get("developer_name_hu", "")
    android_developer_name = android_app.metadata.get("developer_name_hu", "")

    if ios_title == android_title and ios_developer_name == android_developer_name:
        return {"hu_similarity_match": 1.0}

    similarity_score = (
        0.8 * difflib.SequenceMatcher(a=ios_title, b=android_title).ratio()
        + 0.2
        * difflib.SequenceMatcher(
            a=ios_developer_name, b=android_developer_name
        ).ratio()
    )

    return {"hu_similarity_match": 0 if similarity_score <= 0.6 else similarity_score}


ALI_ET_AL_MATCHERS = [ali_exact_match, ali_exact_match_fixed]
HAN_ET_AL_MATCHERS = [han_exact_match_similar_description]
HU_ET_AL_MATCHERS = [hu_similarity_match]

RELATED_WORK_PREPARES = [prepare_ios_descriptions, prepare_tf_idf, prepare_hu_strings]
RELATED_WORK_MATCHERS = ALI_ET_AL_MATCHERS + HU_ET_AL_MATCHERS
RELATED_WORK_INDEX_MATCHERS = HAN_ET_AL_MATCHERS
RELATED_WORK_CLEANUP = [cleanup_tf_idf]
