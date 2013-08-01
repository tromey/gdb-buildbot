# GDB .sum-fetching command.

from buildbot.status.builder import SUCCESS, WARNINGS, FAILURE, EXCEPTION
from buildbot.steps.shell import ShellCommand
from sumfiles import DejaResults

class GdbCatSumfileCommand(ShellCommand):
    name = 'regressions'
    command = ['cat', 'gdb.sum']

    def __init__(self, **kwargs):
        ShellCommand.__init__(self, **kwargs)

    def evaluateCommand(self, cmd):
        rev = self.getProperty('got_revision')
        builder = self.getProperty('buildername')
        istry = self.getProperty('isTryBuilder')
        branch = self.getProperty('branch')
        if branch is None:
            branch = 'master'
        parser = DejaResults()
        cur_results = parser.read_sum_text(self.getLog('stdio').getText())
        if istry == 'no':
            baseline = parser.read_baseline (builder, branch)
        else:
            baseline = parser.read_sum_file(builder, rev)
        result = SUCCESS
        if baseline is not None:
            report = parser.compute_regressions(cur_results, baseline)
            if report is not '':
                self.addCompleteLog('regressions', report)
                result = FAILURE
        if istry == 'no':
            parser.write_sum_file(cur_results, builder, rev)
            # If there was no previous baseline, then this run
            # gets the honor.
            if baseline is None:
                baseline = cur_results
            parser.write_baseline(baseline, builder, branch)
        return result
