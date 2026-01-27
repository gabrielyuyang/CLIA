"""
Unit tests for the Tree-of-Thoughts agent.
"""

import unittest
from unittest.mock import patch, MagicMock
import json

from clia.agents.tot_agent import (
    Thought,
    _generate_thoughts,
    _evaluate_thought,
    _execute_thought_action,
    _search_tree,
    _synthesize_answer,
    tot_agent,
    tot_agent_simple
)


class TestThoughtClass(unittest.TestCase):
    """Test the Thought dataclass."""

    def test_thought_creation(self):
        """Test creating a Thought object."""
        thought = Thought(
            id="test_1",
            content="Test thought content",
            depth=0,
            parent_id=None,
            score=0.8
        )

        self.assertEqual(thought.id, "test_1")
        self.assertEqual(thought.content, "Test thought content")
        self.assertEqual(thought.depth, 0)
        self.assertIsNone(thought.parent_id)
        self.assertEqual(thought.score, 0.8)
        self.assertIsNone(thought.action)
        self.assertIsNone(thought.result)

    def test_thought_with_action_and_result(self):
        """Test creating a Thought with action and result."""
        action = {"tool": "read_file", "args": {"path": "test.txt"}}
        thought = Thought(
            id="test_2",
            content="Thought with action",
            depth=1,
            parent_id="test_1",
            score=0.9,
            action=action,
            result="File content"
        )

        self.assertEqual(thought.action, action)
        self.assertEqual(thought.result, "File content")

    def test_thought_to_dict(self):
        """Test converting Thought to dictionary."""
        thought = Thought(
            id="test_3",
            content="Test conversion",
            depth=2,
            parent_id="test_2",
            score=0.75
        )

        thought_dict = thought.to_dict()
        self.assertEqual(thought_dict["id"], "test_3")
        self.assertEqual(thought_dict["content"], "Test conversion")
        self.assertEqual(thought_dict["depth"], 2)
        self.assertEqual(thought_dict["parent_id"], "test_2")
        self.assertEqual(thought_dict["score"], 0.75)


