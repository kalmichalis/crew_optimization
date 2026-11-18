
import random
import time

from core import config
from core import data
from core.rules import summarize, gap_conflict_count
from core.scoring import score
from core.timing import record_time


# ================= ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ =================

def repair(day):

    crew = day["crew"]
    chosen = {}

    # Πρώτα μηχανικός και ηλεκτρολόγος.
    # Πρέπει υποχρεωτικά να είναι διαφορετικοί.
    for role, elig in (
        ("mech", data.MECH),
        ("elec", data.ELEC)
    ):

        exclude = set(chosen.values())

        cands = [
            m for m in crew
            if m in elig and m not in exclude
        ]

        if not cands:

            outs = [
                m for m in data.names
                if m in elig
                and m not in crew
                and m not in exclude
            ]

            swappable = [
                i for i, m in enumerate(crew)
                if m not in exclude
            ]

            if outs and swappable:
                i = random.choice(swappable)
                crew[i] = random.choice(outs)
                cands = [crew[i]]

        if cands:
            chosen[role] = random.choice(cands)

        else:
            available = [
                m for m in crew
                if m not in exclude
            ]

            chosen[role] = (
                random.choice(available)
                if available else random.choice(crew)
            )

    # Ο υπόλογος μπορεί να συμπίπτει με
    # τον μηχανικό ή τον ηλεκτρολόγο.
    cands = [
        m for m in crew
        if m in data.DUTY_OK
    ]

    if not cands:

        outs = [
            m for m in data.names
            if m in data.DUTY_OK and m not in crew
        ]

        swappable = [
            i for i, m in enumerate(crew)
            if m not in chosen.values()
        ]

        if outs and swappable:
            i = random.choice(swappable)
            crew[i] = random.choice(outs)
            cands = [crew[i]]

    if cands:
        chosen["duty"] = random.choice(cands)

    else:
        chosen["duty"] = random.choice(crew)

    day["mech"] = chosen["mech"]
    day["elec"] = chosen["elec"]
    day["duty"] = chosen["duty"]

    return day


def random_day():

    return repair({
        "crew": random.sample(data.names, config.CREW),
        "duty": None,
        "mech": None,
        "elec": None
    })


def copy_day(day):

    return {
        "crew": day["crew"][:],
        "duty": day["duty"],
        "mech": day["mech"],
        "elec": day["elec"]
    }


def copy_sched(sched):

    return [
        copy_day(d)
        for d in sched
    ]


def crossover(a, b):

    return [
        copy_day(
            a[d] if random.random() < 0.5 else b[d]
        )
        for d in config.R
    ]


def can_assign(m, day_index, sched):
    """
    Ελέγχει αν το άτομο μπορεί να αναλάβει
    τη συγκεκριμένη ημέρα χωρίς παραβίαση MIN_GAP.
    """

    for d in config.R:

        if d == day_index:
            continue

        if m in sched[d]["crew"]:

            if abs(d - day_index) < config.MIN_GAP:
                return False

    return True


def replacement_preserves_roles(day, old_member, new_member):
    """
    Ελέγχει αν η αντικατάσταση διατηρεί έγκυρους
    τους ρόλους της συγκεκριμένης βάρδιας.
    """

    role_fields = [
        role for role in ("duty", "mech", "elec")
        if day[role] == old_member
    ]

    # Το νέο άτομο πρέπει να έχει όλα τα προσόντα
    # των ρόλων που αντικαθιστά.
    for role in role_fields:

        if role == "duty" and new_member not in data.DUTY_OK:
            return False

        if role == "mech" and new_member not in data.MECH:
            return False

        if role == "elec" and new_member not in data.ELEC:
            return False

    # Ενημερώνουμε μόνο τους ρόλους που αντικαθίστανται.
    for role in role_fields:
        day[role] = new_member

    # Μόνο μηχανικός και ηλεκτρολόγος πρέπει να είναι διαφορετικά άτομα.
    if day["mech"] == day["elec"]:
        return False

    if not {
        day["duty"],
        day["mech"],
        day["elec"]
    } <= set(day["crew"]):
        return False

    return True


# ================= ΕΠΙΔΙΟΡΘΩΣΗ ΠΡΟΓΡΑΜΜΑΤΟΣ =================

def repair_schedule(sched, max_changes=1000):
    """
    Συνολική επιδιόρθωση αποστάσεων.

    Αντικαθιστά μόνο το μέλος που προκαλεί τη σύγκρουση,
    διατηρώντας τους ρόλους και τα απαιτούμενα προσόντα.
    """

    start_time = time.perf_counter()
    changes = 0

    while changes < max_changes:

        fixed_one = False

        conflicts = []

        for m in data.names:

            ds = [
                d for d in config.R
                if m in sched[d]["crew"]
            ]

            for a, b in zip(ds, ds[1:]):

                if b - a < config.MIN_GAP:
                    conflicts.append((m, a, b))

        if not conflicts:
            break

        for m, a, b in conflicts:

            if (
                m not in sched[a]["crew"]
                or m not in sched[b]["crew"]
            ):
                continue

            for target in (b, a):

                if m not in sched[target]["crew"]:
                    continue

                candidates = [
                    candidate
                    for candidate in data.names
                    if candidate != m
                    and candidate not in sched[target]["crew"]
                    and can_assign(candidate, target, sched)
                ]

                current = summarize(sched)

                candidates.sort(
                    key=lambda candidate: (
                        current[candidate]["shifts"],
                        data.ORDER[candidate]
                    )
                )

                for candidate in candidates:

                    trial = copy_sched(sched)

                    if m not in trial[target]["crew"]:
                        continue

                    idx = trial[target]["crew"].index(m)

                    trial[target]["crew"][idx] = candidate

                    if not replacement_preserves_roles(
                        trial[target],
                        m,
                        candidate
                    ):
                        continue

                    old_conflicts = gap_conflict_count(sched)
                    new_conflicts = gap_conflict_count(trial)

                    # Αποδεχόμαστε μόνο πραγματική μείωση
                    # των συγκρούσεων απόστασης.
                    if new_conflicts < old_conflicts:

                        sched[:] = trial
                        changes += 1
                        fixed_one = True
                        break

                if fixed_one:
                    break

            if fixed_one:
                break

        if not fixed_one:
            break

    record_time(
        "repair_schedule",
        time.perf_counter() - start_time
    )

    return sched


