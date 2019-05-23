class DualMappingObject(object):
    """
    Mapping data structure that binds a value to another.
    Unlike a standard python dictionary, elements aren't classified as keys or values, they are both.
    """
    def __init__(self, *args):
        object.__init__(self)
        self._pairs = []
        self.add(*args)

    def __contains__(self, item):
        if type(item) == tuple:
            return bool(self._twin_compare(item))
        else:
            return bool(self._deep_compare(item))

    def __iter__(self):
        for pair in self._pairs:
            yield pair

    def __getitem__(self, value):
        return self.getValue(value)

    def _twin_compare(self, pair):
        """
        Private method.
        Compares the pair in normal and reversed order such that:
        (1,0) == (1,0) == (0,1)

        return codes:
            0 : not found
            1 : matches exactly
            2 : matches reversed
        """
        if pair in self._pairs:
            return 1
        elif (pair[1],pair[0]) in self._pairs:
            return 2
        else:
            return 0

    def _deep_compare(self, value):
        """
        Private method.
        Compares the value to all values in all pairs:

        return codes:
            0 : not found
            1 : matches once
            2 : matches more than once
        """
        count = 0
        for pair in self._pairs:
            if value in pair:
                count += 1
                if count > 1:
                    return 2
        if count == 1:
            return 1
        return 0

    def add(self, *args):
        for item in args:
            if type(item) == tuple:
                if len(item) > 2:
                    raise TypeError("Only pairs of values are valid")
                else:
                    if not self._twin_compare(item): self._pairs.append(item)
            elif type(item) == list:
                for subitem in item:
                    self.add(subitem)

    def remove(self, *args):
        for item in args:
            if type(item) == tuple:
                if len(item) > 2:
                    raise TypeError("Only pairs of values are valid")
                else:
                    code = self._twin_compare(item)
                    if code == 1: self._pairs.remove(item)
                    elif code == 2: self._pairs.remove((item[1],item[0]))
                    else: raise ValueError("Value not in mapping object")
            elif type(item) == list:
                for subitem in item:
                    self.remove(subitem)

    def getPair(self, value):
        """
        Retrieve first pair containing the value from the mapping object.
        Returns a tuple.
        """
        for pair in self._pairs:
            if value in pair: return pair
        return None

    def getAllPairs(self, value):
        """
        Retrieve all matching pairs from the mapping object.
        Returns a list of tuples.
        """
        result = []
        for pair in self._pairs:
            if value in pair: result.append(pair)
        return result

    def getValue(self, value):
        """
        Retrieve mapped value of the first pair containing the queried value from the mapping object.
        Returns a value.
        """
        for pair in self._pairs:
            if value == pair[0]: return pair[1]
            elif value == pair[1]: return pair[0]
        return None

    def getAllValues(self, value):
        """
        Retrieve all values of pairs containing the queried value from the mapping object.
        Returns a list of values.
        """
        result = []
        for pair in self._pairs:
            if value == pair[0]: result.append(pair[1])
            elif value == pair[1]: result.append(pair[0])
        return result
