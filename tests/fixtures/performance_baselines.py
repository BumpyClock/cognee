# ABOUTME: Performance baseline documents and metrics for temporal cascade validation
# ABOUTME: Documents of varying sizes to test <2x overhead requirement with expected processing times

from typing import Dict, Any
from datetime import datetime


# ==============================================================================
# Performance Targets (from tasklist)
# ==============================================================================
# - Atomic extraction: <500ms per chunk
# - Classification: <200ms per batch of 10 facts
# - Invalidation check: <100ms per fact
# - Total overhead: <2x base pipeline

PERFORMANCE_TARGETS = {
    "extraction_per_chunk_ms": 500,
    "classification_per_batch_ms": 200,
    "invalidation_per_fact_ms": 100,
    "total_overhead_multiplier": 2.0,
}


# ==============================================================================
# Small Document (~100 words, ~5 facts expected)
# ==============================================================================

SMALL_DOC = """
Apple Inc. was founded in 1976 by Steve Jobs and Steve Wozniak in Cupertino, California.
The company initially focused on personal computers. Tim Cook became CEO in 2011, succeeding
Steve Jobs. Apple is now one of the world's largest technology companies by market capitalization.
"""

SMALL_DOC_BASELINE = {
    "description": "Small document for baseline performance testing",
    "word_count": 52,
    "char_count": 318,
    "expected_facts": 5,  # founded by (x2), founded in, became CEO, is largest
    "expected_extraction_time_ms": 400,  # Well under 500ms target
    "expected_classification_time_ms": 150,  # Single batch, under 200ms
    "expected_total_time_ms": 550,  # Extraction + classification
    "max_acceptable_time_ms": 1100,  # 2x overhead tolerance
}


# ==============================================================================
# Medium Document (~500 words, ~25 facts expected)
# ==============================================================================

MEDIUM_DOC = """
The history of artificial intelligence began in the 1950s when computer scientists first
explored the concept of machine learning. Alan Turing published his seminal paper "Computing
Machinery and Intelligence" in 1950, proposing the famous Turing Test. John McCarthy coined
the term "artificial intelligence" at the Dartmouth Conference in 1956, widely considered
the birth of AI as a field.

Early AI research focused on symbolic reasoning and problem-solving. The perceptron, invented
by Frank Rosenblatt in 1958, was an early neural network model. AI experienced its first
major setback during the "AI Winter" of the 1970s and 1980s, when funding dried up due to
unmet expectations and computational limitations.

The field experienced a renaissance in the 1990s with advances in machine learning algorithms.
Deep Blue, developed by IBM, defeated chess champion Garry Kasparov in 1997, marking a
significant milestone. The 2000s saw the rise of big data and improved computational power,
enabling more sophisticated AI applications.

In 2012, AlexNet demonstrated the power of deep learning by winning the ImageNet competition
with unprecedented accuracy. This breakthrough sparked the modern deep learning revolution.
OpenAI was founded in 2015 by Elon Musk, Sam Altman, and others to ensure AI benefits humanity.
Google's DeepMind created AlphaGo, which defeated world champion Lee Sedol in 2016, showcasing
AI's ability to master complex strategic games.

The 2020s have witnessed explosive growth in large language models. GPT-3, released by OpenAI
in 2020, demonstrated remarkable natural language understanding capabilities. ChatGPT launched
in November 2022, bringing conversational AI to mainstream users and triggering widespread
adoption. Companies and researchers worldwide are now racing to develop increasingly capable
AI systems, with concerns about safety, ethics, and regulation becoming paramount.
"""

MEDIUM_DOC_BASELINE = {
    "description": "Medium document for realistic workload testing",
    "word_count": 289,
    "char_count": 2005,
    "expected_facts": 28,  # Multiple historical events, founding dates, achievements
    "expected_extraction_time_ms": 450,  # Single chunk, under 500ms
    "expected_classification_time_ms": 550,  # 3 batches (10+10+8), ~180ms each
    "expected_total_time_ms": 1000,  # Extraction + classification
    "max_acceptable_time_ms": 2000,  # 2x overhead tolerance
    "fact_distribution": {
        "STATIC": 20,  # Historical events, founding dates
        "DYNAMIC": 5,  # Ongoing developments, current state
        "ATEMPORAL": 3,  # Concepts, definitions
    },
    "temporal_patterns": [
        "Sequential events (1950 → 1956 → 1958 → 1970s → 1990s → 2012 → 2015 → 2016 → 2020 → 2022)",
        "Multiple time periods requiring precise validity windows",
        "Some facts may invalidate earlier statements (company leadership, state of field)",
    ],
}


