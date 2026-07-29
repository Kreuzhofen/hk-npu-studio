from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path

from controllers.model_repository import ModelRepository
from engine.model_loader_service import ModelLoadState, ModelLoaderService


class FakeBackend:
    def __init__(self, *, fail_initialize: bool = False) -> None:
        self.fail_initialize = fail_initialize
        self.initialize_calls = 0
        self.shutdown_calls = 0

    def get_backend_name(self) -> str:
        return "Test Backend"

    def get_supported_models(self) -> list[str]:
        return []

    def initialize(self) -> None:
        self.initialize_calls += 1
        if self.fail_initialize:
            raise RuntimeError("initialization failed")

    def shutdown(self) -> None:
        self.shutdown_calls += 1


class FakeBackendManager:
    def __init__(self, backend: FakeBackend) -> None:
        self.backend = backend

    def get_best_backend(self, model):
        return self.backend


def metadata(model_id: str, path: Path) -> dict:
    return {
        "id": model_id,
        "display_name": model_id,
        "author": "Test",
        "version": "1.0.0",
        "license": "Test",
        "description": "Lifecycle test",
        "category": "Image",
        "backend": "CPU",
        "recommended_backend": "CPU (Stub)",
        "minimum_ram_gb": 1,
        "recommended_ram_gb": 2,
        "supports": ["txt2img"],
        "installed": True,
        "downloaded": True,
        "path": str(path),
        "status": "Ready",
        "capabilities": {"txt2img": True},
    }


class ModelLoaderLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.models = self.root / "definitions"
        self.models.mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def add_model(self, model_id: str) -> None:
        package = self.root / model_id
        package.mkdir()
        (package / "weights.onnx").write_bytes(b"model")
        (self.models / f"{model_id}.json").write_text(
            json.dumps(metadata(model_id, package)), encoding="utf-8"
        )

    def loader(self) -> ModelLoaderService:
        return ModelLoaderService(ModelRepository(str(self.models)))

    def test_duplicate_load_reuses_runtime_and_reference_counts(self):
        self.add_model("demo")
        loader = self.loader()
        backend = FakeBackend()
        manager = FakeBackendManager(backend)

        first = loader.load_model("demo", manager)
        second = loader.load_model("demo", manager)

        self.assertTrue(first.success)
        self.assertTrue(second.reused)
        self.assertIs(first.loaded_model, second.loaded_model)
        self.assertEqual(backend.initialize_calls, 1)
        self.assertTrue(loader.unload_model("demo"))
        self.assertEqual(backend.shutdown_calls, 0)
        self.assertTrue(loader.unload_model("demo"))
        self.assertEqual(backend.shutdown_calls, 1)
        self.assertEqual(loader.state, ModelLoadState.UNLOADED)

    def test_model_package_tree_is_scanned_only_once_per_load(self):
        self.add_model("demo")
        loader = self.loader()
        backend = FakeBackend()
        original_get_files = loader.get_model_files
        scan_count = 0

        def counted_get_files(model_id):
            nonlocal scan_count
            scan_count += 1
            return original_get_files(model_id)

        loader.get_model_files = counted_get_files

        result = loader.load_model("demo", FakeBackendManager(backend))

        self.assertTrue(result.success)
        self.assertEqual(scan_count, 1)
        loader.unload_model("demo")

    def test_parallel_load_is_initialized_only_once(self):
        self.add_model("demo")
        loader = self.loader()
        backend = FakeBackend()
        manager = FakeBackendManager(backend)
        barrier = threading.Barrier(3)
        results = []

        def load() -> None:
            barrier.wait()
            results.append(loader.load_model("demo", manager))

        threads = [threading.Thread(target=load) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(timeout=2)

        self.assertEqual(len(results), 2)
        self.assertTrue(all(result.success for result in results))
        self.assertEqual(backend.initialize_calls, 1)
        self.assertEqual(sum(result.reused for result in results), 1)
        loader.unload_model("demo")
        loader.unload_model("demo")

    def test_initialization_failure_releases_backend_and_resets_runtime(self):
        self.add_model("demo")
        loader = self.loader()
        backend = FakeBackend(fail_initialize=True)

        result = loader.load_model("demo", FakeBackendManager(backend))

        self.assertFalse(result.success)
        self.assertEqual(result.state, ModelLoadState.FAILED)
        self.assertEqual(backend.initialize_calls, 1)
        self.assertEqual(backend.shutdown_calls, 1)
        self.assertIsNone(loader.loaded_model_id)
        self.assertTrue(loader.unload_model())
        self.assertEqual(loader.state, ModelLoadState.UNLOADED)

    def test_registry_rejects_invalid_installation_before_backend_init(self):
        package = self.root / "missing"
        (self.models / "broken.json").write_text(
            json.dumps(metadata("broken", package)), encoding="utf-8"
        )
        loader = self.loader()
        backend = FakeBackend()

        result = loader.load_model("broken", FakeBackendManager(backend))

        self.assertFalse(result.success)
        self.assertIn("invalid", result.message.lower())
        self.assertEqual(backend.initialize_calls, 0)

    def test_switch_releases_old_backend_before_loading_new_model(self):
        self.add_model("first")
        self.add_model("second")
        loader = self.loader()
        first_backend = FakeBackend()
        second_backend = FakeBackend()

        self.assertTrue(
            loader.load_model("first", FakeBackendManager(first_backend)).success
        )
        switched = loader.switch_model(
            "second", FakeBackendManager(second_backend)
        )

        self.assertTrue(switched.success)
        self.assertEqual(first_backend.shutdown_calls, 1)
        self.assertEqual(second_backend.initialize_calls, 1)
        self.assertEqual(loader.loaded_model_id, "second")
        loader.unload_model("second")

    def test_model_session_releases_resources_after_exception(self):
        self.add_model("demo")
        loader = self.loader()
        backend = FakeBackend()

        with self.assertRaisesRegex(RuntimeError, "job failed"):
            with loader.model_session("demo", FakeBackendManager(backend)):
                raise RuntimeError("job failed")

        self.assertEqual(backend.shutdown_calls, 1)
        self.assertEqual(loader.state, ModelLoadState.UNLOADED)


if __name__ == "__main__":
    unittest.main()
