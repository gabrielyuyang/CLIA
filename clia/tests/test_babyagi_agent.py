"""
Unit tests for BabyAGI agent components.
"""

import unittest

from clia.agents.babyagi_agent import TaskList, _normalize_task


class TestTaskList(unittest.TestCase):
    def test_add_task_deduplicates(self):
        task_list = TaskList()
        self.assertTrue(task_list.add_task("Draft proposal", priority=0.6))
        self.assertFalse(task_list.add_task("  draft   proposal ", priority=0.9))
        self.assertEqual(len(task_list.tasks), 1)

    def test_pop_next_orders_by_priority_then_id(self):
        task_list = TaskList()
        task_list.add_task("low", priority=0.1)
        task_list.add_task("high", priority=0.9)
        next_task = task_list.pop_next()
        self.assertIsNotNone(next_task)
        self.assertEqual(next_task.description, "high")

        task_list.add_task("first", priority=0.5)
        task_list.add_task("second", priority=0.5)
        next_task = task_list.pop_next()
        self.assertIsNotNone(next_task)
        self.assertEqual(next_task.description, "first")

    def test_normalize_task(self):
        self.assertEqual(_normalize_task("  Hello   World "), "hello world")


if __name__ == "__main__":
    unittest.main()