# ==============================================================================
# Large Document (~2000 words, ~100 facts expected)
# ==============================================================================

LARGE_DOC = """
The technology industry has undergone remarkable transformation over the past seven decades,
fundamentally reshaping how humans communicate, work, and live. This narrative traces the
evolution of computing from mechanical calculators to artificial intelligence systems that
rival human cognitive capabilities.

### The Foundation Era (1940s-1960s)

The modern computer age began during World War II with machines like ENIAC, completed in 1945
at the University of Pennsylvania. Weighing 30 tons and occupying 1800 square feet, ENIAC could
perform 5,000 operations per second. John von Neumann introduced the stored-program architecture
in 1945, establishing the fundamental design still used in computers today.

The transistor, invented at Bell Labs in 1947 by John Bardeen, Walter Brattain, and William
Shockley, revolutionized electronics by replacing bulky vacuum tubes. This breakthrough earned
them the Nobel Prize in Physics in 1956. Jack Kilby at Texas Instruments and Robert Noyce at
Fairchild Semiconductor independently invented the integrated circuit in 1958-1959, enabling
miniaturization and mass production of electronic devices.

### The Mainframe and Minicomputer Era (1960s-1970s)

IBM dominated the mainframe market in the 1960s with its System/360 family, announced in 1964.
These computers served large corporations and government agencies, processing business transactions
and scientific calculations. Digital Equipment Corporation (DEC) introduced the PDP-8 minicomputer
in 1965, making computing accessible to smaller organizations at a fraction of mainframe costs.

Ken Thompson and Dennis Ritchie at Bell Labs developed the Unix operating system in 1969, which
became foundational to modern computing. Ritchie later created the C programming language in 1972,
which remains widely used today. Douglas Engelbart demonstrated the computer mouse, hypertext, and
graphical user interfaces at "The Mother of All Demos" in 1968, previewing technologies that would
become standard decades later.

### The Personal Computer Revolution (1970s-1980s)

The Altair 8800, released in 1975 as a kit for hobbyists, is considered the first personal computer.
Bill Gates and Paul Allen founded Microsoft in 1975 after developing a BASIC interpreter for the
Altair. Steve Jobs and Steve Wozniak founded Apple Computer in 1976, releasing the Apple II in 1977,
which became one of the first successful mass-produced personal computers.

IBM entered the personal computer market in 1981 with the IBM PC, which established the architecture
that dominated the industry. Microsoft provided the MS-DOS operating system for the IBM PC, beginning
its path to software dominance. Apple launched the Macintosh in 1984, introducing the graphical user
interface and mouse to mainstream users, though it struggled to compete with IBM-compatible PCs.

### The Internet and World Wide Web (1980s-1990s)

The foundation for the internet was laid with ARPANET, launched in 1969, but the modern internet
emerged in the 1980s. Tim Berners-Lee invented the World Wide Web in 1989 while working at CERN,
creating the HTTP protocol and HTML markup language. The first web browser, WorldWideWeb (later
renamed Nexus), was released in 1990.

Marc Andreessen and Eric Bina developed Mosaic at the National Center for Supercomputing Applications
in 1993, the first popular graphical web browser. Andreessen later co-founded Netscape in 1994,
releasing Netscape Navigator, which dominated the browser market until Microsoft's Internet Explorer
challenged it in the "browser wars" of the late 1990s.

Amazon was founded by Jeff Bezos in 1994 as an online bookstore, operating from his garage in Seattle.
Pierre Omidyar created eBay (originally AuctionWeb) in 1995, pioneering online auctions. Yahoo was
incorporated in 1995 by Jerry Yang and David Filo, becoming the dominant web portal. Google was
founded by Larry Page and Sergey Brin in 1998, introducing PageRank algorithm that revolutionized
web search.

### The Dot-Com Boom and Bust (1995-2002)

The late 1990s witnessed explosive growth in internet companies, with the NASDAQ Composite index
peaking at 5,048 on March 10, 2000. Investors poured billions into startups with little revenue,
valuing companies based on user growth and "eyeballs" rather than profits. The bubble burst in 2000,
wiping out trillions in market value. Many companies failed, but survivors like Amazon and eBay
emerged stronger.

### Web 2.0 and Social Media (2000s-2010s)

The 2000s saw the rise of user-generated content and social networking. Mark Zuckerberg launched
Facebook from his Harvard dorm room in 2004, initially limited to college students. The platform
opened to the general public in 2006 and reached 1 billion users in 2012. Facebook acquired Instagram
for $1 billion in 2012 and WhatsApp for $19 billion in 2014.

YouTube was founded by Steve Chen, Chad Hurley, and Jawed Karim in 2005, revolutionizing online video.
Google acquired YouTube for $1.65 billion in 2006. Twitter was created by Jack Dorsey, Noah Glass,
Biz Stone, and Evan Williams in 2006, introducing microblogging and becoming a major communications
platform.

Apple released the iPhone in 2007, combining a phone, iPod, and internet communicator. This revolutionary
device sparked the smartphone era and created the mobile app ecosystem. Google released Android in 2008,
providing an open-source alternative that now powers over 70% of smartphones globally.

### Cloud Computing and Mobile (2010s)

Amazon Web Services (AWS), launched in 2006, pioneered cloud computing infrastructure. Microsoft Azure
launched in 2010, and Google Cloud Platform in 2011, creating intense competition. Cloud services
transformed how companies build and deploy software, enabling startups to scale without massive upfront
infrastructure investments.

The iPad, released by Apple in 2010, created the modern tablet market. Microsoft released Windows 8 in
2012, attempting to bridge desktop and tablet interfaces, though it received mixed reviews. The rise of
mobile computing forced companies to adopt "mobile-first" strategies.

### Artificial Intelligence Renaissance (2010s-2020s)

Deep learning breakthroughs in the 2010s revolutionized AI capabilities. AlexNet won the ImageNet
competition in 2012 with unprecedented accuracy, launching the deep learning revolution. Google
acquired DeepMind in 2014 for $500 million. DeepMind's AlphaGo defeated world champion Lee Sedol in
2016, demonstrating AI's potential.

OpenAI was founded in 2015 by Elon Musk, Sam Altman, Greg Brockman, and others as a non-profit AI
research organization. OpenAI released GPT-2 in 2019 and GPT-3 in 2020, showcasing impressive language
capabilities. ChatGPT launched in November 2022, reaching 100 million users in just two months, the
fastest-growing consumer application in history.

### Current Landscape (2020s)

The 2020s are defined by AI competition, with major tech companies investing billions in large language
models and generative AI. Microsoft invested $10 billion in OpenAI in 2023, integrating AI into its
products. Google released Bard (later rebranded as Gemini) in 2023 to compete with ChatGPT. Anthropic,
founded by former OpenAI researchers in 2021, released Claude in 2023, emphasizing AI safety.

The industry faces challenges including antitrust scrutiny, data privacy concerns, misinformation, and
debates about AI safety and regulation. Companies like Apple, Microsoft, Google, Amazon, and Meta have
market capitalizations exceeding $1 trillion, wielding enormous economic and social influence.
"""

