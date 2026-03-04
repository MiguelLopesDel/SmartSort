import unittest
from unittest.mock import MagicMock

from watchdog.events import FileCreatedEvent

from smartsort.__main__ import SmartSortHandler


class TestWatchdog(unittest.TestCase):
    def test_handler_triggers_processor(self):
        mock_processor = MagicMock()
        handler = SmartSortHandler(mock_processor)

        event = FileCreatedEvent("/tmp/test.txt")
        handler.on_created(event)

        mock_processor.process_file.assert_called_once_with("/tmp/test.txt")

    def test_handler_triggers_processor_on_dir(self):
        mock_processor = MagicMock()
        handler = SmartSortHandler(mock_processor)

        event = MagicMock(spec=FileCreatedEvent)
        event.is_directory = True
        event.src_path = "/tmp/nova_pasta"

        handler.on_created(event)
        mock_processor.process_file.assert_called_once_with("/tmp/nova_pasta")


if __name__ == "__main__":
    unittest.main()
