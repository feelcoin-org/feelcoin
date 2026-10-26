"""Synthetic hashrate-change study for Feelcoin v17, not a consensus test.
Run: python3 tests/difficulty/feelcoin_lwma_simulation.py
"""
import random
import statistics


def retarget(timestamps, cumulative, window=90, target=120):
    if len(timestamps) < window + 1:
        return 1000
    first = len(timestamps) - window - 1
    previous = timestamps[first]
    weighted = 0
    for i in range(1, window + 1):
        t = timestamps[first + i]
        if t > previous:
            solvetime = min(t - previous, 6 * target)
            previous = t
        else:
            solvetime = 1
            previous += 1
        weighted += i * solvetime
    weighted = max(weighted, max(1, window * window * target // 20))
    return max(1, (cumulative[-1] - cumulative[first]) * (window + 1) * target // (2 * weighted))


def run(window, hashrate_ratio, seed):
    random.seed(seed)
    timestamps = [1_900_000_000]
    cumulative = [1000]
    difficulty = 1000
    samples = []

    for height in range(450):
        ratio = 1 if height < 210 else hashrate_ratio
        mean_solvetime = 120 * difficulty / (1000 * ratio)
        solvetime = max(1, round(random.expovariate(1 / mean_solvetime)))
        timestamps.append(timestamps[-1] + solvetime)
        cumulative.append(cumulative[-1] + difficulty)
        difficulty = retarget(timestamps, cumulative, window) if len(timestamps) > window else 1000
        if height >= 210:
            samples.append((solvetime, difficulty))
    return samples


def main():
    for ratio in (0.1, 0.5, 2, 10):
        print("Hashrate ratio:", ratio)
        for window in (60, 90):
            trials = [run(window, ratio, seed) for seed in range(100)]
            first_25 = statistics.mean(statistics.mean(s[0] for s in trial[:25]) for trial in trials)
            next_50 = statistics.mean(statistics.mean(s[0] for s in trial[25:75]) for trial in trials)
            median_difficulty_75 = statistics.median(trial[75][1] for trial in trials)
            print("  window", window,
                  "mean first 25 solve seconds", round(first_25),
                  "mean next 50 solve seconds", round(next_50),
                  "median difficulty after 75 blocks", median_difficulty_75)


if __name__ == "__main__":
    main()
