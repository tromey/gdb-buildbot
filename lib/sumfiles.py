# Functions for manipulating .sum summary files.

import re
import os.path
from StringIO import StringIO

# Helper regex for parse_sum_line.
sum_matcher = re.compile('^(.?(PASS|FAIL)): (.*)$')

# You must call set_web_base at startup to set this.
gdb_web_base = None

def set_web_base(arg):
    global gdb_web_base
    gdb_web_base = arg
    if not os.path.isdir(gdb_web_base):
        # If the parent doesn't exist, we're confused.
        # So, use mkdir and not makedirs.
        os.mkdir(gdb_web_base, 0755)

class DejaResults(object):
    def __init__(self):
        object.__init__(self)

    # Parse a single line from a .sum file.
    # Uniquify the name, and put the result into OUT_DICT.
    # If the line does not appear to be about a test, ignore it.
    def parse_sum_line(self, out_dict, line):
        global sum_matcher
        line = line.rstrip()
        m = re.match(sum_matcher, line)
        if m:
            result = m.group(1)
            test_name = m.group(3)
            if test_name in out_dict:
                i = 2
                while True:
                    nname = test_name + ' <<' + str(i) + '>>'
                    if nname not in out_dict:
                        break
                    i = i + 1
                test_name = nname
            out_dict[test_name] = result

    def _write_sum_file(self, sum_dict, subdir, filename):
        global gdb_web_base
        bdir = os.path.join(gdb_web_base, subdir)
        if not os.path.isdir(bdir):
            os.makedirs(bdir, 0755)
        fname = os.path.join(bdir, filename)
        keys = sum_dict.keys()
        keys.sort()
        f = open(fname, 'w')
        for k in keys:
            f.write(sum_dict[k] + ': ' + k + '\n')
        f.close()

    def write_sum_file(self, sum_dict, builder, filename):
        self._write_sum_file(sum_dict, builder, filename)

    def write_baseline(self, sum_dict, builder, branch):
        self.write_sum_file(sum_dict, os.path.join(builder, branch), 
                            'baseline')

    # Read a .sum file.
    # The builder name is BUILDER.
    # The base file name is given in FILENAME.  This should be a git
    # revision; to read the baseline file for a branch, use `read_baseline'.
    # Returns a dictionary holding the .sum contents, or None if the
    # file did not exist.
    def read_sum_file(self, builder, filename):
        global gdb_web_base
        fname = os.path.join(gdb_web_base, builder, filename)
        if os.path.exists(fname):
            result = {}
            f = open(fname, 'r')
            for line in f:
                self.parse_sum_line (result, line)
            f.close()
        else:
            result = None
        return result

    def read_baseline(self, builder, branch):
        return self.read_sum_file(builder, os.path.join(branch, 'baseline'))

    # Parse some text as a .sum file and return the resulting
    # dictionary.
    def read_sum_text(self, text):
        cur_file = StringIO(text)
        cur_results = {}
        for line in cur_file.readlines():
            self.parse_sum_line(cur_results, line)
        return cur_results

    # Compute regressions between RESULTS and BASELINE.
    # BASELINE will be modified if any new PASSes are seen.
    # Returns a regression report, as a string.
    def compute_regressions(self, results, baseline):
        our_keys = results.keys()
        our_keys.sort()
        result = ''
        xfails = self.read_sum_file('', 'xfail')
        if xfails is None:
            xfails = {}
        for key in our_keys:
            # An XFAIL entry means we have an unreliable test.
            if key in xfails:
                continue
            # A transition to PASS means we should update the baseline.
            if results[key] == 'PASS':
                if key not in baseline or baseline[key] != 'PASS':
                    baseline[key] = 'PASS'
            # A regression is just a transition to FAIL.
            if results[key] != 'FAIL':
                continue
            if key not in baseline:
                result = result + 'new FAIL: ' + key + '\n'
            elif baseline[key] != 'FAIL':
                result = result + baseline[key] + ' -> FAIL: ' + key + '\n'
        return result
