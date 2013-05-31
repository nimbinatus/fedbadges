# -*- coding; utf-8 -*-
""" Models for fedbadges.

The primary thing here is a "BadgeRule" which is an in-memory working
abstraction of the trigger and criteria required to award a badge.

Authors:    Ralph Bean
"""

import abc

operator_fields = set([
    "all",
    "any",
    #"not",
])
# TODO -- lambdas?


class BadgeRule(object):
    required_fields = set([
        'name',
        'description',
        'creator',
        'discussion',
        'trigger',
        'criteria',
    ])

    def __init__(self, badge_dict):
        for field in self.required_fields:
            # TODO - do set magic here
            if not field in badge_dict:
                raise ValueError("BadgeRule requires %r" % field)

        self._d = badge_dict

        self.trigger = Trigger(self._d['trigger'])
        self.criteria = Criteria(self._d['criteria'])

    def __getitem__(self, key):
        return self._d[key]

    def matches(self, msg):
        if not self.trigger.matches(msg):
            return False
        if not self.criteria.matches(msg):
            return False
        return True


class BaseComparator(object):
    """ Base class for shared behavior between trigger and criteria. """
    __metaclass__ = abc.ABCMeta

    def __init__(self, d):
        for field in d:
            # TODO -- do set magic here
            if not field in self.possible_fields:
                raise KeyError("%r is not a possible field" % field)
        self._d = d

    @abc.abstractmethod
    def matches(self, msg):
        pass


class Trigger(BaseComparator):
    possible_fields = set([
        'topic',
        'category',
    ]).union(operator_fields)
    children = None

    def __init__(self, d):
        super(Trigger, self).__init__(d)

        if len(self._d) > 1:
            raise ValueError("No more than one trigger allowed.  "
                             "Use an operator, one of %r" % operator_fields)
        self.attribute = self._d.keys()[0]
        self.expected_value = self._d[self.attribute]

        # Check if we should we recursively nest Triggers?
        if self.attribute in operator_fields:

            if not isinstance(self.expected_value, list):
                raise TypeError("Operators only accept lists, not %r" %
                                 type(self.expected_value))

            self.children = [Trigger(child) for child in self.expected_value]

    def matches(self, msg):
        # Check if we should just aggregate the results of our children.
        # Otherwise, we are a leaf-node doing a straightforward comparison.
        if self.children:
            return __builtins__[self.attribute]([
                child.matches(msg) for child in self.children
            ])
        elif self.attribute == 'category':
            # TODO -- use fedmsg.meta.msg2processor(msg).__name__.lower()
            return msg['topic'].split('.')[3] == self.expected_value
        else:
            return msg[self.attribute] == self.expected_value


class Criteria(BaseComparator):
    possible_fields = set([
        'datanommer',
    ]).union(operator_fields)

    def matches(self, msg):
        raise NotImplementedError("need to write this")
