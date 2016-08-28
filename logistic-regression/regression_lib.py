# Common library code for running logistic regressions and classifiers.
#
# Eli Bendersky (http://eli.thegreenplace.net)
# This code is in the public domain
import numpy as np


def augment_1s_column(X):
    """Augment the given data matrix with a first column of ones.

    X: (k, n) k rows of data items, each having n features.

    Returns a (k, n+1) matrix with an additional column of 1s at the start.
    """
    return np.hstack((np.ones((X.shape[0], 1)), X))


def feature_normalize(X):
    """Normalize the feature matrix X.

    Given a feature matrix X, where each row is a vector of features, normalizes
    each feature. Returns (X_norm, mu, sigma) where mu and sigma are the mean
    and stddev of features (vectors).
    """
    num_features = X.shape[1]
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    X_norm = (X - mu) / sigma
    return X_norm, mu, sigma


def predict_binary(X, theta):
    """Make classification predictions for the data in X using theta.

    X: (k, n) k rows of data items, each having n features; augmented.
    theta: (n, 1) regression parameters.

    Returns yhat (k, 1) - either +1 or -1 classification for each item.
    """
    yhat = X.dot(theta)
    return np.sign(yhat)


def sigmoid(z):
    """Compute sigmoid function.

    z: array of input values.

    Returns array of outputs, sigmoid(z).
    """
    return 1 / (1 + np.exp(-z))


def predict_logistic_probability(X, theta):
    """Make classification predictions for the data in X using theta.

    X: (k, n) k rows of data items, each having n features; augmented.
    theta: (n, 1) logistic regression parameters.

    Computes the logistic regression prediction. Returns yhat (k, 1) - number
    in the range [0.0, 1.0) for each item. The number is the probability that
    the item is classified as +1.
    """
    z = X.dot(theta)
    return sigmoid(z)


# See the docstring of gradient_descent for the description of the signature of
# loss functions.
def square_loss(X, y, theta, reg_beta=0.0):
    """Computes squared loss and gradient.

    Based on mean square margin loss.

    Note: the mean (division by k) helps; otherwise, the loss is very large and
    tiny learning rate is required to prevent divergence in the beginning of
    the search.
    """
    k, n = X.shape
    margin = y * X.dot(theta)
    diff = margin - 1
    loss = np.dot(diff.T, diff) / k + np.dot(theta.T, theta) * reg_beta / 2

    dtheta = np.zeros_like(theta)
    for j in range(n):
        dtheta[j, 0] = (2 * np.dot((diff * y).T, X[:, j]) / k +
                        reg_beta * theta[j, 0])
    return loss.flat[0], dtheta


def hinge_loss(X, y, theta, reg_beta=0.0):
    """Compute hinge loss and gradient."""
    k, n = X.shape
    # margin is (k, 1)
    margin = y * X.dot(theta)
    loss = (np.sum(np.maximum(np.zeros_like(margin), 1 - margin)) / k +
            np.dot(theta.T, theta) * reg_beta / 2)

    dtheta = np.zeros_like(theta)
    # yx is (k, n) where the elementwise multiplication by y is broadcase across
    # the whole X.
    yx = y * X
    # We're going to select columns of yx, and each column turns into a vector.
    # Precompute the margin_selector vector which has for each j whether the
    # margin for that j was < 1.
    # Note: still keeping an explicit look over n since I don't expect the
    # number of features to be very large. It's possibly to fully vectorize this
    # but that would make the computation even more obscure. I'll do that if
    # performance becomes an issue with this version.
    margin_selector = (margin < 1).ravel()
    for j in range(n):
        # Sum up the contributions to the jth theta element gradient from all
        # input samples.
        dtheta[j, 0] = (np.sum(np.where(margin_selector, -yx[:, j], 0)) / k +
                        reg_beta * theta[j, 0])
    return loss.flat[0], dtheta


def gradient_descent(X, y, lossfunc=None, nsteps=100, learning_rate=0.1):
    """Runs gradient descent optimization to minimize loss for X, y.

    X: (k, n) data items.
    y: (k, 1) result (+1 or -1) for each data item in X.
    lossfunc:
        a function computing loss and gradients.
        Takes (X, y, theta). theta is a (n, 1) parameter array.
        Returns (loss, dtheta) where loss is the numeric loss for this theta,
        and dtheta is (n, 1) gradients for theta based on that loss.
    nsteps: how many steps to run.
    learning_rate: learning rate update (multiplier of gradient).

    Yields 'nsteps + 1' pairs of (theta, loss). The first pair yielded is the
    initial theta and its loss; the rest carry results after each of the
    iteration steps.
    """
    k, n = X.shape
    theta = np.zeros((n, 1))
    loss, dtheta = lossfunc(X, y, theta)
    yield theta, loss
    for step in range(nsteps):
        theta -= learning_rate * dtheta
        loss, dtheta = lossfunc(X, y, theta)
        yield theta, loss