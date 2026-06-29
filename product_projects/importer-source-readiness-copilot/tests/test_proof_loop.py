from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_run_all_artifacts_module():
    path = ROOT / "scripts" / "run_all_artifacts.py"
    spec = importlib.util.spec_from_file_location("run_all_artifacts", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProductProofLoopTests(unittest.TestCase):
    def test_run_all_artifacts_generates_dependencies_before_country_source_engine(self) -> None:
        module = _load_run_all_artifacts_module()
        commands = [" ".join(command) for command in module.ARTIFACT_GENERATOR_COMMANDS]

        self.assertIn("scripts/run_product_operations.py", commands)
        self.assertIn("scripts/run_production_country_source_engine.py", commands)
        self.assertLess(
            commands.index("scripts/run_product_operations.py"),
            commands.index("scripts/run_production_country_source_engine.py"),
        )
        self.assertNotIn("-m unittest discover -s tests -p test_*.py", commands)
        self.assertNotIn("scripts/audit_external_package.py --root .", commands)

    def test_check_product_regenerates_artifacts_before_tests(self) -> None:
        text = (ROOT / "scripts" / "check_product.py").read_text(encoding="utf-8")

        self.assertLess(
            text.index('"scripts/run_all_artifacts.py"'),
            text.index('"-m", "unittest"'),
        )
        self.assertLess(
            text.index('"-m", "unittest"'),
            text.index('"scripts/audit_external_package.py"'),
        )


if __name__ == "__main__":
    unittest.main()
