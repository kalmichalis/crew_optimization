
import math
import random
import time

from core import config
from core import data
from core.rules import rules_errors
from core.scoring import score
from core.timing import record_time



def copy_day(day):
    return {
        "crew": day["crew"][:],
        "duty": day["duty"],
        "mech": day["mech"],
        "elec": day["elec"]
    }


def copy_sched(sched):
    return [
        copy_day(day)
        for day in sched
    ]




def create_initial_solution(rng):

    for attempt in range(1000):

        sched = []
        failed = False

        for day_index in config.R:

            # Άτομα που μπορούν να αναλάβουν σήμερα
            available = [
                m for m in data.names
                if all(
                    m not in sched[d]["crew"]
                    for d in range(
                        max(0, day_index - config.MIN_GAP + 1),
                        day_index
                    )
                )
            ]

            # Επιλογή μηχανικού
            mech_candidates = [
                m for m in available
                if m in data.MECH
            ]

            if not mech_candidates:
                failed = True
                break

            mech = rng.choice(mech_candidates)

            # Επιλογή ηλεκτρολόγου
            elec_candidates = [
                m for m in available
                if m in data.ELEC and m != mech
            ]

            if not elec_candidates:
                failed = True
                break

            elec = rng.choice(elec_candidates)

            # Επιλογή υπόλογου
            duty_candidates = [
                m for m in available
                if m in data.DUTY_OK
            ]

            if not duty_candidates:
                failed = True
                break

            duty = rng.choice(duty_candidates)

            crew = [mech, elec]

            if duty not in crew:
                crew.append(duty)

            remaining = [
                m for m in available
                if m not in crew
            ]

            needed = config.CREW - len(crew)

            if len(remaining) < needed:
                failed = True
                break

            crew.extend(rng.sample(remaining, needed))

            sched.append({
                "crew": crew,
                "duty": duty,
                "mech": mech,
                "elec": elec
            })

        if not failed:
            return sched

    raise RuntimeError(
        "Δεν βρέθηκε έγκυρη αρχική λύση μετά από 1000 προσπάθειες."
    )





def create_neighbor(sched, rng, stats=None):
    def invalid(reason, trial=None):

        if stats is not None:

            stats["invalid"] += 1
            stats[f"invalid_{reason}"] += 1

            if trial is not None:

                categories = diagnose_invalid_rules(trial)

                for category in categories:
                    stats[f"invalid_{category}"] += 1

        return copy_sched(sched)

    # Τυχαία επιλογή ημέρας και θέσης πληρώματος
    day_index = rng.randrange(config.DAYS)
    idx = rng.randrange(config.CREW)

    day = sched[day_index]
    old_member = day["crew"][idx]

    # Ρόλοι που κατέχει το παλιό μέλος
    roles = [
        role
        for role in ("duty", "mech", "elec")
        if day[role] == old_member
    ]

    # Τυχαία επιλογή ατόμου εκτός πληρώματος
    candidates = [
        m for m in data.names
        if m not in day["crew"]
    ]

    new_member = rng.choice(candidates)

    # Έλεγχος προσόντων
    if "duty" in roles and new_member not in data.DUTY_OK:
        return invalid("duty")

    if "mech" in roles and new_member not in data.MECH:
        return invalid("mech")

    if "elec" in roles and new_member not in data.ELEC:
        return invalid("elec")

    # Δημιουργία νέας λύσης
    trial = copy_sched(sched)
    trial_day = trial[day_index]

    trial_day["crew"][idx] = new_member

    for role in roles:
        trial_day[role] = new_member

    # Μηχανικός και ηλεκτρολόγος πρέπει να είναι διαφορετικοί
    if trial_day["mech"] == trial_day["elec"]:
        return invalid("role_conflict")

    # Έλεγχος όλων των σκληρών περιορισμών
    if rules_errors(trial):
        return invalid("gap_or_other", trial)

    return trial

