# -*- coding: utf-8 -*-
"""
Test data for Event Trigger Agent evaluation.
Contains robustness and scalability test cases with realistic data structures.
"""

from datetime import datetime

# ===== REUSABLE EVENT DEFINITIONS =====

# Core events used across multiple test cases
CORE_EVENTS = {
    "btc_creator_discovery": {
        "eventId": "btc_creator_discovery_001",
        "title": "BTC Creator is discovered",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 8),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "eth_foundation_shutdown": {
        "eventId": "eth_foundation_shutdown_001",
        "title": "Ethereum Foundation disappear",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 12),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "major_exchange_hack": {
        "eventId": "major_exchange_hack_001",
        "title": "Major crypto exchange hack",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 10),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "sec_crypto_ban": {
        "eventId": "sec_crypto_ban_001",
        "title": "SEC bans all cryptocurrencies",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 11),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "tether_collapse": {
        "eventId": "tether_collapse_001",
        "title": "Tether (USDT) collapses",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 13),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "trump_tariff_india_russia": {
        "eventId": "trump_tariff_india_russia_001",
        "title": "Higher than 20% tariff on India by US",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 14),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "fed_interest_below_expectations": {
        "eventId": "fed_rate_below_expectations_001",
        "title": "Fed Interest Rate Decision below expectations",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 14),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "inflation_below_expectations": {
        "eventId": "inflation_below_expectations_001",
        "title": "US inflation data comes in below expectations",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 13),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "inflation_above_expectations": {
        "eventId": "inflation_above_expectations_001",
        "title": "US inflation data comes in above expectations",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 13),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "july_cpi_above_expectations": {
        "eventId": "july_cpi_above_expectations_001",
        "title": "July Consumer Price Index > 2.7%",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 13),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "july_cpi_below_expectations": {
        "eventId": "july_cpi_below_expectations_001",
        "title": "July Consumer Price Index < 2.7%",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 13),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "thailand_cpi_fall": {
        "eventId": "thailand_cpi_fall_001",
        "title": "Thailand's Consumer Price Index decreases.",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 13),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "jobless_claims_above_215k": {
        "eventId": "jobless_claims_above_215k_001",
        "title": "Initial Jobless Claims August Above 215K",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 13),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
}

# Additional distractor events
DISTRACTOR_EVENTS = {
    "dogecoin_moon": {
        "eventId": "dogecoin_moon_001",
        "title": "Dogecoin reaches $1",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 5),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "elon_twitter_bitcoin": {
        "eventId": "elon_buys_twitter_001",
        "title": "Elon Musk announces X (Twitter) will accept Bitcoin",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 6),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "quantum_breaks_crypto": {
        "eventId": "quantum_breaks_crypto_001",
        "title": "Quantum computer breaks Bitcoin encryption",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 7),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "china_unbans_crypto": {
        "eventId": "china_unbans_crypto_001",
        "title": "China reverses crypto ban",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 4),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "solana_flippening": {
        "eventId": "solana_flippening_001",
        "title": "Solana flippening Ethereum",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 3),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
}

