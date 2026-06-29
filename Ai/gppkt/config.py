from pathlib import Path

GPPKT_ROOT = Path(__file__).resolve().parent
AI_ROOT = GPPKT_ROOT.parent

# Rating → b_i (script 00)
RATING_MIN = 800
RATING_MAX = 3500
B_I_SCALE = 3.0

# Default artifact locations (relative to Ai/)
DEFAULT_KC_VOCAB = AI_ROOT / "kc_vocab.csv"
DEFAULT_CONCEPT_EMBEDDINGS = AI_ROOT / "embeddings" / "concept_embeddings.csv"

# Working data (outputs of 00–09). Legacy sandbox: gppkt/data/ (7 students — do not use).
DATA_DIR = GPPKT_ROOT / "data_new"
DEFAULT_INTERACTIONS = DATA_DIR / "interactions_table.csv"
DEFAULT_PROBLEMS = DATA_DIR / "problems_table.csv"
DEFAULT_EXERCISE_VECTORS = DATA_DIR / "exercise_vectors.npy"
DEFAULT_RATING_IMPUTATION = DATA_DIR / "rating_imputation.json"

# Verdict allowlist (script 00)
VERDICT_ACCEPTED = "ACCEPTED"
VERDICT_WRONG_ANSWER = "WRONG_ANSWER"
ALLOWED_VERDICTS = frozenset({VERDICT_ACCEPTED, VERDICT_WRONG_ANSWER})

# Eligibility: minimum interactions per student after filtering
MIN_INTERACTIONS_PER_STUDENT = 10

# IRT inversion (script 02) — Eq. (8)–(9); do not change 1.702 in model code per plan
IRT_D = 1.702
IRT_P_CLIP = 1e-6

# Answer-summary features (script 03): z_feat_1 = min(attempts, Z_ATTEMPTS_MAX) / Z_ATTEMPTS_MAX
Z_ATTEMPTS_MAX = 50

# Padded sequence length (script 04 / 05)
SEQ_LEN = 200
DEFAULT_SEQUENCES_NPZ = DATA_DIR / "gppkt_sequences.npz"

# Model / training (scripts 05–07) — align with GPPKT_PLAN.md
KC_EMBED_DIM = 64  # TransE d; must match exercise_vectors.npy
Z_DIM = 32
HIDDEN_DIM = 128
BATCH = 64
LR = 0.001
EPOCHS = 30
DROPOUT = 0.2
SEED = 42
TRAIN_FRAC = 0.8
DEFAULT_CHECKPOINT = DATA_DIR / "gppkt_best.pt"
DEFAULT_KC_CHECKPOINT = DATA_DIR / "gppkt_kc_best.pt"
DEFAULT_KC_INDEX = DATA_DIR / "kc_index.json"
DEFAULT_KC_EMBEDDINGS = DATA_DIR / "kc_embeddings.npy"
DEFAULT_KC_GRAPH = AI_ROOT / "kc_graph.json"
DEFAULT_METRICS_JSON = DATA_DIR / "metrics.json"
DEFAULT_WEAKNESS_REPORT = DATA_DIR / "weakness_report.csv"
DEFAULT_WEAKNESS_SUMMARY = DATA_DIR / "weakness_summary.csv"
DEFAULT_MASTERY_REPORT = DATA_DIR / "mastery_report.csv"

# KC mastery head (scripts 06–09) — Option C: active-step mastery + graph loss
PROBLEM_LOSS_WEIGHT = 0.3
KC_LOSS_WEIGHT = 1.0
KC_CURRENT_LOSS_WEIGHT = 0.15  # BCE on current problem outcome per active KC tag
WEIGHT_DECAY = 1e-4
GRAPH_LOSS_WEIGHT = 0.1
GRAPH_PREREQ_MARGIN = 0.15  # child mastery should not exceed parent by more than this
GRAPH_SMOOTH_BETA = 0.3  # inference: blend mastery with prerequisite neighbors
MASTERY_WEAK_THRESHOLD = 0.4
TOP_N_WEAK = 5
MIN_KC_ATTEMPTS = 3
DEFAULT_OPTION_C_CHECKPOINT = DATA_DIR / "gppkt_kc_option_c.pt"

# Episode VAE v1 (scripts 00a, 00b, 03_pretrain, 03_encode)
DEFAULT_SUBMISSIONS_RICH = DATA_DIR / "submissions_rich.csv"
DEFAULT_EPISODE_NPZ = DATA_DIR / "episode_attempts.npz"
DEFAULT_EPISODE_STATS = DATA_DIR / "episode_stats.json"
DEFAULT_VAE_CHECKPOINT = DATA_DIR / "vae_best.pt"
DEFAULT_VAE_METRICS = DATA_DIR / "vae_metrics.json"
DEFAULT_Z_LATENT_CSV = DATA_DIR / "z_latent.csv"
VAE_RUN_DIR = DATA_DIR / "vae_v1"
MAX_EP_LEN = 32
VAE_EPOCHS = 40
VAE_LR = 1e-3
VAE_BETA_MAX = 0.1
VAE_BATCH = 64
VAE_HIDDEN = 64
Z_RAW_DIM = Z_DIM
ENCODE_UNMATCHED_MAX_FRAC = 0.05
MIN_FEATURE_FILL_RATE = 0.2  # Phase 4: enable compiler columns when fill rate exceeds this
