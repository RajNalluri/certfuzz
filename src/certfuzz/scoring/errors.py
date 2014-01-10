'''
Created on Feb 22, 2013

@organization: cert.org
'''
from ..errors import CERTFuzzError


class ScoringError(CERTFuzzError):
    pass


class ScorableSetError(ScoringError):
    pass


class EmptySetError(ScorableSetError):
    pass
