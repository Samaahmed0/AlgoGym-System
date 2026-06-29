"""Paths and constants for the hybrid recommender (Ai/recommender/)."""

from pathlib import Path

RECOMMENDER_ROOT = Path(__file__).resolve().parent
AI_ROOT = RECOMMENDER_ROOT.parent
GPPKT_ROOT = AI_ROOT / "gppkt"

# Input data (read-only; swap paths when weakness export updates)
PROBLEMS_CSV = AI_ROOT / "data" / "Problems_rows.csv"
SUBMISSIONS_CSV = GPPKT_ROOT / "data_new" / "incoming" / "submissions_merged.csv"
SUBMISSIONS_FALLBACK = GPPKT_ROOT / "data_new" / "submissions_rich.csv"
MASTERY_REPORT = GPPKT_ROOT / "data_new" / "option_c" / "mastery_report_infer_only.csv"
WEAKNESS_SUMMARY = GPPKT_ROOT / "data_new" / "option_c" / "weakness_summary_infer_only.csv"
KC_GRAPH = AI_ROOT / "kc_graph.json"
KC_VOCAB = AI_ROOT / "kc_vocab.csv"

# Generated outputs
DATA_DIR = RECOMMENDER_ROOT / "data"
ARTIFACTS_DIR = RECOMMENDER_ROOT / "artifacts"
CATALOG_PARQUET = DATA_DIR / "catalog.parquet"
LABELS_PARQUET = DATA_DIR / "training_labels.parquet"
FEATURES_PARQUET = DATA_DIR / "feature_matrix.parquet"
RANKER_PKL = ARTIFACTS_DIR / "ranker.pkl"
FEATURE_SCHEMA_JSON = ARTIFACTS_DIR / "feature_schema.json"
EVAL_REPORT_JSON = ARTIFACTS_DIR / "eval_report.json"

# Rating normalization (aligned with GPPKT script 00)
RATING_MIN = 800
RATING_MAX = 3500

# Weakness thresholds (for deriving weak KCs when summary absent)
MASTERY_WEAK_THRESHOLD = 0.4
MIN_KC_ATTEMPTS = 3

# Recommendation
TOP_K = 10
SELECTION_POOL_SIZE = None  # None = all filtered candidates
EXPLORE_EPS = 0.1
SKILL_RATING_DELTA = 400
WEAK_FIRST = True
MIN_WEAK_KC_OVERLAP = 1
WEAK_FIRST_FALLBACK = True  # use full pool when no weak-tagged candidates
# Weak-first filter: use weakest_N from weakness_summary (not only is_weak / weak_kcs)
USE_WEAKEST_N = True
WEAKEST_N_COLUMN = "weakest_5"  # column in weakness_summary_infer_only.csv

# Weak-first remedial band: difficulty from weak-KC mastery, not overall skill
USE_WEAK_KC_SKILL = True
WEAK_KC_SKILL_STRETCH = 200  # max rating above weak-area skill center
WEAK_KC_SKILL_BELOW = 400  # same as SKILL_RATING_DELTA below weak skill

# Pre-ranking remedial difficulty filter (before ranker; easy + medium + capped hard per weak KC)
FILTER_REMEDIAL_DIFFICULTY = True
FILTER_HARD_POOL_FRACTION = 0.2  # keep at most this fraction of hard candidates per weak KC
FILTER_HARD_MAX_PER_KC = 8  # absolute cap on hard candidates per weak KC in the pool

# Difficulty stratification (aligned with Backend ProblemService rating bands)
DIFFICULTY_STRATIFY = True
DIFFICULTY_EASY_MAX = 1199
DIFFICULTY_MEDIUM_MAX = 1599
DIFFICULTY_QUOTA_EASY = 4
DIFFICULTY_QUOTA_MEDIUM = 4
DIFFICULTY_QUOTA_HARD = 2  # global fallback when PER_KC_STRATIFY off or no weak KCs
# Per weak-KC: allocate slots + MMR/stratify inside each concept (replaces global 4/4/2)
PER_KC_STRATIFY = True
PER_KC_STRATIFY_USE_MMR = True
PER_KC_MASTERY_NO_HARD = 0.4  # below: 0 Hard picks for that KC
PER_KC_MASTERY_MAX_ONE_HARD = 0.45  # below: at most 1 Hard for that KC
# MMR diverse shortlist before global stratify (when PER_KC_STRATIFY=False)
STRATIFY_USE_MMR = True
MMR_STRATIFY_POOL_SIZE = 40

# Cold-start fallback
COLD_START_RATING_MIN = 800
COLD_START_RATING_MAX = 1200

# Training labels
LABEL_WINDOW = 50
MIN_PREFIX_ATTEMPTS = 10
MAX_ROWS_PER_USER = None  # None = full trajectory per student
TRAIN_VAL_SPLIT = 0.8
SEED = 42

# Verdict filter
VERDICT_ACCEPTED = "ACCEPTED"
VERDICT_WRONG_ANSWER = "WRONG_ANSWER"
ALLOWED_VERDICTS = frozenset({VERDICT_ACCEPTED, VERDICT_WRONG_ANSWER})

# Export scores: shift to strictly positive for JSON/DB (ranking unchanged before export)
NORMALIZE_EXPORT_SCORES = True
EXPORT_SCORE_FLOOR = 0.01

# Eval (0 = all students with mastery export)
EVAL_STRIDE = 5
EVAL_FORWARD_WINDOW = 50
EVAL_STUDENT_SAMPLE = 0