# ================= ΜΕΤΑΛΛΑΞΗ =================

def mutate(sched, rate=0.04):

    for day in sched:

        if random.random() < rate:

            outside = [
                m for m in data.names
                if m not in day["crew"]
            ]

            if outside:

                day["crew"][random.randrange(config.CREW)] = (
                    random.choice(outside)
                )

                repair(day)

    return sched


# ================= ΤΟΠΙΚΗ ΑΝΑΖΗΤΗΣΗ =================

def local_search(sched, passes=5):

    sched = repair_schedule(sched)
    best = score(sched)

    for _ in range(passes):

        improved = False

        for d in config.R:

            for idx in range(config.CREW):

                for cand in data.names:

                    if cand in sched[d]["crew"]:
                        continue

                    trial = copy_sched(sched)
                    trial[d]["crew"][idx] = cand

                    repair(trial[d])
                    repair_schedule(trial)

                    s = score(trial)

                    if s < best:

                        best = s
                        sched = trial
                        improved = True

        if not improved:
            break

    return sched, best


# ================= GENETIC ALGORITHM =================

def evolve_ga():

    ga_start = time.perf_counter()

    print("Δημιουργία αρχικού πληθυσμού GA...", flush=True)

    init_start = time.perf_counter()
    pop = []

    for i in range(config.GA_POP):

        sched = [
            random_day()
            for _ in config.R
        ]

        repair_schedule(sched)
        pop.append(sched)

        if (i + 1) % 10 == 0:

            print(
                f"  Αρχικός πληθυσμός: {i+1}/{config.GA_POP}",
                flush=True
            )

    init_elapsed = time.perf_counter() - init_start

    record_time("GA αρχικός πληθυσμός", init_elapsed)

    print(
        f"Ολοκληρώθηκε ο αρχικός πληθυσμός σε "
        f"{init_elapsed:.2f} δευτερόλεπτα.",
        flush=True
    )

    best = None
    best_s = None
    stall = 0

    for g in range(config.GA_GENS):

        generation_start = time.perf_counter()

        score_start = time.perf_counter()

        scored = sorted(
            ((score(s), s) for s in pop),
            key=lambda t: t[0]
        )

        score_elapsed = time.perf_counter() - score_start

        record_time("GA αξιολόγηση πληθυσμού", score_elapsed)

        if best_s is None or scored[0][0] < best_s:

            best_s = scored[0][0]
            best = copy_sched(scored[0][1])
            stall = 0

        else:
            stall += 1

        if g % 10 == 0:

            print(
                f"GA γενιά {g:4d}: "
                f"βαθμολογία {best_s} | "
                f"αξιολόγηση {score_elapsed:.2f}s",
                flush=True
            )

        if stall >= config.GA_PATIENCE:

            print(
                f"GA: τερματισμός λόγω stagnation στη γενιά {g}."
            )

            break

        reproduction_start = time.perf_counter()

        elite = [
            copy_sched(s)
            for _, s in scored[:config.GA_POP // 10]
        ]

        parents = [
            s for _, s in scored[:config.GA_POP // 2]
        ]

        children = []

        for _ in range(config.GA_POP - len(elite)):

            child = crossover(
                random.choice(parents),
                random.choice(parents)
            )

            mutate(child)
            repair_schedule(child)

            children.append(child)

        pop = elite + children

        reproduction_elapsed = (
            time.perf_counter() - reproduction_start
        )

        record_time(
            "GA αναπαραγωγή",
            reproduction_elapsed
        )

        generation_elapsed = (
            time.perf_counter() - generation_start
        )

        record_time("GA γενιά", generation_elapsed)

        if g % 10 == 0:

            print(
                f"  Χρόνος γενιάς: {generation_elapsed:.2f}s | "
                f"Αναπαραγωγή: {reproduction_elapsed:.2f}s",
                flush=True
            )

    print(
        "GA: συνολική επιδιόρθωση καλύτερου προγράμματος...",
        flush=True
    )

    repair_start = time.perf_counter()

    best = repair_schedule(best)

    record_time(
        "GA τελική επιδιόρθωση",
        time.perf_counter() - repair_start
    )

    print(
        "GA: τοπική αναζήτηση στον καλύτερο...",
        flush=True
    )

    local_start = time.perf_counter()

    result = local_search(best)

    record_time(
        "GA local search",
        time.perf_counter() - local_start
    )

    record_time(
        "GA συνολικός χρόνος",
        time.perf_counter() - ga_start
    )

    return result
