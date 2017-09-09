import re
import random
import glob
import pickle
from functools import reduce


class MarkovChain:
    def __init__(self, vForce=False):
        self.tree = dict()
        self.vForce = vForce

    '''
    Trains the generator on a block of text.
    '''
    def train(self, text, factor=1):
        # Split text at every space (including tabs and newlines),
        # and remove empty entries. This keeps punctuation at the
        # end of words containing it. If you do not care about
        # punctuation, include it in the split regex.
        words = filter(lambda s: len(s) > 0, re.split(r'[\s"]', text))
        # Casing is not as important as punctuation.
        words = [w.lower() for w in words]
        # "For each pair of words contained within the corpus:"
        for a, b in [(words[i], words[i + 1]) for i in range(len(words) - 1)]:
            # If a branch for "a" doesn't exist, create it.
            if a not in self.tree:
                self.tree[a] = dict()
            # If a leaf "b" hasn't yet grown on branch "a", create it w/
            # a value of "factor". Otherwise, add its value multiplied by "factor" to it.
            self.tree[a][b] = factor if b not in self.tree[a] else self.tree[a][b] + self.tree[a][b] * factor

    '''
    Trains the generator on a single file.
    '''
    def train_on_file(self, filename, encodings=None, verbose=False):
        encodings = encodings if encodings is not None else ['utf-8']
        ret = False
        # If your input files have mismatching encoding, try a few, good ones. If all fails, report back.
        for encoding in encodings:
            try:
                with open(filename, 'r', encoding=encoding) as f:
                    self.train(f.read())
                if verbose:
                    print('Successfully trained on "{0}". [ENCODING: {1}]'.format(filename, encoding))
                ret = True
                break
            except UnicodeDecodeError:
                if verbose:
                    print('Unable to decode "{0}" for training. [ENCODING: {1}]'.format(filename, encoding))

        if verbose:
            print()

        return ret

    '''
    Serializes the tree to a file.
    '''
    def save_training(self, file):
        with open(file, 'wb') as f:
            pickle.dump(self.tree, f)

    '''
    Deserializes the tree from a file.
    '''
    def load_training(self, file):
        with open(file, 'rb') as f:
            self.tree = pickle.load(f)

    '''
    Trains the generator on a single file, or on a list of files, and saves the state to disk upon finishing. (Uses glob patterns!)
    Returns the number of files successfully parsed and trained on.
    '''
    def bulk_train(self, path, verbose=False):
        i = 0
        for filename in glob.glob(path):
            if self.train_on_file(filename, verbose=verbose):
                i += 1
            elif verbose:
                print('Unable to train on "{0}".'.format(filename))

        if verbose:
            print('Successfully trained on {0} files.'.format(i))

        return i


    '''
    Yields a sequence of words until a dead end is found or until a maximum length, if specified, is reached.
    '''
    def generate(self, start_with=None, max_len=20, rand=lambda x: random.random(), verbose=False):
        # If there's nothing here, end
        if len(self.tree) == 0:
            return

        # Start with a given word, or randomize one that exists already.
        word = start_with if start_with is not None else random.choice([key for key in self.tree])
        if verbose:
            print('Generating a sentence of {0}, starting with "{1}":\n'
                  .format('max. {0} words'.format(max_len) if max_len > 0 else 'unspecified length', word))

        # If this word doesn't have a first-level entry in the tree
        # (i.e. no word was ever found next to it during training),
        # GENERATE A NEW ONE, we want a sentence.  Otherwise, yield the starting word
        if word not in self.tree:
            self.vForce = True
            return
        else:
            yield word

        i = 1
        while max_len == 0 or i < max_len:
            q = 0
            i += 1
            # this is a safety catch -end the chain if it reaches
            if word not in self.tree:
                return

            # Otherwise, randomize against the weight of each leaf word divided by the number of leaves.
            dist = sorted(((w, rand(self.tree[word][w] // len(self.tree[word]))) for w in self.tree[word]),
                          # And sort the result in decreasing order.
                          key=lambda k: 1-k[1])

            # And yield the highest scoring word
            word = dist[0][0]

            # Go through checks to try and stop from repeating numbers
            # Especially troublesome if you can't intelligently sanitize numbers
            # from the database efficiently - often generates strings of numbers
            while q < 2:
                if word.isdigit() is True:
                    dist = sorted(((w, rand(self.tree[word][w] // len(self.tree[word]))) for w in self.tree[word]),
                                    key=lambda k: 1-k[1])
                    q += 1
                else: break
            yield word

    '''
    Adjusts the relationships between branch and leaf according to a fitness function f.
    '''
    def adjust_weights(self, max_len=2, f=lambda a, b: 0):
        # Generate a number of words stochastically
        pairs = [w.lower() for w in self.generate(max_len=max_len, rand=lambda r: random.random() * r)]
        # Create the pairs a,b b,c, c,d ...
        pairs = [[pairs[i], None if i == len(pairs) - 1 else pairs[i + 1]] for i in range(len(pairs))][:-1]
        # Get the fitness for each pair, and convert it from the 0,1 range to the -1,1 range.
        factors = [(f(*p) - 0.5) * 2 for p in pairs]
        # Train the model on the pair p by a factor x
        for p, x in zip(pairs, factors):
            if x < -1 or x > 1:
                raise ValueError(x)
            self.train(reduce(lambda a, b: '{0} {1}'.format(a, b), p), x)

    '''
    Calls adjust_weights with the multiplied result of multiple fitness functions, for a given number of iterations.
    If verbose==True, shows a neat progress bar.
    '''
    def bulk_adjust_weights(self, fitness_functions=None, iterations=1, pbar_len=14, verbose=False):
        # Used to flush stdout to properly show the progress bar
        import sys

        if fitness_functions is None or len(fitness_functions) == 0:
            return

        if verbose:
            print('Beginning training with {0} algorithms.'.format(len(fitness_functions)))

        for i in range(iterations):
            self.adjust_weights(f=lambda a, b: reduce(lambda x, y: x * y, [ff(a, b) for ff in fitness_functions]))
            if verbose and i % (iterations // pbar_len + 1) == 0:
                progress = i / iterations
                pbar_full = int(progress * pbar_len)
                pbar_empty = pbar_len - pbar_full

                print('\r[{0}{1}] - {2:.2f}%'.format('=' * pbar_full, '-' * pbar_empty, progress * 100), end='')
                sys.stdout.flush()

        if verbose:
            print('\r[{0}] - {1:.2f}%'.format('=' * pbar_len, 100))
            print('Training complete.')
