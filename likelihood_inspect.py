import numpy as np

L = np.load("likelihood-campaign/likelihoods.npz")
print(L['test_names'])
print(L['L'])
print(L['outcome_labels'])