"""
Bias detection lexicons and pattern definitions.
Contains word lists and patterns for identifying various types of bias.
"""

from typing import Dict, List, Set

# Emotional loading - words that carry strong emotional connotations
EMOTIONAL_LOADING = {
    "positive": [
        "amazing", "brilliant", "fantastic", "incredible", "outstanding",
        "spectacular", "phenomenal", "extraordinary", "magnificent", "superb",
        "wonderful", "marvelous", "excellent", "perfect", "flawless",
        "revolutionary", "breakthrough", "game-changing", "innovative"
    ],
    "negative": [
        "terrible", "horrible", "awful", "disastrous", "catastrophic",
        "devastating", "abysmal", "dreadful", "pathetic", "appalling",
        "shocking", "outrageous", "disgraceful", "shameful", "scandalous",
        "corrupt", "evil", "vile", "heinous", "atrocious"
    ],
    "fear_inducing": [
        "terrifying", "alarming", "dangerous", "threatening", "menacing",
        "scary", "frightening", "horrifying", "nightmare", "crisis",
        "emergency", "disaster", "doom", "apocalyptic", "catastrophe"
    ]
}

# Hedging - words that soften or qualify claims
HEDGE_WORDS = [
    # Modal verbs
    "might", "may", "could", "would", "should", "can",
    # Adverbs
    "possibly", "perhaps", "maybe", "probably", "likely",
    "potentially", "presumably", "supposedly", "allegedly",
    "apparently", "seemingly", "arguably",
    # Verbs
    "appears", "seems", "suggests", "indicates", "implies",
    "tends", "believes", "thinks", "feels", "estimates",
    # Phrases
    "it seems that", "it appears that", "one might say",
    "in some cases", "to some extent", "in a sense"
]

# Hyperbole - exaggerated language
HYPERBOLE_WORDS = [
    "always", "never", "everyone", "no one", "nobody", "everybody",
    "all", "none", "every", "any", "total", "complete", "absolute",
    "entirely", "completely", "totally", "utterly", "perfectly",
    "infinite", "endless", "eternal", "forever", "constantly",
    "literally", "actually", "really", "very", "extremely",
    "incredibly", "unbelievably", "impossibly"
]

# Ad hominem - personal attack indicators
AD_HOMINEM_PATTERNS = [
    # Direct attacks
    "idiots?", "fools?", "morons?", "stupid", "dumb", "ignorant",
    "clueless", "incompetent", "unqualified", "corrupt",
    # Dismissive language
    "so-called", "self-proclaimed", "wannabe", "fake",
    # Character attacks
    "liar", "dishonest", "untrustworthy", "biased", "partisan",
    # Group dismissals
    "shills?", "puppets?", "trolls?", "bots?"
]

# Weasel words - vague qualifiers
WEASEL_WORDS = [
    # Vague quantifiers
    "some people", "many", "most", "few", "several", "numerous",
    "a number of", "various", "certain", "particular",
    # Vague sources
    "sources say", "it is said", "reportedly", "allegedly",
    "critics say", "experts claim", "studies show",
    "research suggests", "some believe",
    # Vague qualifiers
    "up to", "as many as", "as few as", "more than",
    "less than", "approximately", "roughly", "about",
    "around", "nearly", "almost", "virtually"
]

# Loaded questions - presuppositional language
LOADED_QUESTION_PATTERNS = [
    # "When did you stop..." patterns
    r"when (did|will|do) (you|they|he|she)",
    # "Why don't you..." patterns
    r"why (don't|didn't|won't|doesn't|do not) (you|they|he|she)",
    # "How can you..." patterns
    r"how (can|could) (you|they|he|she) .+ (when|while|if)",
    # "Don't you think..." patterns
    r"(don't|doesn't|do not) (you|they) think",
]

# False balance - language suggesting artificial equivalence
FALSE_BALANCE_INDICATORS = [
    "both sides", "on the other hand", "however", "some say",
    "debate", "controversy", "disputed", "questioned",
    "critics argue", "proponents claim", "equal time",
    "fair and balanced", "he said she said"
]

# Cherry-picking - selective presentation indicators
CHERRY_PICKING_INDICATORS = [
    "hand-picked", "selected", "chosen", "specific", "particular",
    "certain examples", "one study", "a single", "anecdotal",
    "for instance", "for example", "such as", "including",
    "notably", "especially", "in particular"
]

# Neutral/objective language (positive indicators)
NEUTRAL_LANGUAGE = {
    "reporting_verbs": [
        "said", "stated", "reported", "announced", "declared",
        "noted", "mentioned", "indicated", "explained", "described"
    ],
    "scientific_terms": [
        "data", "evidence", "research", "study", "analysis",
        "findings", "results", "methodology", "peer-reviewed",
        "published", "journal", "statistical", "empirical"
    ],
    "objective_qualifiers": [
        "according to", "based on", "as measured by",
        "as defined by", "in comparison to", "relative to"
    ]
}

# Domain-specific bias patterns
DOMAIN_BIAS = {
    "political": {
        "left_leaning": [
            "progressive", "liberal", "socialist", "equality",
            "social justice", "diversity", "inclusion"
        ],
        "right_leaning": [
            "conservative", "traditional", "free market",
            "liberty", "individual rights", "small government"
        ]
    },
    "commercial": {
        "promotional": [
            "buy", "purchase", "discount", "sale", "offer",
            "limited time", "exclusive", "premium", "best"
        ]
    },
    "sensational": {
        "clickbait": [
            "you won't believe", "shocking", "secret", "exposed",
            "truth about", "what they don't want you to know",
            "doctors hate", "one weird trick"
        ]
    }
}


def get_all_bias_lexicons() -> Dict[str, any]:
    """
    Get all bias detection lexicons.

    Returns:
        Dictionary of all lexicons
    """
    return {
        "emotional_loading": EMOTIONAL_LOADING,
        "hedge_words": HEDGE_WORDS,
        "hyperbole": HYPERBOLE_WORDS,
        "ad_hominem": AD_HOMINEM_PATTERNS,
        "weasel_words": WEASEL_WORDS,
        "loaded_questions": LOADED_QUESTION_PATTERNS,
        "false_balance": FALSE_BALANCE_INDICATORS,
        "cherry_picking": CHERRY_PICKING_INDICATORS,
        "neutral_language": NEUTRAL_LANGUAGE,
        "domain_bias": DOMAIN_BIAS
    }


def get_bias_weights() -> Dict[str, float]:
    """
    Get weights for different bias types (impact on overall bias score).

    Returns:
        Dictionary mapping bias type to weight
    """
    return {
        "emotional_loading": 0.8,
        "hedge_words": 0.3,  # Less severe
        "hyperbole": 0.7,
        "ad_hominem": 1.0,  # Most severe
        "weasel_words": 0.6,
        "loaded_questions": 0.8,
        "false_balance": 0.5,
        "cherry_picking": 0.6
    }


def get_neutrality_bonus() -> Dict[str, float]:
    """
    Get bonus points for neutral/objective language.

    Returns:
        Dictionary of neutrality bonuses
    """
    return {
        "reporting_verbs": 0.05,
        "scientific_terms": 0.08,
        "objective_qualifiers": 0.06
    }
