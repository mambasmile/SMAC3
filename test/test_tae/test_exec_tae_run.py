'''
Created on Jan 31, 2017

copied from test_exec_tae_old and modified to test exceptions

@author: lindauer
@modified: marben
'''
import os
import sys
import unittest

import numpy as np

from smac.configspace import ConfigurationSpace
from smac.tae.execute_ta_run import ExecuteTARun, StatusType
from smac.tae.execute_ta_run import BudgetExhaustedException, TAEAbortException
from smac.tae.execute_ta_run import FirstRunCrashedException
from smac.scenario.scenario import Scenario
from smac.stats.stats import Stats

if sys.version_info[0] == 2:
    import mock
else:
    from unittest import mock


class TaeTest(unittest.TestCase):

    def setUp(self):
        self.current_dir = os.getcwd()
        base_dir = os.path.split(__file__)[0]
        base_dir = os.path.join(base_dir, '..', '..')
        os.chdir(base_dir)

    def tearDown(self):
        os.chdir(self.current_dir)

    def test_start_exhausted_budget(self):
        '''
            testing exhausted budget
        '''
        # Set time-limit negative in scenario-options to trigger exception
        scen = Scenario(scenario={'wallclock_limit': -1, 'cs': ConfigurationSpace()}, cmd_args=None)
        stats = Stats(scen)
        stats.start_timing()
        eta = ExecuteTARun(
                ta=lambda *args: None,  # Dummy-function
                stats=stats)

        self.assertRaises(
            BudgetExhaustedException, eta.start, config={}, instance=1)

    @mock.patch.object(ExecuteTARun, 'run')
    def test_start_tae_return_abort(self, test_run):
        '''
            testing abort
        '''
        # Patch run-function for custom-return
        test_run.return_value = StatusType.ABORT, 12345.0, 1.2345, {}

        scen = Scenario(scenario={'cs': ConfigurationSpace()}, cmd_args=None)
        stats = Stats(scen)
        stats.start_timing()
        eta = ExecuteTARun(ta=lambda *args: None, stats=stats)

        self.assertRaises(
            TAEAbortException, eta.start, config={}, instance=1)

    @mock.patch.object(ExecuteTARun, 'run')
    def test_start_crash_first_run(self, test_run):
        '''
            testing crash-on-first-run
        '''
        # Patch run-function for custom-return
        test_run.return_value = StatusType.CRASHED, 12345.0, 1.2345, {}

        scen = Scenario(scenario={'cs': ConfigurationSpace()}, cmd_args=None)
        stats = Stats(scen)
        stats.start_timing()
        eta = ExecuteTARun(ta=lambda *args: None, stats=stats)

        self.assertRaises(
            FirstRunCrashedException, eta.start, config={}, instance=1)

    @mock.patch.object(ExecuteTARun, 'run')
    def test_start_tae_return_nan_inf(self, test_run):
        '''
            test nan-handling and inf-handling
        '''
        def get_tae(obj):
            """ Create ExecuteTARun-object for testing. """
            scen = Scenario(scenario={'cs': ConfigurationSpace(), 'run_obj': obj,
                'abort_on_first_run_crash': '0', 'cutoff_time': '10'}, cmd_args=None)
            stats = Stats(scen)
            stats.start_timing()
            eta = ExecuteTARun(ta=lambda *args: None, stats=stats, run_obj=obj)
            # Add first run to not trigger FirstRunCrashedException
            test_run.return_value = StatusType.SUCCESS, 1, 1, {}
            eta.start(config={}, instance=1)
            return eta

        # TEST NAN
        eta = get_tae('runtime')
        # Patch run-function for custom-return (obj = runtime, cost = nan)
        test_run.return_value = StatusType.SUCCESS, np.nan, 1, {}
        self.assertEqual(eta.start(config={}, cutoff=10, instance=1)[0], StatusType.SUCCESS)
        #                                      (obj = runtime, runtime = nan)
        test_run.return_value = StatusType.SUCCESS, 1, np.nan, {}
        self.assertEqual(eta.start(config={}, cutoff=10, instance=1)[0], StatusType.CRASHED)

        eta = get_tae('quality')
        # Patch run-function for custom-return (obj = quality, cost = nan)
        test_run.return_value = StatusType.SUCCESS, np.nan, 1, {}
        self.assertEqual(eta.start(config={}, instance=1)[0], StatusType.CRASHED)
        #                                      (obj = quality, runtime = nan)
        test_run.return_value = StatusType.SUCCESS, 1, np.nan, {}
        self.assertEqual(eta.start(config={}, instance=1)[0], StatusType.SUCCESS)

        # TEST INF
        eta = get_tae('runtime')
        # Patch run-function for custom-return (obj = runtime, cost = inf)
        test_run.return_value = StatusType.SUCCESS, np.inf, 1, {}
        self.assertEqual(eta.start(config={}, cutoff=10, instance=1)[0], StatusType.SUCCESS)
        #                                      (obj = runtime, runtime = inf)
        test_run.return_value = StatusType.SUCCESS, 1, np.inf, {}
        self.assertEqual(eta.start(config={}, cutoff=10, instance=1)[0], StatusType.CRASHED)

        eta = get_tae('quality')
        # Patch run-function for custom-return (obj = quality, cost = inf)
        test_run.return_value = StatusType.SUCCESS, np.inf, 1, {}
        self.assertEqual(eta.start(config={}, instance=1)[0], StatusType.CRASHED)
        #                                      (obj = quality, runtime = inf)
        test_run.return_value = StatusType.SUCCESS, 1, np.inf, {}
        self.assertEqual(eta.start(config={}, instance=1)[0], StatusType.SUCCESS)


if __name__ == "__main__":
    unittest.main()
