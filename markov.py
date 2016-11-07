from collections import Counter
import random
import string
import re

END_STOP = u"\u3002"


def remove_punctuation(word):
    ''' Remove punctuation, trailing whitespace, and lower a string '''
    s = re.compile('[%s]' % re.escape(string.punctuation)).sub(
        '', word).strip()
    return s


def clean(text, lower=True):
    s = remove_punctuation(utf(text))
    if lower:
        return s.lower()
    return s

def create_sequence(text: str, clean_keys=False):
    tokens = text.split()
    triples = [Triple(word, tokens[index + 1], tokens[index + 2]) for index, word in enumerate(tokens[:-2])]
    if len(tokens) > 1:
        triples.append(Triple(tokens[-2], tokens[-1], END_STOP))
    if clean_keys:
        for triple in triples:
            triple.first = clean(triple.first)
            triple.second = clean(triple.second)
    return triples

class MarkovChainer:
    def __init__(self):
        self.markovs = {}

    def chain(self, double):
        words = []
        words.extend(double)
        current_triple = self[double]
        while words[-1] != END_STOP and len(words) < 50:
            next_pair = current_triple.next()
            words.append(next_pair[-1])
            current_triple = self[next_pair]

        if words[-1] == END_STOP:
            words.pop()

        return " ".join(words)

    def add_triple(self, triple):
        if triple.double not in self.markovs:
            self.markovs[triple.double] = triple
        else:
            self.markovs[triple.double] += triple

    def add_sequence(self, text: str, clean_keys=False):
        triples = create_sequence(text, clean_keys)
        for triple in triples:
            self.add_triple(triple)

    def get_random_key(self):
        return random.choice(list(self.markovs.keys()))

    def __getitem__(self, item):
        return self.markovs.get(item, Triple(item[0], item[1]))

    def __contains__(self, item):
        return item in self.markovs


class Triple:
    def __init__(self, first, second, third=None):
        self.first = first
        self.second = second
        self.third = Counter((third,)) if third else Counter()

    @property
    def double(self):
        return self.first, self.second

    def next(self):
        return self.second, self.get_third()

    def get_third(self):
        total = sum(self.third.values())
        if total == 0:
            return END_STOP
        pick = random.randint(0, total - 1)
        count = 0
        for key, weight in self.third.items():
            count += weight
            if pick < count:
                return key

    def add_word(self, word):
        self.third[word] = self.third.get(word, 0) + 1

    def __add__(self, other):
        new = Triple(self.first, self.second)
        new.third = self.third + other.third
        return new

    def __iadd__(self, other):
        self.third += other.third
        return self

    def __str__(self):
        return "({t.first}, {t.second}): {ext}".format(t=self, ext=str(self.third))

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':
    test_string = "hello there friend of a friend! it is so of a friend of a pal very nice to meet you say hello to your friend pally."
    m = MarkovChainer()
    m.add_sequence(test_string)
    print(m.markovs[("there", "friend")])
