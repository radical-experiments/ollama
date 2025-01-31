#!/usr/bin/env python3

import random

import numpy as np


def get_seed():
    rgen  = np.random.default_rng()
    seeds = rgen.normal(4.44, 0.55, size=5_000)

    seeds.mean()
    seeds.std()

    while True:
        seed = max(random.choice(seeds), 2.22)
        yield float(seed)


if __name__ == '__main__':

    seed = get_seed()

    for _ in range(10):
        print(next(seed))

