import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import storage


class StorageConfigTests(unittest.TestCase):
    def test_reads_project_and_bucket_from_env_file_when_environment_is_blank(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text(
                "GCS_BUCKET_NAME=test-bucket\nGOOGLE_CLOUD_PROJECT=test-project\n",
                encoding="utf-8",
            )

            with (
                patch.object(storage, "ENV_FILE", env_file),
                patch.dict(
                    os.environ,
                    {"GCS_BUCKET_NAME": "", "GOOGLE_CLOUD_PROJECT": ""},
                ),
                patch("src.storage.Client") as client,
            ):
                storage._get_gcs_bucket()

            client.assert_called_once_with(project="test-project")
            client.return_value.bucket.assert_called_once_with("test-bucket")


if __name__ == "__main__":
    unittest.main()
