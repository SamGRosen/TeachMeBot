from collections import Counter, namedtuple
import random

Double = namedtuple("Double", "first", "second")


class MarkovChainer:
    def __init__(self):
        self.markovs = {}

    def chain(self, double):
        pass

    def add_triple(self, triple):
        if triple.double not in self.markovs:
            self.markovs[triple.double] = triple
        else:
            self.markovs[triple.double] += triple

    def add_sequence(self, text: str):
        triples = self.create_sequence(MarkovChainer, text)
        for triple in triples:
            self.add_triple(triple)

    def __getitem__(self, item):
        return self.markovs.get(item, Triple(item[0], item[1]))

    @staticmethod
    def create_sequence(cls, text: str):
        tokens = text.split()
        return [Triple(word, tokens[index + 1], tokens[index + 2]) for index, word in enumerate(tokens[:-2])]


class Triple:
    def __init__(self, first, second, third=None):
        self.first = first
        self.second = second
        self.third = Counter((third,)) if third else Counter()

    @property
    def double(self):
        return (self.first, self.second)

    def next(self):
        return Double(self.second, self.get_third())

    def get_third(self):
        total = sum(self.third.values())
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

    def __str__(self):
        return "({t.first}, {t.second}): {ext}".format(t=self, ext=str(self.third))

    def __repr__(self):
        return
if __name__ == '__main__':
    m = MarkovChainer()
    m.add_sequence("hello there friend of a friend!")
    print(m.markovs[("there", "friend")])