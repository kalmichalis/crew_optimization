
from core import timing


def test_record_time_counts_calls():
    timing.TIMINGS.clear()

    timing.record_time("Genetic Algorithm", 1.5)
    timing.record_time("Genetic Algorithm", 2.5)

    assert timing.TIMINGS["Genetic Algorithm"]["calls"] == 2


def test_record_time_calculates_total():
    timing.TIMINGS.clear()

    timing.record_time("Genetic Algorithm", 1.5)
    timing.record_time("Genetic Algorithm", 2.5)

    assert timing.TIMINGS["Genetic Algorithm"]["total"] == 4.0

def test_record_time_tracks_maximum():
    timing.TIMINGS.clear()

    timing.record_time("Genetic Algorithm", 1.5)
    timing.record_time("Genetic Algorithm", 3.2)
    timing.record_time("Genetic Algorithm", 2.1)

    assert timing.TIMINGS["Genetic Algorithm"]["max"] == 3.2


def test_print_timing_summary_shows_average(capsys):
    timing.TIMINGS.clear()

    timing.record_time("Genetic Algorithm", 2.0)
    timing.record_time("Genetic Algorithm", 4.0)

    timing.print_timing_summary()

    output = capsys.readouterr().out

    assert "μέσος:" in output
    assert "3.0000s" in output



def test_record_time_keeps_algorithms_separate():
    timing.TIMINGS.clear()

    timing.record_time("Genetic Algorithm", 2.0)
    timing.record_time("CP-SAT", 1.5)

    assert timing.TIMINGS["Genetic Algorithm"]["total"] == 2.0
    assert timing.TIMINGS["CP-SAT"]["total"] == 1.5

    assert timing.TIMINGS["Genetic Algorithm"]["calls"] == 1
    assert timing.TIMINGS["CP-SAT"]["calls"] == 1


