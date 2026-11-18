
# ================= ΡΥΘΜΙΣΕΙΣ =================

DATA_SOURCE = "dummy"       # "dummy" ή "excel"
EXCEL_FILE = "personnel.xlsx"
EXCEL_SHEET = 0

# Περίοδος προγραμματισμού
DAYS = 31
R = range(DAYS)

# Ειδικές ημέρες
HOLIDAYS = {24, 25}
FRIDAYS = {3, 10, 17, 24}

# Σύνθεση ημερήσιας βάρδιας
CREW = 5
AK_RANK = 4
MIN_GAP = 3

# Παράμετροι CP-SAT
TIME_LIMIT = 120

# Παράμετροι Genetic Algorithm
GA_POP = 200
GA_GENS = 300
GA_PATIENCE = 60

# Εμφάνιση αναλυτικών προγραμμάτων
SHOW_SCHEDULES = False

# Αναπαραγωγιμότητα αποτελεσμάτων
SEED = 42

# Βαθμοί, αναμενόμενος αριθμός ατόμων και όρια βαρδιών
RANKS = [
    ("Δίοπος", 1, 5, 5),
    ("Κελευστής", 2, 5, 5),
    ("Επικελευστής", 3, 5, 5),
    ("Αρχικελευστής", 4, 5, 5),
    ("Ανθυπασπιστής", 5, 5, 4),
]

RANK_BY_NAME = {
    label: rank for label, rank, _, _ in RANKS
}

RANK_LABEL = {
    rank: label for label, rank, _, _ in RANKS
}

CAP = {
    rank: cap for _, rank, _, cap in RANKS
}

EXPECTED = {
    rank: count for _, rank, count, _ in RANKS
}

# Περιγραφές για τις επιμέρους κατηγορίες αναφοράς
REASONS = {
    "shifts": "πλήθος βαρδιών",
    "over": "υπέρβαση",
    "hol": "κατανομή αργιών",
    "fri": "κατανομή Παρασκευών",
    "duty": "ανάθεση υπόλογου",
    "mech": "ανάθεση μηχανικού",
    "elec": "ανάθεση ηλεκτρολόγου",
}