# World political and war-related events
WORLD_EVENTS = {
    "palestine_israel_conflict": {
        "eventId": "palestine_israel_conflict_001",
        "title": "Palestine launches major attack on Israel",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 15),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "south_korea_nuclear_001": {
        "eventId": "south_korea_nuclear_001",
        "title": "South Korea attacks Japan",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 16),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "japan_president_crypto_fraud_001": {
        "eventId": "japan_president_crypto_fraud_001",
        "title": "Japan President arrested for crypto fraud",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 17),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "syria_turkey_attack_001": {
        "eventId": "syria_turkey_attack_001",
        "title": "Syria launches missile attack on Turkey",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 18),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "russia_ukraine_escalation_001": {
        "eventId": "russia_ukraine_escalation_001",
        "title": "Russia escalates war in Ukraine with nuclear threat",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 19),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "india_pakistan_peace_announcement_001": {
        "eventId": "india_pakistan_peace_announcement_001",
        "title": "India and Pakistan announce peace agreement",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 20),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "iran_saudi_war_001": {
        "eventId": "iran_saudi_war_001",
        "title": "Iran declares war on Saudi Arabia",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 21),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "north_korea_missile_test_001": {
        "eventId": "north_korea_missile_test_001",
        "title": "North Korea tests ICBM over Japan",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 22),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "india_pakistan_border_conflict_001": {
        "eventId": "india_pakistan_border_conflict_001",
        "title": "Pakistan and India border conflict started.",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 24),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "russia_ukraine_ceasefire_001": {
        "eventId": "russia_ukraine_ceasefire_001",
        "title": "Russia x Ukraine ceasefire",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 23),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
    "india_pakistan_nuclear_001": {
        "eventId": "india_pakistan_nuclear_001",
        "title": "India and Pakistan exchange nuclear threats",
        "longTrades": [],
        "shortTrades": [],
        "eventTime": None,
        "closingTime": None,
        "createdAt": datetime(2024, 1, 24),
        "executionTime": None,
        "executed": False,
        "tradeStatus": "pending",
        "tweetBased": True,
    },
}

# Event arrays for scalability testing
SINGLE_EVENT = [CORE_EVENTS["major_exchange_hack"]]

FIVE_EVENTS = [
    CORE_EVENTS["major_exchange_hack"],
    CORE_EVENTS["btc_creator_discovery"],
    CORE_EVENTS["eth_foundation_shutdown"],
    CORE_EVENTS["sec_crypto_ban"],
    CORE_EVENTS["tether_collapse"],
]

TEN_EVENTS = [
    *FIVE_EVENTS,
    DISTRACTOR_EVENTS["dogecoin_moon"],
    DISTRACTOR_EVENTS["elon_twitter_bitcoin"],
    DISTRACTOR_EVENTS["quantum_breaks_crypto"],
    DISTRACTOR_EVENTS["china_unbans_crypto"],
    DISTRACTOR_EVENTS["solana_flippening"],
]

TWENTY_EVENTS = [
    *TEN_EVENTS,
    WORLD_EVENTS["palestine_israel_conflict"],
    WORLD_EVENTS["south_korea_nuclear_001"],
    WORLD_EVENTS["japan_president_crypto_fraud_001"],
    WORLD_EVENTS["syria_turkey_attack_001"],
    WORLD_EVENTS["russia_ukraine_escalation_001"],
    WORLD_EVENTS["india_pakistan_peace_announcement_001"],
    WORLD_EVENTS["iran_saudi_war_001"],
    WORLD_EVENTS["north_korea_missile_test_001"],
    WORLD_EVENTS["india_pakistan_border_conflict_001"],
    WORLD_EVENTS["russia_ukraine_ceasefire_001"],
    WORLD_EVENTS["india_pakistan_nuclear_001"],
]

