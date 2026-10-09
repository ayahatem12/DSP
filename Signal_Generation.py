import numpy as np


def generate_sine(A, AnalogFrequency, SamplingFrequency, PhaseShift):
    

    n = np.arange(0, SamplingFrequency)

    x = A * np.sin(
        2 * np.pi * AnalogFrequency * n / SamplingFrequency
        + PhaseShift
    )

    return n, x


def generate_cosine(A, AnalogFrequency, SamplingFrequency, PhaseShift):
    
    n = np.arange(0, SamplingFrequency)

    x = A * np.cos(
        2 * np.pi * AnalogFrequency * n / SamplingFrequency
        + PhaseShift
    )

    return n, x
