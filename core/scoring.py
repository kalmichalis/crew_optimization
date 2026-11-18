
from core import config
from core import data
from core.rules import rules_errors, summarize


# ================= ΛΕΞΙΚΟΓΡΑΦΙΚΗ ΑΞΙΟΛΟΓΗΣΗ =================

def score(sched):
    """
    Λεξικογραφική βαθμολογία Genetic Algorithm.

    Μικρότερο tuple = καλύτερη λύση.

    Οι προτεραιότητες εξετάζονται με τη σειρά:
    1. Ελαχιστοποίηση παραβιάσεων κανόνων.
    2. Ελαχιστοποίηση συνολικών υπερβάσεων.
    3. Καλύτερη κατανομή υπερβάσεων.
    4. Μέγιστη κάλυψη διαφορετικών ατόμων στις αργίες.
    5. Προτεραιότητα νεότερων στις αργίες.
    6. Ελαχιστοποίηση φορτίου αργιών.
    7. Μέγιστη κάλυψη διαφορετικών ατόμων στις Παρασκευές.
    8. Προτεραιότητα νεότερων στις Παρασκευές.
    """

    s = summarize(sched)

    # 1. Παραβιάσεις σκληρών κανόνων
    hard = len(rules_errors(sched))

    # 2. Συνολικές υπερβάσεις ορίων
    total_over = sum(
        v["over"] for v in s.values()
    )

    # 3. Ποινή κατανομής υπερβάσεων
    dist = sum(
        k * 100 + data.ORDER[m]
        for m in data.names
        for k in range(1, s[m]["over"] + 1)
    )

    # 4. Πόσα άτομα δεν έχουν πάρει αργία
    miss_h_count = sum(
        1 for m in data.names
        if s[m]["hol"] == 0
    )

    # 5. Προτεραιότητα νεότερων στις αργίες
    miss_h_priority = sum(
        data.N - data.ORDER[m]
        for m in data.names
        if s[m]["hol"] == 0
    )

    # 6. Συνολικό φορτίο αργιών
    load_h = sum(
        data.ORDER[m] * s[m]["hol"]
        for m in data.names
    )

    # 7. Πόσα άτομα δεν έχουν πάρει Παρασκευή
    miss_f_count = sum(
        1 for m in data.names
        if s[m]["fri"] == 0
    )

    # 8. Προτεραιότητα νεότερων στις Παρασκευές
    miss_f_priority = sum(
        data.N - data.ORDER[m]
        for m in data.names
        if s[m]["fri"] == 0
    )

    return (
        hard,
        total_over,
        dist,
        miss_h_count,
        miss_h_priority,
        load_h,
        miss_f_count,
        miss_f_priority
    )