# Robustness test cases - testing agent's ability to handle edge cases
ROBUSTNESS_TEST_CASES = [
    {
        "name": "sarcasm_detection",
        "description": "Agent should not trigger on sarcastic tweets",
        "tweet": {
            "text": "Oh wow, Satoshi Nakamoto just revealed himself to me in my dreams!  What a joke, crypto bros will believe anything these days",
            "username": "cryptoskeptic",
            "created_at": "2024-01-15T10:30:00Z",
            "id": "test_sarcasm_001",
        },
        "events": [CORE_EVENTS["btc_creator_discovery"]],
        "expected_triggers": [],  # Should NOT trigger
    },
    {
        "name": "price_discussion_confusion",
        "description": "Agent should not confuse price discussions with actual events",
        "tweet": {
            "text": "Bitcoin technical analysis shows strong resistance at $45k. If we break through, could see massive gains. Chart patterns looking bullish! ",
            "username": "cryptotrader_pro",
            "created_at": "2024-01-15T14:22:00Z",
            "id": "test_price_001",
        },
        "events": [
            CORE_EVENTS["btc_creator_discovery"],
            CORE_EVENTS["eth_foundation_shutdown"],
        ],
        "expected_triggers": [],  # Should NOT trigger
    },
    {
        "name": "ambiguous_announcement",
        "description": "Agent should handle vague announcements carefully",
        "tweet": {
            "text": "BREAKING: Major announcement coming from Ethereum Foundation tomorrow. This will change everything in crypto. Stay tuned!",
            "username": "cryptonews_insider",
            "created_at": "2024-01-15T16:45:00Z",
            "id": "test_ambiguous_001",
        },
        "events": [
            CORE_EVENTS["eth_foundation_shutdown"],
        ],
        "expected_triggers": [],  # Too vague, should NOT trigger
    },
    {
        "name": "fed_rate_opposite_condition",
        "description": "Agent should not trigger if announcement goes against expected direction",
        "tweet": {
            "text": "BREAKING: Federal Reserve raises interest rates by 0.75% - ABOVE market expectations of 0.5%. Markets tumbling on hawkish surprise! #Fed #InterestRates",
            "username": "fed_reporter",
            "created_at": "2024-01-15T18:00:00Z",
            "id": "test_fed_above_001",
        },
        "events": [CORE_EVENTS["fed_interest_below_expectations"]],
        "expected_triggers": [],  # Should NOT trigger (rate was ABOVE, not below)
    },
    {
        "name": "inflation_data_opposite_condition",
        "description": "Agent should only trigger event which announcement goes in the expected direction",
        "tweet": {
            "text": "US inflation data just released: CPI came in at 3.8%, significantly higher than economist forecasts of 3.2%. Crypto markets reacting negatively.",
            "username": "economic_data",
            "created_at": "2024-01-15T13:30:00Z",
            "id": "test_inflation_higher_001",
        },
        "events": [
            CORE_EVENTS["inflation_above_expectations"],
            CORE_EVENTS["inflation_below_expectations"],
        ],
        "expected_triggers": [
            {
                "eventId": "inflation_above_expectations_001",
                "tweetContent": "US inflation data just released: CPI came in at 3.8%, significantly higher than economist forecasts of 3.2%. Crypto markets reacting negatively.",
                "username": "economic_data",
                "tweetId": "test_inflation_higher_001",
            }
        ],  # Should trigger (inflation was HIGHER, not below)
    },
    {
        "name": "sui_etf_opposite_condition",
        "description": "Agent should not trigger event if announcement is completely opposite of expected.",
        "tweet": {
            "text": "JUST IN: SEC REJECTS SUI ETF application from BlackRock. Commissioner cites 'market manipulation concerns' and 'insufficient investor protections'",
            "username": "sec_news",
            "created_at": "2024-01-15T15:45:00Z",
            "id": "test_etf_rejected_001",
        },
        "events": [
            {
                "eventId": "sui_etf_approved_001",
                "title": "SUI ETF gets approved by SEC",
                "longTrades": [],
                "shortTrades": [],
                "eventTime": None,
                "closingTime": None,
                "createdAt": datetime(2024, 1, 12),
                "executionTime": None,
                "executed": False,
                "tradeStatus": "pending",
                "tweetBased": True,
            }
        ],
        "expected_triggers": [],  # Should NOT trigger (ETF was REJECTED, not approved)
    },
    {
        "name": "economic_data_other_country",
        "description": "Agent should not trigger event if information is not related to that country",
        "tweet": {
            "text": "Ghana’s inflation rate fell more than expected in July, bolstering the case for further interest-rate cuts",
            "username": "bloomberg",
            "created_at": "2024-01-15T15:45:00Z",
            "id": "economic_ghana_tweet",
        },
        "events": [
            CORE_EVENTS["july_cpi_above_expectations"],
            CORE_EVENTS["july_cpi_below_expectations"],
            CORE_EVENTS["fed_interest_below_expectations"],
            CORE_EVENTS["trump_tariff_india_russia"],
            DISTRACTOR_EVENTS["dogecoin_moon"],
            DISTRACTOR_EVENTS["elon_twitter_bitcoin"],
            DISTRACTOR_EVENTS["quantum_breaks_crypto"],
            DISTRACTOR_EVENTS["china_unbans_crypto"],
            DISTRACTOR_EVENTS["solana_flippening"],
        ],
        "expected_triggers": [],  # Should NOT trigger (It's not US inflation rate)
    },
    {
        "name": "economic_data_other_country_2",
        "description": "Agent should not trigger event if information is not related to that country",
        "tweet": {
            "text": "Thailand's consumer price index fell the most since early 2024 as energy costs remained subdued and utility tariffs dropped, providing the central bank more room to weigh monetary easing at its meeting next week.",
            "username": "bloomberg",
            "created_at": "2024-01-15T15:45:00Z",
            "id": "economic_thailand_tweet",
        },
        "events": [
            CORE_EVENTS["july_cpi_above_expectations"],
            CORE_EVENTS["july_cpi_below_expectations"],
            CORE_EVENTS["fed_interest_below_expectations"],
            CORE_EVENTS["thailand_cpi_fall"],
            CORE_EVENTS["trump_tariff_india_russia"],
            DISTRACTOR_EVENTS["dogecoin_moon"],
            DISTRACTOR_EVENTS["elon_twitter_bitcoin"],
            DISTRACTOR_EVENTS["quantum_breaks_crypto"],
            DISTRACTOR_EVENTS["china_unbans_crypto"],
            DISTRACTOR_EVENTS["solana_flippening"],
        ],
        "expected_triggers": [
            {
                "eventId": "thailand_cpi_fall_001",
                "tweetContent": "Thailand's consumer price index fell the most since early 2024 as energy costs remained subdued and utility tariffs dropped, providing the central bank more room to weigh monetary easing at its meeting next week.",
                "username": "bloomberg",
                "tweetId": "economic_thailand_tweet",
            }
        ],  # Should only trigger thailand cpi event (not US event)
    },
    {
        "name": "economic_non_us_data",
        "description": "Agent should trigger event if economic data is relevant to that country",
        "tweet": {
            "text": "Thailand's consumer price index fell the most since early 2024 as energy costs remained subdued and utility tariffs dropped, providing the central bank more room to weigh monetary easing at its meeting next week.",
            "username": "bloomberg",
            "created_at": "2024-01-15T15:45:00Z",
            "id": "economic_thailand_tweet",
        },
        "events": [
            CORE_EVENTS["july_cpi_above_expectations"],
            CORE_EVENTS["july_cpi_below_expectations"],
            CORE_EVENTS["fed_interest_below_expectations"],
            CORE_EVENTS["trump_tariff_india_russia"],
            DISTRACTOR_EVENTS["dogecoin_moon"],
            DISTRACTOR_EVENTS["elon_twitter_bitcoin"],
            DISTRACTOR_EVENTS["quantum_breaks_crypto"],
            DISTRACTOR_EVENTS["china_unbans_crypto"],
            DISTRACTOR_EVENTS["solana_flippening"],
        ],
        "expected_triggers": [],  # Should NOT trigger (It's not US inflation rate)
    },
    {
        "name": "unclear_data_economic_indicator",
        "description": "Agent should not trigger event if the data is not clearly mentioned in the tweet",
        "tweet": {
            "text": "Donald Trump's move to fire the head of the US Bureau of Labor Statistics has put trust in US data reporting mechanisms on the line just as demand for reliable diagnoses of the health of the world's largest economy is bigger than ever.",
            "username": "bloomberg",
            "created_at": "2024-01-15T19:15:00Z",
            "id": "test_data_economic_001",
        },
        "events": [
            CORE_EVENTS["july_cpi_above_expectations"],
            CORE_EVENTS["jobless_claims_above_215k"],
            CORE_EVENTS["july_cpi_below_expectations"],
            CORE_EVENTS["fed_interest_below_expectations"],
            CORE_EVENTS["trump_tariff_india_russia"],
            DISTRACTOR_EVENTS["dogecoin_moon"],
            DISTRACTOR_EVENTS["elon_twitter_bitcoin"],
            DISTRACTOR_EVENTS["quantum_breaks_crypto"],
            DISTRACTOR_EVENTS["china_unbans_crypto"],
            DISTRACTOR_EVENTS["solana_flippening"],
        ],
        "expected_triggers": [],
    },
    {
        "name": "multiple_events_sec_crypto_ban_and_thether_collapse",
        "description": "Agent should trigger multiple events if multiple events are mentioned in the tweet",
        "tweet": {
            "text": "SEC announces COMPLETE BAN on all cryptocurrencies. In response, Tether (USDT) loses peg and crashes to $0.25 as massive selloff begins. Crypto markets in freefall!",
            "username": "regulatory_news",
            "created_at": "2024-01-15T21:30:00Z",
            "id": "test_multiple_sec_usdt_001",
        },
        "events": [
            CORE_EVENTS["sec_crypto_ban"],
            CORE_EVENTS["tether_collapse"],
            CORE_EVENTS["major_exchange_hack"],  # Should NOT trigger this one
            CORE_EVENTS["eth_foundation_shutdown"],  # Should NOT trigger this one
            WORLD_EVENTS["palestine_israel_conflict"],  # Should NOT trigger this one
            WORLD_EVENTS["south_korea_nuclear_001"],  # Should NOT trigger this one
        ],
        "expected_triggers": [
            {
                "eventId": "sec_crypto_ban_001",
                "tweetContent": "SEC announces COMPLETE BAN on all cryptocurrencies. In response, Tether (USDT) loses peg and crashes to $0.25 as massive selloff begins. Crypto markets in freefall!",
                "username": "regulatory_news",
                "tweetId": "test_multiple_sec_usdt_001",
            },
            {
                "eventId": "tether_collapse_001",
                "tweetContent": "SEC announces COMPLETE BAN on all cryptocurrencies. In response, Tether (USDT) loses peg and crashes to $0.25 as massive selloff begins. Crypto markets in freefall!",
                "username": "regulatory_news",
                "tweetId": "test_multiple_sec_usdt_001",
            },
        ],
    },
    {
        "name": "multiple_events_btc_creator_eth_foundation",
        "description": "Agent should trigger multiple events if multiple events are mentioned in the tweet (2)",
        "tweet": {
            "text": "HISTORIC DAY: Satoshi Nakamoto's identity REVEALED as Dr. John Smith. Meanwhile, Ethereum Foundation announces IMMEDIATE DISSOLUTION following internal conflicts. Vitalik confirms end of centralized ETH development. Crypto world shaken!",
            "username": "crypto_breaking_news",
            "created_at": "2024-01-15T19:15:00Z",
            "id": "test_multiple_btc_eth_001",
        },
        "events": [
            CORE_EVENTS["btc_creator_discovery"],
            CORE_EVENTS["eth_foundation_shutdown"],
            CORE_EVENTS["major_exchange_hack"],  # Should NOT trigger this one
            DISTRACTOR_EVENTS["dogecoin_moon"],  # Should NOT trigger this one
            DISTRACTOR_EVENTS["elon_twitter_bitcoin"],  # Should NOT trigger this one
        ],
        "expected_triggers": [
            {
                "eventId": "btc_creator_discovery_001",
                "tweetContent": "HISTORIC DAY: Satoshi Nakamoto's identity REVEALED as Dr. John Smith. Meanwhile, Ethereum Foundation announces IMMEDIATE DISSOLUTION following internal conflicts. Vitalik confirms end of centralized ETH development. Crypto world shaken!",
                "username": "crypto_breaking_news",
                "tweetId": "test_multiple_btc_eth_001",
            },
            {
                "eventId": "eth_foundation_shutdown_001",
                "tweetContent": "HISTORIC DAY: Satoshi Nakamoto's identity REVEALED as Dr. John Smith. Meanwhile, Ethereum Foundation announces IMMEDIATE DISSOLUTION following internal conflicts. Vitalik confirms end of centralized ETH development. Crypto world shaken!",
                "username": "crypto_breaking_news",
                "tweetId": "test_multiple_btc_eth_001",
            },
        ],  # Should trigger BOTH
    },
    {
        "name": "country_specific_event",
        "description": "Agent should trigger only events that are relevant to the country/s mentioned in the tweet",
        "tweet": {
            "text": "Big issues between India and Pakistan. India is invading Pakistan frontiers!",
            "username": "world_war_news",
            "created_at": "2024-01-15T19:15:00Z",
            "id": "test_country_001",
        },
        "events": [
            WORLD_EVENTS["india_pakistan_border_conflict_001"],
            WORLD_EVENTS["india_pakistan_nuclear_001"],
            WORLD_EVENTS["palestine_israel_conflict"],
            WORLD_EVENTS["south_korea_nuclear_001"],
            WORLD_EVENTS["japan_president_crypto_fraud_001"],
            WORLD_EVENTS["syria_turkey_attack_001"],
            WORLD_EVENTS["russia_ukraine_escalation_001"],
            WORLD_EVENTS["india_pakistan_peace_announcement_001"],
            WORLD_EVENTS["iran_saudi_war_001"],
        ],
        "expected_triggers": [
            {
                "eventId": "india_pakistan_border_conflict_001",
                "tweetContent": "Big issues between India and Pakistan. India is invading Pakistan frontiers!",
                "username": "world_war_news",
                "tweetId": "test_country_001",
            }
        ],
    },
    {
        "name": "tariff_event_comparison",
        "description": "Agent should trigger the event that is most relevant to the tweet based on the tariff mentioned",
        "tweet": {
            "text": "Trump announces 25% tariff on India plus 'penalty' for trade with Russia",
            "username": "us_news_today",
            "created_at": "2024-01-15T19:15:00Z",
            "id": "test_tariff_event_001",
        },
        "events": [
            CORE_EVENTS["trump_tariff_india_russia"],
            WORLD_EVENTS["india_pakistan_border_conflict_001"],
            WORLD_EVENTS["india_pakistan_nuclear_001"],
            WORLD_EVENTS["palestine_israel_conflict"],
            WORLD_EVENTS["south_korea_nuclear_001"],
        ],
        "expected_triggers": [
            {
                "eventId": "trump_tariff_india_russia_001",
                "tweetContent": "Trump announces 25% tariff on India plus 'penalty' for trade with Russia",
                "username": "us_news_today",
                "tweetId": "test_tariff_event_001",
            }
        ],
    },
    {
        "name": "empty_tweet_or_repost",
        "description": "Agent should NOT trigger if the tweet is empty or a repost with a link",
        "tweet": {
            "text": "@WatcherGuru https://t.co/mFPMulReHK",
            "username": "S4mmyEth",
            "created_at": "2024-01-15T19:15:00Z",
            "id": "repost_id",
        },
        "events": [
            {
                "eventId": "us_eth_reserves_001",
                "title": "US announces national ETH reserves",
                "longTrades": [],
                "shortTrades": [],
                "eventTime": None,
                "closingTime": None,
                "createdAt": datetime(2024, 1, 14),
                "executionTime": None,
                "executed": False,
                "tradeStatus": "pending",
                "tweetBased": True,
            },
            CORE_EVENTS["trump_tariff_india_russia"],
            WORLD_EVENTS["india_pakistan_border_conflict_001"],
            WORLD_EVENTS["india_pakistan_nuclear_001"],
            WORLD_EVENTS["palestine_israel_conflict"],
            WORLD_EVENTS["south_korea_nuclear_001"],
        ],
        "expected_triggers": [],  # Empty tweet should not trigger anything
    },
    {
        "name": "lummis_mortgage_reform_bill",
        "description": "Agent should trigger only the event that matches the actual action described in the tweet (introduces vs rejects)",
        "tweet": {
            "text": "Senator Cynthia Lummis introduces mortgage reform bill to recognize crypto assets in home loan eligibility assessments.",
            "username": "crypto_policy_news",
            "created_at": "2024-01-15T22:00:00Z",
            "id": "test_lummis_mortgage_001",
        },
        "events": [
            {
                "eventId": "lummis_mortgage_reform_001",
                "title": "Senator Lummis introduces crypto mortgage reform bill",
                "longTrades": [],
                "shortTrades": [],
                "eventTime": None,
                "closingTime": None,
                "createdAt": datetime(2024, 1, 14),
                "executionTime": None,
                "executed": False,
                "tradeStatus": "pending",
                "tweetBased": True,
            },
            {
                "eventId": "lummis_rejects_mortgage_reform_001",
                "title": "Senator Lummis rejects crypto mortgage reform bill",
                "longTrades": [],
                "shortTrades": [],
                "eventTime": None,
                "closingTime": None,
                "createdAt": datetime(2024, 1, 13),
                "executionTime": None,
                "executed": False,
                "tradeStatus": "pending",
                "tweetBased": True,
            },
            {
                "eventId": "sec_crypto_regulation_001",
                "title": "SEC announces new crypto regulations",
                "longTrades": [],
                "shortTrades": [],
                "eventTime": None,
                "closingTime": None,
                "createdAt": datetime(2024, 1, 12),
                "executionTime": None,
                "executed": False,
                "tradeStatus": "pending",
                "tweetBased": True,
            },
        ],
        "expected_triggers": [
            {
                "eventId": "lummis_mortgage_reform_001",
                "tweetContent": "Senator Cynthia Lummis introduces mortgage reform bill to recognize crypto assets in home loan eligibility assessments.",
                "username": "crypto_policy_news",
                "tweetId": "test_lummis_mortgage_001",
            }
        ],  # Should trigger only the mortgage reform event
    },
]