def create_neighbor_smart(sched, rng, stats=None):
    day_index = rng.randrange(config.DAYS)
    idx = rng.randrange(config.CREW)

    day = sched[day_index]
    old_member = day["crew"][idx]

    roles = [
        role
        for role in ("duty", "mech", "elec")
        if day[role] == old_member
    ]

    # Άτομα που δεν συμμετέχουν ήδη στη συγκεκριμένη ημέρα
    candidates = [
        m for m in data.names
        if m not in day["crew"]
    ]

    # Έλεγχος ελάχιστης χρονικής απόστασης
    available_candidates = [
        m for m in candidates
        if all(
            m not in sched[d]["crew"]
            for d in range(
                max(0, day_index - config.MIN_GAP + 1),
                min(config.DAYS, day_index + config.MIN_GAP)
            )
            if d != day_index
        )
    ]

    if not available_candidates:
        return copy_sched(sched)

    new_member = rng.choice(available_candidates)
    # Έλεγχος προσόντων για τους ρόλους που κατείχε το παλιό μέλος
    if "duty" in roles and new_member not in data.DUTY_OK:
        if stats is not None:
            stats["invalid"] += 1
            stats["invalid_duty"] += 1

        return copy_sched(sched)

    if "mech" in roles and new_member not in data.MECH:
        if stats is not None:
            stats["invalid"] += 1
            stats["invalid_mech"] += 1

        return copy_sched(sched)

    if "elec" in roles and new_member not in data.ELEC:
        if stats is not None:
            stats["invalid"] += 1
            stats["invalid_elec"] += 1

        return copy_sched(sched)
    trial = copy_sched(sched)
    trial_day = trial[day_index]

    # Αντικατάσταση μέλους πληρώματος
    trial_day["crew"][idx] = new_member

    # Ενημέρωση των ρόλων που κατείχε το παλιό μέλος
    for role in roles:
        trial_day[role] = new_member

    # Έλεγχος σύγκρουσης μηχανικού και ηλεκτρολόγου
    if trial_day["mech"] == trial_day["elec"]:

        if stats is not None:
            stats["invalid"] += 1
            stats["invalid_role_conflict"] += 1

        return copy_sched(sched)

    # Τελικός έλεγχος όλων των σκληρών περιορισμών
    if rules_errors(trial):

        if stats is not None:
            stats["invalid"] += 1
            stats["invalid_gap_or_other"] += 1

        return copy_sched(sched)

    return trial


def create_neighbor_swap(sched, rng, stats=None):

    def invalid(reason, trial=None):

        if stats is not None:

            stats["invalid"] += 1
            stats[f"invalid_{reason}"] += 1

            if trial is not None:

                categories = diagnose_invalid_rules(trial)

                for category in categories:
                    stats[f"invalid_{category}"] += 1

        return copy_sched(sched)

    # Επιλογή δύο διαφορετικών ημερών
    day_a, day_b = rng.sample(range(config.DAYS), 2)

    # Επιλογή μίας τυχαίας θέσης από κάθε πλήρωμα
    idx_a = rng.randrange(config.CREW)
    idx_b = rng.randrange(config.CREW)

    member_a = sched[day_a]["crew"][idx_a]
    member_b = sched[day_b]["crew"][idx_b]

    # Δημιουργία αντιγράφου της λύσης
    trial = copy_sched(sched)

    # Ανταλλαγή των δύο ατόμων
    trial[day_a]["crew"][idx_a] = member_b
    trial[day_b]["crew"][idx_b] = member_a

    # Έλεγχος ειδικών ρόλων
    roles_a = [
        role for role in ("duty", "mech", "elec")
        if sched[day_a][role] == member_a
    ]

    roles_b = [
        role for role in ("duty", "mech", "elec")
        if sched[day_b][role] == member_b
    ]

    # Έλεγχος προσόντων πρώτης ημέρας
    if "duty" in roles_a and member_b not in data.DUTY_OK:
        return invalid("duty")

    if "mech" in roles_a and member_b not in data.MECH:
        return invalid("mech")

    if "elec" in roles_a and member_b not in data.ELEC:
        return invalid("elec")

    # Έλεγχος προσόντων δεύτερης ημέρας
    if "duty" in roles_b and member_a not in data.DUTY_OK:
        return invalid("duty")

    if "mech" in roles_b and member_a not in data.MECH:
        return invalid("mech")

    if "elec" in roles_b and member_a not in data.ELEC:
        return invalid("elec")

    # Μεταφορά ειδικών ρόλων
    for role in roles_a:
        trial[day_a][role] = member_b

    for role in roles_b:
        trial[day_b][role] = member_a

    # Έλεγχος σύγκρουσης ρόλων
    if trial[day_a]["mech"] == trial[day_a]["elec"]:
        return invalid("role_conflict")

    if trial[day_b]["mech"] == trial[day_b]["elec"]:
        return invalid("role_conflict")

    # Έλεγχος όλων των σκληρών περιορισμών
    if rules_errors(trial):
        return invalid("gap_or_other", trial)

    return trial