class TestToTAgentFunctions(unittest.TestCase):
    """Test individual functions of the ToT agent."""

    def setUp(self):
        """Set up common test data."""
        self.question = "What is the capital of France?"
        self.command = "ask"
        self.api_params = {
            "api_key": "test_key",
            "base_url": "test_url",
            "max_retries": 1,
            "model": "test_model",
            "temperature": 0.7,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "max_tokens": 1000,
            "timeout": 10.0
        }

    @patch('clia.agents.tot_agent.llm.openai_completion')
    def test_generate_thoughts_success(self, mock_llm):
        """Test successful thought generation."""
        # Mock LLM response with JSON array
        mock_response = '''[
            {"thought": "Paris is the capital of France"},
            {"thought": "France's capital is Paris"},
            {"thought": "The capital city of France is Paris"}
        ]'''
        mock_llm.return_value = mock_response

        thoughts = _generate_thoughts(
            self.question, self.command, [], 0, 3, **self.api_params
        )

        self.assertEqual(len(thoughts), 3)
        self.assertTrue(all(isinstance(t, Thought) for t in thoughts))
        self.assertTrue(all(t.depth == 0 for t in thoughts))
        self.assertIn("Paris", thoughts[0].content)

    @patch('clia.agents.tot_agent.llm.openai_completion')
    def test_generate_thoughts_with_fallback(self, mock_llm):
        """Test thought generation fallback on error."""
        mock_llm.side_effect = Exception("LLM error")

        thoughts = _generate_thoughts(
            self.question, self.command, [], 0, 3, **self.api_params
        )

        self.assertEqual(len(thoughts), 3)
        self.assertTrue(all("Fallback approach" in t.content for t in thoughts))

    @patch('clia.agents.tot_agent.llm.openai_completion')
    def test_evaluate_thought_success(self, mock_llm):
        """Test successful thought evaluation."""
        # Mock LLM response with JSON score
        mock_response = '{"score": 0.85}'
        mock_llm.return_value = mock_response

        thought = Thought(
            id="eval_test",
            content="Test thought for evaluation",
            depth=0,
            parent_id=None,
            score=0.0
        )

        score = _evaluate_thought(
            thought, self.question, self.command, [], **self.api_params
        )

        self.assertEqual(score, 0.85)

    @patch('clia.agents.tot_agent.llm.openai_completion')
    def test_evaluate_thought_fallback(self, mock_llm):
        """Test thought evaluation fallback on error."""
        mock_llm.side_effect = Exception("LLM error")

        thought = Thought(
            id="eval_test",
            content="Test thought for evaluation",
            depth=0,
            parent_id=None,
            score=0.0
        )

        score = _evaluate_thought(
            thought, self.question, self.command, [], **self.api_params
        )

        self.assertEqual(score, 0.5)  # Default fallback score

    @patch('clia.agents.tot_agent.run_tool')
    def test_execute_thought_action_file_read(self, mock_run_tool):
        """Test executing thought action for file reading."""
        mock_run_tool.return_value = "File contents here"

        thought = Thought(
            id="action_test",
            content="We should read the file 'test.txt' to get more information",
            depth=1,
            parent_id="parent_1",
            score=0.8
        )

        result = _execute_thought_action(thought, **self.api_params)

        self.assertEqual(result, "File contents here")
        mock_run_tool.assert_called_once_with("read_file", path_str="test.txt", max_chars=1000)

    def test_execute_thought_action_no_action(self):
        """Test executing thought action when no action is suggested."""
        thought = Thought(
            id="no_action_test",
            content="This is just a thought with no actionable items",
            depth=1,
            parent_id="parent_1",
            score=0.6
        )

        result = _execute_thought_action(thought, **self.api_params)

        self.assertIsNone(result)

    @patch('clia.agents.tot_agent.llm.openai_completion')
    def test_synthesize_answer_success(self, mock_llm):
        """Test successful answer synthesis."""
        mock_llm.return_value = "The capital of France is Paris."

        final_thoughts = [
            Thought("final_1", "Paris is the capital", 2, "parent_1", 0.9, result="Confirmed"),
            Thought("final_2", "France's capital is Paris", 2, "parent_2", 0.85)
        ]

        all_thoughts = final_thoughts + [
            Thought("parent_1", "Initial thought about France", 1, None, 0.7),
            Thought("parent_2", "Another approach to the question", 1, None, 0.65)
        ]

        answer = _synthesize_answer(
            self.question, self.command, final_thoughts, all_thoughts, **self.api_params
        )

        self.assertEqual(answer, "The capital of France is Paris.")

    @patch('clia.agents.tot_agent.llm.openai_completion')
    def test_synthesize_answer_fallback(self, mock_llm):
        """Test answer synthesis fallback on error."""
        mock_llm.side_effect = Exception("LLM error")

        final_thoughts = [
            Thought("final_1", "Paris is the capital", 2, "parent_1", 0.9, result="Confirmed")
        ]

        answer = _synthesize_answer(
            self.question, self.command, final_thoughts, final_thoughts, **self.api_params
        )

        self.assertIn("Best reasoning path", answer)
        self.assertIn("Paris is the capital", answer)


class TestToTAgentIntegration(unittest.TestCase):
    """Test the integrated ToT agent functions."""

    def setUp(self):
        """Set up common test data."""
        self.question = "What is 2+2?"
        self.command = "ask"
        self.base_params = {
            "max_depth": 2,
            "branching_factor": 2,
            "beam_width": 2,
            "api_key": "test_key",
            "base_url": "test_url",
            "max_retries": 1,
            "model": "test_model",
            "temperature": 0.7,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "max_tokens": 1000,
            "timeout": 10.0
        }

    @patch('clia.agents.tot_agent._search_tree')
    @patch('clia.agents.tot_agent._synthesize_answer')
    def test_tot_agent_success(self, mock_synthesize, mock_search):
        """Test successful execution of tot_agent."""
        # Mock search tree to return some thoughts
        mock_thought = Thought("test_1", "2+2 equals 4", 1, None, 0.9)
        mock_search.return_value = ([mock_thought], [mock_thought])

        # Mock synthesis to return final answer
        mock_synthesize.return_value = "The answer is 4."

        result = tot_agent(self.question, self.command, **self.base_params)

        self.assertEqual(result, "The answer is 4.")
        mock_search.assert_called_once()
        mock_synthesize.assert_called_once()

    def test_tot_agent_simple_wrapper(self):
        """Test the simple wrapper function."""
        # Just test that it calls the main function with verbose=False
        with patch('clia.agents.tot_agent.tot_agent') as mock_tot_agent:
            mock_tot_agent.return_value = "Test answer"

            result = tot_agent_simple(self.question, self.command, **self.base_params)

            self.assertEqual(result, "Test answer")
            mock_tot_agent.assert_called_once_with(
                question=self.question,
                command=self.command,
                stream=False,  # Add the missing stream parameter
                verbose=False,
                **self.base_params
            )


if __name__ == '__main__':
    unittest.main()