# Scalability test cases - testing agent's performance with different numbers of events
SCALABILITY_TEST_CASES = [
    {
        "name": "clear_match_scalability",
        "description": "Agent should consistently detect clear matches regardless of event count",
        "tweet": {
            "text": "CONFIRMED: Binance has been hacked. $100M+ stolen. Trading suspended immediately. All funds at risk. #BinanceHack #CryptoNews",
            "username": "blockchain_reporter",
            "created_at": "2024-01-15T20:15:00Z",
            "id": "test_scale_clear_001",
        },
        "events_1": SINGLE_EVENT,
        "events_5": FIVE_EVENTS,
        "events_10": TEN_EVENTS,
        "events_20": TWENTY_EVENTS,
        "expected_triggers": [
            {
                "eventId": "major_exchange_hack_001",
                "tweetContent": "CONFIRMED: Binance has been hacked. $100M+ stolen. Trading suspended immediately. All funds at risk. #BinanceHack #CryptoNews",
                "username": "blockchain_reporter",
                "tweetId": "test_scale_clear_001",
            }
        ],  # Should ALWAYS trigger this one
    },
    {
        "name": "subtle_match_scalability",
        "description": "Agent should detect subtle matches consistently across different event counts",
        "tweet": {
            "text": "BREAKING: Ethereum Foundation announces major restructuring. Vitalik says they're 'winding down operations' and transitioning to a new decentralized model. End of an era for centralized ETH development.",
            "username": "ethereum_insider",
            "created_at": "2024-01-15T18:30:00Z",
            "id": "test_scale_subtle_001",
        },
        "events_1": [CORE_EVENTS["eth_foundation_shutdown"]],
        "events_5": FIVE_EVENTS,
        "events_10": TEN_EVENTS,
        "events_20": TWENTY_EVENTS,
        "expected_triggers": [
            {
                "eventId": "eth_foundation_shutdown_001",
                "tweetContent": "BREAKING: Ethereum Foundation announces major restructuring. Vitalik says they're 'winding down operations' and transitioning to a new decentralized model. End of an era for centralized ETH development.",
                "username": "ethereum_insider",
                "tweetId": "test_scale_subtle_001",
            }
        ],  # Should ALWAYS trigger this one
    },
    {
        "name": "no_match_scalability",
        "description": "Agent should consistently avoid false positives regardless of event count",
        "tweet": {
            "text": "Beautiful sunset over the mountains today! Nature is absolutely stunning. Going for a hike tomorrow. #nature #photography #outdoors",
            "username": "nature_lover_2024",
            "created_at": "2024-01-15T19:45:00Z",
            "id": "test_scale_nomatch_001",
        },
        "events_1": [CORE_EVENTS["btc_creator_discovery"]],
        "events_5": FIVE_EVENTS,
        "events_10": TEN_EVENTS,
        "events_20": TWENTY_EVENTS,
        "expected_triggers": [],  # Should NEVER trigger any events
    },
    {
        "name": "country_match_scalability",
        "description": "Agent should trigger events only if country/s mentioned in the tweet are mentioned in the events",
        "tweet": {
            "text": "South Korea is launching 3 nuclear missiles towards Japan. Japan is preparing for the worst.",
            "username": "world_war_news",
            "created_at": "2024-01-15T19:45:00Z",
            "id": "test_scale_nomatch_001",
        },
        "events_1": [WORLD_EVENTS["south_korea_nuclear_001"]],
        "events_5": [WORLD_EVENTS["south_korea_nuclear_001"]] + FIVE_EVENTS,
        "events_10": [WORLD_EVENTS["south_korea_nuclear_001"]] + TEN_EVENTS,
        "events_20": TWENTY_EVENTS,
        "expected_triggers": [
            {
                "eventId": "south_korea_nuclear_001",
                "tweetContent": "South Korea is launching 3 nuclear missiles towards Japan. Japan is preparing for the worst.",
                "username": "world_war_news",
                "tweetId": "test_scale_nomatch_001",
            }
        ],  # Should trigger this one and not any other country related event
    },
    {
        "name": "no_trigger_on_potential_event",
        "description": "Agent should NOT trigger any event when the tweet only discusses possible or potential future events, not confirmed occurrences.",
        "tweet": {
            "text": "Russia is weighing options for a concession that could include an air truce with Ukraine to try to head off Trump's threat of secondary sanctions.",
            "username": "world_war_news",
            "created_at": "2024-01-15T19:45:00Z",
            "id": "test_scale_nomatch_001",
        },
        "events_1": [WORLD_EVENTS["russia_ukraine_ceasefire_001"]],
        "events_5": [WORLD_EVENTS["russia_ukraine_ceasefire_001"]] + FIVE_EVENTS,
        "events_10": TEN_EVENTS
        + [WORLD_EVENTS["russia_ukraine_ceasefire_001"]]
        + [CORE_EVENTS["sec_crypto_ban"]]
        + [CORE_EVENTS["eth_foundation_shutdown"]],
        "events_20": TWENTY_EVENTS,
        "expected_triggers": [],  # Should NOT trigger any event, as nothing has actually happened yet
    },
    {
        "name": "trigger_on_effective_event",
        "description": "Agent should trigger an event when the tweet describes an event that has already occurred.",
        "tweet": {
            "text": "Russia and Ukraine have signed a ceasefire agreement.",
            "username": "world_war_news",
            "created_at": "2024-01-15T19:45:00Z",
            "id": "test_scale_nomatch_001",
        },
        "events_1": [WORLD_EVENTS["russia_ukraine_ceasefire_001"]],
        "events_5": [WORLD_EVENTS["russia_ukraine_ceasefire_001"]] + FIVE_EVENTS,
        "events_10": [WORLD_EVENTS["russia_ukraine_ceasefire_001"]] + TEN_EVENTS,
        "events_20": TWENTY_EVENTS,
        "expected_triggers": [
            {
                "eventId": "russia_ukraine_ceasefire_001",
                "tweetContent": "Russia and Ukraine have signed a ceasefire agreement.",
                "username": "world_war_news",
                "tweetId": "test_scale_nomatch_001",
            }
        ],  # Should trigger because it happen
    },
]
