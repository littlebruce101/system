"""
Claim extraction patterns for identifying factual statements in text.
Uses spaCy's Matcher and DependencyMatcher for linguistic pattern matching.
"""

from typing import Dict, List


# Statistical Claims - numerical facts and statistics
STATISTICAL_PATTERNS = [
    # "X% of Y" or "X percent of Y"
    [
        {"LIKE_NUM": True},
        {"LOWER": {"IN": ["%", "percent", "percentage"]}},
        {"LOWER": "of"},
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}
    ],
    # "X increased/decreased by Y"
    [
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"},
        {"LEMMA": {"IN": ["increase", "decrease", "rise", "fall", "grow", "decline", "drop"]}},
        {"LOWER": "by"},
        {"LIKE_NUM": True}
    ],
    # "X million/billion/trillion Y"
    [
        {"LIKE_NUM": True},
        {"LOWER": {"IN": ["million", "billion", "trillion", "thousand"]}},
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}
    ],
    # "more than X" or "less than X"
    [
        {"LOWER": {"IN": ["more", "less", "fewer", "over", "under"]}},
        {"LOWER": "than"},
        {"LIKE_NUM": True}
    ]
]

# Causal Claims - cause and effect relationships
CAUSAL_PATTERNS = [
    # "X causes Y"
    [
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"},
        {"LEMMA": {"IN": ["cause", "lead", "result", "produce", "create", "trigger"]}},
        {"LOWER": {"IN": ["to", "in"]}, "OP": "?"},
        {"POS": {"IN": ["NOUN", "PROPN", "VERB"]}, "OP": "+"}
    ],
    # "because of X" or "due to X"
    [
        {"LOWER": {"IN": ["because", "due"]}},
        {"LOWER": {"IN": ["of", "to"]}},
        {"POS": {"IN": ["NOUN", "PROPN", "DET"]}, "OP": "+"}
    ],
    # "X is responsible for Y"
    [
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"},
        {"LEMMA": "be"},
        {"LOWER": "responsible"},
        {"LOWER": "for"},
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}
    ],
    # "If X then Y"
    [
        {"LOWER": "if"},
        {"IS_ALPHA": True, "OP": "+"},
        {"LOWER": {"IN": ["then", ","]}},
        {"IS_ALPHA": True, "OP": "+"}
    ]
]

# Temporal Claims - time-specific statements
TEMPORAL_PATTERNS = [
    # "in [year]" or "on [date]"
    [
        {"LOWER": {"IN": ["in", "on", "during", "by", "since", "until"]}},
        {"ENT_TYPE": {"IN": ["DATE", "TIME"]}, "OP": "+"}
    ],
    # "[Entity] will [verb]" (future predictions)
    [
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"},
        {"LEMMA": "will"},
        {"POS": "VERB"}
    ],
    # "has been [adj] since [date]"
    [
        {"LEMMA": "have"},
        {"LEMMA": "be"},
        {"POS": {"IN": ["ADJ", "VERB"]}},
        {"LOWER": "since"},
        {"ENT_TYPE": "DATE", "OP": "+"}
    ]
]

# Definitional Claims - statements about what things are
DEFINITIONAL_PATTERNS = [
    # "X is Y" (simple definitions)
    [
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"},
        {"LEMMA": "be"},
        {"POS": {"IN": ["DET", "ADJ"]}, "OP": "*"},
        {"POS": {"IN": ["NOUN", "PROPN", "ADJ"]}, "OP": "+"}
    ],
    # "X refers to Y" or "X means Y"
    [
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"},
        {"LEMMA": {"IN": ["refer", "mean", "define", "describe", "denote"]}},
        {"LOWER": {"IN": ["to", "as"]}, "OP": "?"},
        {"POS": {"IN": ["NOUN", "PROPN", "DET"]}, "OP": "+"}
    ]
]

# Comparative Claims - comparisons between entities
COMPARATIVE_PATTERNS = [
    # "X is [comparative adj] than Y"
    [
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"},
        {"LEMMA": "be"},
        {"TAG": {"IN": ["JJR", "RBR"]}},  # Comparative adjective/adverb
        {"LOWER": "than"},
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}
    ],
    # "X compared to Y"
    [
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"},
        {"LEMMA": {"IN": ["compare", "contrast"]}},
        {"LOWER": {"IN": ["to", "with"]}},
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}
    ]
]

# Attribution Claims - statements attributed to sources
ATTRIBUTION_PATTERNS = [
    # "According to X"
    [
        {"LOWER": "according"},
        {"LOWER": "to"},
        {"POS": {"IN": ["NOUN", "PROPN", "DET"]}, "OP": "+"}
    ],
    # "X said/reported/claimed"
    [
        {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"},
        {"LEMMA": {"IN": ["say", "report", "claim", "state", "announce", "assert"]}},
        {"LOWER": "that", "OP": "?"}
    ],
    # "studies show" or "research indicates"
    [
        {"LOWER": {"IN": ["studies", "research", "data", "evidence"]}},
        {"LEMMA": {"IN": ["show", "indicate", "suggest", "demonstrate", "reveal"]}},
        {"LOWER": "that", "OP": "?"}
    ]
]

# Entity-specific patterns for extracting named entities involved in claims
ENTITY_PATTERNS = {
    "PERSON": ["CEO", "President", "scientist", "researcher", "expert"],
    "ORG": ["Company", "University", "Institute", "Organization", "Government"],
    "GPE": ["Country", "City", "State"],
    "DATE": ["year", "month", "day", "quarter"],
    "MONEY": ["dollar", "euro", "pound"],
    "PERCENT": ["percent", "percentage"],
    "CARDINAL": ["million", "billion", "trillion"]
}


def get_all_patterns() -> Dict[str, List[List[Dict]]]:
    """
    Returns all claim extraction patterns organized by type.

    Returns:
        Dictionary mapping claim type to pattern lists
    """
    return {
        "statistical": STATISTICAL_PATTERNS,
        "causal": CAUSAL_PATTERNS,
        "temporal": TEMPORAL_PATTERNS,
        "definitional": DEFINITIONAL_PATTERNS,
        "comparative": COMPARATIVE_PATTERNS,
        "attribution": ATTRIBUTION_PATTERNS
    }


def get_high_confidence_keywords() -> Dict[str, List[str]]:
    """
    Returns keywords that indicate high-confidence factual claims.
    These boost the claim extraction confidence score.

    Returns:
        Dictionary of keyword categories
    """
    return {
        "quantitative": [
            "percent", "percentage", "million", "billion", "trillion",
            "increase", "decrease", "growth", "decline", "rate"
        ],
        "temporal": [
            "year", "month", "day", "since", "until", "during",
            "will", "has been", "was", "were"
        ],
        "causal": [
            "causes", "leads to", "results in", "due to", "because of",
            "responsible for", "triggers", "produces"
        ],
        "attribution": [
            "according to", "reported", "announced", "confirmed",
            "studies show", "research indicates", "data shows"
        ],
        "definitive": [
            "is", "are", "was", "were", "defined as", "refers to",
            "means", "represents"
        ]
    }


def get_hedge_words() -> List[str]:
    """
    Returns hedge words that reduce claim confidence.
    These indicate uncertainty or speculation.

    Returns:
        List of hedge words
    """
    return [
        "might", "may", "could", "possibly", "perhaps", "maybe",
        "appears", "seems", "suggests", "indicates", "likely",
        "probably", "presumably", "supposedly", "allegedly",
        "reportedly", "apparently"
    ]
