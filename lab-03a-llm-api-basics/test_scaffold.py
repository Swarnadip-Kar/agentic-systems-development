import unittest
from unittest.mock import patch, MagicMock
from scaffold import (
    assigned_trap_ticket_id,
    extract_category,
    classify_ticket_safely,
    suggest_next_action,
)
import os

class TestScaffold(unittest.TestCase):

    def test_assigned_trap_ticket_id(self):
        with patch.dict(os.environ, {"USER": "testuser"}):
            self.assertIn(assigned_trap_ticket_id(), [7, 8])

    def test_extract_category(self):
        response_mock = MagicMock()
        response_mock.choices = [
            {"message": {"content": "This is a billing issue"}}
        ]
        self.assertEqual(extract_category(response_mock), "billing")

        response_mock.choices = [
            {"message": {"content": "technical problem"}}
        ]
        self.assertEqual(extract_category(response_mock), "technical")

        response_mock.choices = [
            {"message": {"content": "unknown category"}}
        ]
        self.assertIsNone(extract_category(response_mock))

    def test_classify_ticket_safely_with_valid_response(self):
        client_mock = MagicMock()
        client_mock.chat.completions.create.return_value = MagicMock(choices=[
            {"message": {"content": "billing"}}
        ])
        self.assertEqual(classify_ticket_safely(client_mock, "This is a billing issue"), "billing")

    def test_classify_ticket_safely_with_empty_choices(self):
        client_mock = MagicMock()
        client_mock.chat.completions.create.return_value = MagicMock(choices=[])
        self.assertIsNone(classify_ticket_safely(client_mock, "This is a billing issue"))

    def test_classify_ticket_safely_with_empty_input(self):
        client_mock = MagicMock()
        self.assertIsNone(classify_ticket_safely(client_mock, ""))

    def test_suggest_next_action_with_valid_response(self):
        client_mock = MagicMock()
        client_mock.chat.completions.create.return_value = MagicMock(choices=[
            {"message": {"content": "escalate to billing team"}}
        ])
        self.assertEqual(suggest_next_action(client_mock, "This is a billing issue"), "escalate to billing team")

    def test_suggest_next_action_with_empty_choices(self):
        client_mock = MagicMock()
        client_mock.chat.completions.create.return_value = MagicMock(choices=[])
        self.assertIsNone(suggest_next_action(client_mock, "This is a billing issue"))

    def test_suggest_next_action_with_empty_input(self):
        client_mock = MagicMock()
        self.assertIsNone(suggest_next_action(client_mock, ""))

if __name__ == "__main__":
    unittest.main()