def diagnose_invalid_rules(sched):

    errors = rules_errors(sched)

    if not errors:
        return []

    categories = []

    for error in errors:

        if "απόσταση" in error:
            categories.append("minimum_gap")

        elif "διακριτά άτομα" in error:
            categories.append("crew_size")

        elif "ρόλος εκτός βάρδιας" in error:
            categories.append("role_outside_crew")

        else:
            categories.append("other")

    return categories



def lexicographic_cost(score_tuple):
    """
    Μετατρέπει τη λεξικογραφική βαθμολογία
    σε έναν αριθμητικό δείκτη κόστους.

    Διατηρεί αυστηρά τη σειρά προτεραιότητας
    των επτά κριτηρίων μετά τους σκληρούς κανόνες.
    """

    if score_tuple[0] != 0:
        raise ValueError(
            "Ο SA δέχεται μόνο λύσεις χωρίς παραβιάσεις."
        )

    values = score_tuple[1:]

    max_assignments = config.DAYS * config.CREW
    max_order = max(data.ORDER.values(), default=0)
    n = data.N

    # Συντηρητικά άνω όρια για κάθε κριτήριο
    max_dist = (
        100 * max_assignments * (max_assignments + 1) // 2
        + max_assignments * max_order
    )

    bounds = [
        max_assignments,
        max_dist,
        n,
        n * (n - 1),
        len(config.HOLIDAYS) * config.CREW * max_order,
        n,
        n * (n - 1)
    ]

    # Mixed-radix encoding
    cost = 0

    for value, bound in zip(values, bounds):

        if value < 0 or value > bound:
            raise ValueError(
                f"Το κριτήριο {value} υπερβαίνει το όριο {bound}."
            )

        cost = cost * (bound + 1) + value

    return cost



def accept_solution(current_score, new_score, temperature, rng):

    current_cost = lexicographic_cost(current_score)
    new_cost = lexicographic_cost(new_score)

    # Καλύτερη ή ισοδύναμη λύση
    if new_cost <= current_cost:
        return True

    # Δεν δεχόμαστε χειρότερη λύση με μηδενική θερμοκρασία
    if temperature <= 0:
        return False

    # Διαφορά κόστους
    delta = new_cost - current_cost

    # Πιθανότητα αποδοχής χειρότερης λύσης
    probability = math.exp(-delta / temperature)

    return rng.random() < probability





def calibrate_temperature(
    sched,
    rng,
    samples=100,
    target_acceptance=0.80,
    neighbor_fn=create_neighbor
):

    current_score = score(sched)
    current_cost = lexicographic_cost(current_score)

    positive_deltas = []

    for _ in range(samples):

        neighbor = neighbor_fn(sched, rng)
        neighbor_score = score(neighbor)
        neighbor_cost = lexicographic_cost(neighbor_score)

        delta = neighbor_cost - current_cost

        if delta > 0:
            positive_deltas.append(delta)

    if not positive_deltas:
        return 1.0

    # Διάμεσος θετικών μεταβολών
    positive_deltas.sort()

    middle = len(positive_deltas) // 2

    if len(positive_deltas) % 2 == 0:
        median_delta = (
            positive_deltas[middle - 1]
            + positive_deltas[middle]
        ) / 2
    else:
        median_delta = positive_deltas[middle]

    # Θερμοκρασία για αρχική πιθανότητα αποδοχής 80%
    temperature = -median_delta / math.log(target_acceptance)

    return temperature



def cool_temperature(temperature, alpha=0.95):
    return temperature * alpha




def create_sa_stats():

    return {
        "better_accepted": 0,
        "worse_accepted": 0,
        "rejected": 0,
        "invalid": 0,

        "invalid_duty": 0,
        "invalid_mech": 0,
        "invalid_elec": 0,
        "invalid_role_conflict": 0,
        "invalid_gap_or_other": 0,
        "invalid_minimum_gap": 0,
        "invalid_crew_size": 0,
        "invalid_role_outside_crew": 0,
        "invalid_other": 0
    }