LARGE_DOC_BASELINE = {
    "description": "Large document for stress testing and performance validation",
    "word_count": 1085,
    "char_count": 7815,
    "expected_facts": 115,  # Extensive historical timeline with many events
    "expected_extraction_time_ms": 480,  # Single chunk, under 500ms (efficient extraction)
    "expected_classification_time_ms": 2200,  # 12 batches (115/10 rounded up), ~180ms each
    "expected_total_time_ms": 2680,  # Extraction + classification
    "max_acceptable_time_ms": 5360,  # 2x overhead tolerance
    "fact_distribution": {
        "STATIC": 90,  # Most are historical facts with fixed dates
        "DYNAMIC": 15,  # Current state, ongoing trends
        "ATEMPORAL": 10,  # Technical concepts, definitions
    },
    "temporal_patterns": [
        "Dense timeline from 1940s to 2020s",
        "Many sequential events requiring invalidation chains",
        "Company leadership changes (Jobs → Cook at Apple, etc.)",
        "Market value changes over time",
        "Technology releases and acquisitions with specific dates",
    ],
    "complexity_factors": [
        "Multiple entities with changing attributes over time",
        "Nested relationships (founders → companies → products)",
        "Precise dates requiring accurate timestamp parsing",
        "Potential for numerous STATIC→STATIC replacements",
    ],
}


