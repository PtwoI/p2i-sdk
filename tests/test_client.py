import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from p2i_sdk import Client, P2IAPIError


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class ClientTests(unittest.TestCase):
    def test_model_and_operation_are_requested_at_expected_paths(self):
        with patch("p2i_sdk.client.urlopen", side_effect=lambda *_args, **_kwargs: Response(b'{"modules": []}')) as call:
            self.assertEqual(Client().model(), {"modules": []})
            self.assertEqual(call.call_args.args[0].full_url, "http://127.0.0.1:8000/api/model")
            Client().item("operations", "op/1")
            self.assertTrue(call.call_args.args[0].full_url.endswith("/api/operations/op%2F1"))

    def test_action_is_serialized_as_json(self):
        with patch("p2i_sdk.client.urlopen", return_value=Response(b'{"result": {"success": true}}')) as call:
            result = Client().command("preview", {"type": "set_parameter", "value": 0.2})
            self.assertTrue(result["result"]["success"])
            request = call.call_args.args[0]
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(json.loads(request.data)["value"], 0.2)

    def test_http_error_is_structured(self):
        error = HTTPError("http://127.0.0.1:8000/api/model", 409, "Conflict", None, io.BytesIO(b'{"detail":"no Harness"}'))
        with patch("p2i_sdk.client.urlopen", side_effect=error):
            with self.assertRaises(P2IAPIError) as failure:
                Client().model()
            self.assertEqual(failure.exception.status, 409)
            self.assertEqual(failure.exception.detail, {"detail": "no Harness"})

    def test_invalid_urls_and_commands(self):
        with self.assertRaises(ValueError):
            Client("file:///tmp/model")
        with self.assertRaises(ValueError):
            Client("http://127.0.0.1:8000/other")
        with self.assertRaises(ValueError):
            Client().command("run_arbitrary_code")


if __name__ == "__main__":
    unittest.main()
