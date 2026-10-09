import matplotlib.pyplot as plt

def read_signal(file_name):
    indices = []
    samples = []

    with open(file_name, "r") as file:
        file.readline()
        file.readline()

        n = int(file.readline())

        for _ in range(n):
            index, value = file.readline().split()

            indices.append(int(index))
            samples.append(float(value))

    return indices, samples



def plot_signal(indices, samples, title="Signal"):
    plt.figure()
    plt.stem(indices, samples)
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.title(title)
    plt.grid(True)
    plt.show()


def add_signals(*signals):

    all_indices = set()

    for indices, samples in signals:
        all_indices.update(indices)

    all_indices = sorted(all_indices)

    result_samples = []

    for index in all_indices:
        total = 0

        for indices, samples in signals:
            if index in indices:
                position = indices.index(index)
                total += samples[position]

        result_samples.append(total)

    return all_indices, result_samples



def multiply_signal(signal, constant):
    indices, samples = signal

    result_samples = []

    for sample in samples:
        result_samples.append(sample * constant)

    return indices, result_samples



def subtract_signals(signal1, signal2):
    negative_signal2 = multiply_signal(signal2, -1)

    result = add_signals(signal1, negative_signal2)

    return result


def shift_signal(signal, k):
    indices, samples = signal

    result_indices = []

    for index in indices:
        result_indices.append(index - k)

    return result_indices, samples


def fold_signal(signal):
    indices, samples = signal

    folded = []

    for i in range(len(indices)):
        folded.append((-indices[i], samples[i]))

    folded.sort()

    result_indices = []
    result_samples = []

    for index, sample in folded:
        result_indices.append(index)
        result_samples.append(sample)

    return result_indices, result_samples

