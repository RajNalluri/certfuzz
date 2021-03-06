'''
Created on Aug 19, 2011

@organization: cert.org
'''
import logging
import math
import collections
import sys
import operator

from ..fuzztools.filetools import all_files_nonzero_length
from ..fuzztools.vectors import compare
from ..analyzers.callgrind.annotation_file import AnnotationFile

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class SimilarityMatrixError(Exception):
    pass

class SimilarityMatrix(object):
    def __init__(self, dirs):
        self.dirs = dirs
        self.pattern = '*.annotated'
        self.precision = '3'

        self.files = []
        # coverage is a dict of coverages keyed by file
        self.coverage = {}
        self.docfreq = collections.defaultdict(int)
        self.idf = {}
        self.tf_idf = {}
        self.sim = {}

        self.find_files()  # get the list of files to analyze
        if len(self.files) < 2:
            raise SimilarityMatrixError('Must have at least 2 files to compare')
        self.read_coverage()  # build a dict of coverage keyed by file
        self.measure_doc_count_by_term()  # calculate document frequency for each coverage string
        self.calculate_idf()  # calculate the IDF for each term
        self.calculate_tf_idf()  # calculate the TF-IDF vectors keyed by file
        self.build_matrix()  # Pairwise compare files based on their TF-IDF vectors

    def find_files(self):
        for d in self.dirs:
            logger.info('Find files in dir: %s', d)
            self.files.extend(list(all_files_nonzero_length(d, self.pattern)))

    def read_coverage(self):
        logger.info('Read coverage from files:')
        for f in self.files:
            logger.info('...processing file: %s', f)
            annotation = AnnotationFile(f)  # get their coverage vector
            self.coverage[f] = annotation.coverage

    def measure_doc_count_by_term(self):
        logger.info('Measuring document count by term')
        for cov in self.coverage.values():
            # each cov is a vector keyed by lib/file/function
            for term in cov.keys():
                self.docfreq[term] += 1

    def calculate_idf(self):
        logger.info('Calculating Inverse Document Frequency')
        for term in self.docfreq.keys():
            numerator = float(len(self.files))
            denominator = 1.0 + float(self.docfreq[term])
            self.idf[term] = math.log(numerator / denominator)

    def calculate_tf_idf(self):
        logger.info('Calculating Term Frequency - Inverse Document Frequency scores')
        for f in self.files:
            tf_idf = {}
            cov = self.coverage[f]
            for term, termfreq in cov.iteritems():
                tf_idf[term] = termfreq * self.idf[term]
            # store the vector for this file
            self.tf_idf[f] = tf_idf

    def build_matrix(self):
        logger.info('Building similarity matrix')
        # we're only doing the lower triangle of the matrix since
        # a) it's symmetric
        # b) the diagonal is 1.0

        for i in range(len(self.files)):
            for j in range(i):
                f = self.files[i]
                g = self.files[j]
                # create similarity matrix
                self.sim[(f, g)] = compare(self.tf_idf[f], self.tf_idf[g])

    def _crash_id_from_path(self, path):
        parts = path.split('/')
        # we assume a directory structure of <foo>/crashers/<crash_id>/<bar>
        idx = parts.index('crashers') + 1
        return parts[idx]

    def print_to(self, target=None):
        fmt = '%0.' + self.precision + 'f\t%s\t%s'

        if target:
            output = open(target, 'w')
        else:
            output = sys.stdout

        sorted_similarity = sorted(self.sim.iteritems(), key=operator.itemgetter(1))
        for (k1, k2), v in sorted_similarity:
            crash_id1 = self._crash_id_from_path(k1)
            crash_id2 = self._crash_id_from_path(k2)
            print >> output, fmt % (v, crash_id1, crash_id2)

        if target:
            output.close()
