import numpy as np

def calculate_features(data):

    mean = calculate_mean(data)
    variance = calculate_variance(data, mean)
    std_dev = calculate_std_dev(variance)
    abs_derivative = calculate_abs_derivative(data)

    max_value = max(data) if data else 0
    min_value = min(data) if data else 0
    

    return {
        "Mean": mean,
        "Variance": variance,
        "StdDev": std_dev,
        "Max": max_value,
        "Min": min_value,
        "AbsDerivative": abs_derivative
    }


def compute_sma(x, y, z):
    N = len(x)
    sma = np.sum(np.abs(x) + np.abs(y) + np.abs(z)) / N
    return sma

def calculate_mean(data):
    return round(sum(data) / len(data), 3) if data else 0

def calculate_variance(data, mean):
    return round(sum((x - mean) ** 2 for x in data) / len(data) ,3) if data else 0

def calculate_std_dev(variance):
    return round(variance ** 0.5,3)

def calculate_abs_derivative(data):
    return abs(sum([data[i] - data[i - 1] for i in range(1, len(data))] if len(data) > 1 else [0]))