# ==============================================================================
# Helper Functions
# ==============================================================================

def get_baseline_document(size: str) -> str:
    """
    Get performance baseline document by size.

    Args:
        size: Document size ("small", "medium", or "large")

    Returns:
        Document text

    Raises:
        ValueError: If size not recognized
    """
    size = size.lower()
    if size == "small":
        return SMALL_DOC
    elif size == "medium":
        return MEDIUM_DOC
    elif size == "large":
        return LARGE_DOC
    else:
        raise ValueError(f"Unknown size '{size}'. Use 'small', 'medium', or 'large'")


def get_baseline_metrics(size: str) -> Dict[str, Any]:
    """
    Get expected performance metrics for a baseline document.

    Args:
        size: Document size ("small", "medium", or "large")

    Returns:
        Dictionary with expected metrics (fact count, timing, etc.)

    Raises:
        ValueError: If size not recognized
    """
    size = size.lower()
    if size == "small":
        return SMALL_DOC_BASELINE
    elif size == "medium":
        return MEDIUM_DOC_BASELINE
    elif size == "large":
        return LARGE_DOC_BASELINE
    else:
        raise ValueError(f"Unknown size '{size}'. Use 'small', 'medium', or 'large'")


def validate_performance(
    actual_time_ms: float,
    actual_fact_count: int,
    doc_size: str,
) -> Dict[str, Any]:
    """
    Validate actual performance against baseline expectations.

    Args:
        actual_time_ms: Measured processing time in milliseconds
        actual_fact_count: Number of facts extracted
        doc_size: Document size ("small", "medium", or "large")

    Returns:
        Validation result dictionary with:
        - passed: bool (True if within 2x overhead)
        - overhead_multiplier: float (actual/expected ratio)
        - fact_count_delta: int (actual - expected)
        - warnings: List[str]

    Example:
        >>> result = validate_performance(1200, 6, "small")
        >>> assert result["passed"], f"Exceeded 2x overhead: {result['overhead_multiplier']}"
    """
    baseline = get_baseline_metrics(doc_size)
    expected_time = baseline["expected_total_time_ms"]
    max_acceptable = baseline["max_acceptable_time_ms"]
    expected_facts = baseline["expected_facts"]

    overhead_multiplier = actual_time_ms / expected_time
    fact_count_delta = actual_fact_count - expected_facts
    warnings = []

    # Check if within 2x overhead
    passed = actual_time_ms <= max_acceptable

    # Warnings for significant deviations
    if overhead_multiplier > 1.5:
        warnings.append(
            f"Performance approaching 2x limit: {overhead_multiplier:.2f}x"
        )

    if abs(fact_count_delta) > expected_facts * 0.3:
        warnings.append(
            f"Fact count deviation >30%: expected {expected_facts}, got {actual_fact_count}"
        )

    return {
        "passed": passed,
        "overhead_multiplier": overhead_multiplier,
        "actual_time_ms": actual_time_ms,
        "expected_time_ms": expected_time,
        "max_acceptable_time_ms": max_acceptable,
        "fact_count_delta": fact_count_delta,
        "actual_facts": actual_fact_count,
        "expected_facts": expected_facts,
        "warnings": warnings,
    }


def get_performance_summary() -> str:
    """
    Get human-readable summary of performance baselines.

    Returns:
        Formatted string with baseline expectations
    """
    lines = ["Performance Baseline Documents:", "=" * 70]

    for size in ["small", "medium", "large"]:
        baseline = get_baseline_metrics(size)
        lines.append(f"\n{size.upper()} DOCUMENT")
        lines.append(f"  Word Count: {baseline['word_count']}")
        lines.append(f"  Expected Facts: {baseline['expected_facts']}")
        lines.append(f"  Expected Time: {baseline['expected_total_time_ms']}ms")
        lines.append(f"  Max Acceptable: {baseline['max_acceptable_time_ms']}ms (2x)")

    lines.append(f"\n\nPERFORMANCE TARGETS")
    lines.append(f"  Extraction per chunk: <{PERFORMANCE_TARGETS['extraction_per_chunk_ms']}ms")
    lines.append(f"  Classification per batch: <{PERFORMANCE_TARGETS['classification_per_batch_ms']}ms")
    lines.append(f"  Total overhead: <{PERFORMANCE_TARGETS['total_overhead_multiplier']}x base pipeline")

    return "\n".join(lines)