def solve_sa(
    iterations_per_temp=100,
    max_levels=200,
    alpha=0.95,
    neighbor_fn=create_neighbor,
    seed=None
):

    start_time = time.perf_counter()

    # Ανεξάρτητη γεννήτρια τυχαίων αριθμών
    # Αν δεν δοθεί seed, χρησιμοποιούμε το προκαθορισμένο seed του config.
    # Διαφορετικά, χρησιμοποιούμε το seed που δόθηκε κατά την κλήση.
    if seed is None:
        seed = config.SEED

    rng = random.Random(seed)

    print("SA: δημιουργία αρχικής λύσης...", flush=True)

    # Αρχική λύση
    current = create_initial_solution(rng)
    current_score = score(current)
    initial_score = current_score
    stats = create_sa_stats()
    best = copy_sched(current)
    best_score = current_score

    # Αρχική θερμοκρασία
    temperature = calibrate_temperature(
        current,
        rng,
        neighbor_fn=neighbor_fn
    )

    initial_temperature = temperature

    print(
        f"SA: αρχική θερμοκρασία {temperature:.4f}",
        flush=True
    )

    # Κύριος βρόχος Simulated Annealing
    for level in range(max_levels):

        for iteration in range(iterations_per_temp):


            neighbor = neighbor_fn(current, rng, stats)

            # Έλεγχος αν δημιουργήθηκε έγκυρη νέα λύση
            if neighbor == current:

                continue

            neighbor_score = score(neighbor)

            # Έλεγχος αν η νέα λύση είναι καλύτερη
            if neighbor_score < current_score:
                stats["better_accepted"] += 1

                current = neighbor
                current_score = neighbor_score

            # Έλεγχος αν είναι χειρότερη
            elif neighbor_score > current_score:

                if accept_solution(
                    current_score,
                    neighbor_score,
                    temperature,
                    rng
                ):
                    stats["worse_accepted"] += 1

                    current = neighbor
                    current_score = neighbor_score

                else:
                    stats["rejected"] += 1

            # Ισοδύναμη βαθμολογία
            else:
                current = neighbor
                current_score = neighbor_score


            # Ενημέρωση καλύτερης λύσης
            if current_score < best_score:

                best = copy_sched(current)
                best_score = current_score

        # Ενημέρωση θερμοκρασίας
        temperature = cool_temperature(
            temperature,
            alpha
        )

        if level % 10 == 0:

            print(
                f"SA επίπεδο {level:4d} | "
                f"Θερμοκρασία: {temperature:.6f} | "
                f"Καλύτερη βαθμολογία: {best_score}",
                flush=True
            )

        # Τερματισμός όταν η θερμοκρασία γίνει πολύ μικρή
        if temperature <= initial_temperature * 1e-8:
            break

    record_time(
        "SA συνολικός χρόνος",
        time.perf_counter() - start_time
    )

    print(
        f"SA: ολοκληρώθηκε σε "
        f"{time.perf_counter() - start_time:.2f}s",
        flush=True
    )


    print("\n=== SA ΣΤΑΤΙΣΤΙΚΑ ΚΙΝΗΣΕΩΝ ===")
    print("Καλύτερες αποδεκτές: ", stats["better_accepted"])
    print("Χειρότερες αποδεκτές:", stats["worse_accepted"])
    print("Απορριφθείσες:       ", stats["rejected"])
    print("Μη έγκυρες προτάσεις:", stats["invalid"])
    print("\n=== ΑΙΤΙΕΣ ΜΗ ΕΓΚΥΡΩΝ ΠΡΟΤΑΣΕΩΝ ===")
    print("Υπόλογος:", stats["invalid_duty"])
    print("Μηχανικός:", stats["invalid_mech"])
    print("Ηλεκτρολόγος:", stats["invalid_elec"])
    print("Σύγκρουση ρόλων:", stats["invalid_role_conflict"])
    print("Χρονικός περιορισμός / άλλος κανόνας:",
          stats["invalid_gap_or_other"])
    total_moves = (
            stats["better_accepted"]
            + stats["worse_accepted"]
            + stats["rejected"]
            + stats["invalid"]
    )
    print("\n=== ΑΝΑΛΥΣΗ ΠΑΡΑΒΙΑΣΕΩΝ ΚΑΝΟΝΩΝ ===")
    print("Ελάχιστη απόσταση:", stats["invalid_minimum_gap"])
    print("Μέγεθος πληρώματος:", stats["invalid_crew_size"])
    print("Ρόλος εκτός πληρώματος:", stats["invalid_role_outside_crew"])
    print("Άλλες παραβιάσεις:", stats["invalid_other"])

    print("Σύνολο κινήσεων:     ", total_moves)

    print("Αρχική λύση:       ", initial_score)
    print("Καλύτερη λύση:     ", best_score)
    print("Τελική τρέχουσα:   ", current_score)

    return best, best_score
