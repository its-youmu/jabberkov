from markovchain import *
from training_algorithms import *
import os

# Builds proper path naming to prevent issues
bP1 = "training_data"
sP1 = "stored_data"
bulktrainPath = os.path.join(bP1, "*.txt")
savePath = os.path.join(sP1, "training")
renamePath = os.path.join(sP1, "training01")

# Builds a formatted string from the generator
def gen(m):
    return ''.join([w for w in m.generate_formatted(word_wrap=60, soft_wrap=True, start_with=None, max_len=100, verbose=True)])

# Initialize the chain and train it on a few of my reddit posts.
mkv = MarkovChain()
mkv.bulk_train(bulktrainPath, verbose=True)
# Or,
# mkv.load_training('training01.txt')


# Store this information for later, so that there's no need to re-train the next time.
mkv.save_training(savePath)
# Adjust the weights with the help of some fitness functions.
mkv.bulk_adjust_weights(fitness_functions=[aw_favor_alternating_complexity, aw_mul(aw_favor_punctuation, 0.5)],
                        iterations=100,
                        verbose=True)
# Save the new state to a different file, to prevent feedback loops.
mkv.save_training(renamePath)
# Print a sample output after all weights have been adjusted.
print(gen(mkv))
