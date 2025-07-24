"""Unit tests for CI Hardware Detector."""

import json
import os
import unittest
from unittest.mock import Mock, patch

import pytest

# Import the module under test
try:
    from ci_hardware_detector import CIHardwareDetector, HardwareCapabilities
except ImportError:
    # If import fails, skip this test module
    pytest.skip("ci_hardware_detector module not found", allow_module_level=True)


class TestHardwareCapabilities(unittest.TestCase):
    """Test HardwareCapabilities dataclass."""

    def test_capabilities_creation(self):
        """Test creating hardware capabilities."""
        caps = HardwareCapabilities(
            cpu_count=8,
            memory_gb=16.0,
            gpu_available=True,
            gpu_count=2,
            gpu_models=["NVIDIA RTX 3080", "NVIDIA RTX 3080"],
            gpu_memory_gb=[10.0, 10.0],
            cuda_available=True,
            cuda_version="11.4",
            opencl_available=True,
            rocm_available=False,
            metal_available=False,
        )

        self.assertEqual(caps.cpu_count, 8)
        self.assertEqual(caps.memory_gb, 16.0)
        self.assertTrue(caps.gpu_available)
        self.assertEqual(caps.gpu_count, 2)
        self.assertEqual(len(caps.gpu_models), 2)

    def test_capabilities_to_dict(self):
        """Test converting capabilities to dictionary."""
        caps = HardwareCapabilities()
        caps_dict = caps.to_dict()

        self.assertIn("cpu_count", caps_dict)
        self.assertIn("gpu_available", caps_dict)
        self.assertIn("platform", caps_dict)
        self.assertIsInstance(caps_dict["gpu_models"], list)


class TestCIHardwareDetector(unittest.TestCase):
    """Test CI Hardware Detector."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = CIHardwareDetector()

    @patch("ci_hardware_detector.psutil.cpu_count")
    def test_detect_cpu(self, mock_cpu_count):
        """Test CPU detection."""
        mock_cpu_count.return_value = 16

        caps = HardwareCapabilities()
        self.detector._detect_cpu(caps)

        self.assertEqual(caps.cpu_count, 16)

    @patch("ci_hardware_detector.psutil.virtual_memory")
    def test_detect_memory(self, mock_vm):
        """Test memory detection."""
        mock_vm.return_value = Mock(total=17179869184)  # 16 GB in bytes

        caps = HardwareCapabilities()
        self.detector._detect_memory(caps)

        self.assertAlmostEqual(caps.memory_gb, 16.0, places=1)

    @patch("ci_hardware_detector.subprocess.run")
    def test_detect_nvidia_gpu_success(self, mock_run):
        """Test successful NVIDIA GPU detection."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="""
GPU 0: NVIDIA GeForce RTX 3080 (UUID: GPU-12345)
GPU 1: NVIDIA GeForce RTX 3090 (UUID: GPU-67890)
""",
        )

        caps = HardwareCapabilities()
        self.detector._detect_nvidia_gpu(caps)

        self.assertTrue(caps.gpu_available)
        self.assertEqual(caps.gpu_count, 2)
        self.assertIn("NVIDIA GeForce RTX 3080", caps.gpu_models)
        self.assertIn("NVIDIA GeForce RTX 3090", caps.gpu_models)

    @patch("ci_hardware_detector.subprocess.run")
    def test_detect_nvidia_gpu_not_found(self, mock_run):
        """Test NVIDIA GPU detection when nvidia-smi not found."""
        mock_run.side_effect = FileNotFoundError()

        caps = HardwareCapabilities()
        self.detector._detect_nvidia_gpu(caps)

        self.assertFalse(caps.gpu_available)
        self.assertEqual(caps.gpu_count, 0)

    @patch("ci_hardware_detector.subprocess.run")
    def test_detect_cuda_available(self, mock_run):
        """Test CUDA detection."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=(
                "nvcc: NVIDIA (R) Cuda compiler driver\n"
                "Cuda compilation tools, release 11.4, V11.4.152\n"
            ),
        )

        caps = HardwareCapabilities()
        self.detector._detect_cuda(caps)

        self.assertTrue(caps.cuda_available)
        self.assertEqual(caps.cuda_version, "11.4")

    @patch("ci_hardware_detector.subprocess.run")
    def test_detect_cuda_not_available(self, mock_run):
        """Test CUDA detection when not available."""
        mock_run.side_effect = FileNotFoundError()

        caps = HardwareCapabilities()
        self.detector._detect_cuda(caps)

        self.assertFalse(caps.cuda_available)
        self.assertIsNone(caps.cuda_version)

    @patch("ci_hardware_detector.subprocess.run")
    def test_detect_amd_gpu_success(self, mock_run):
        """Test AMD GPU detection."""
        # First call for rocm-smi
        mock_run.return_value = Mock(
            returncode=0,
            stdout="""
GPU[0] : AMD Radeon RX 6800 XT
GPU[1] : AMD Radeon RX 6900 XT
""",
        )

        caps = HardwareCapabilities()
        self.detector._detect_amd_gpu(caps)

        self.assertTrue(caps.gpu_available)
        self.assertEqual(caps.gpu_count, 2)
        self.assertIn("AMD Radeon RX 6800 XT", caps.gpu_models)

    @patch("ci_hardware_detector.subprocess.run")
    def test_detect_opencl(self, mock_run):
        """Test OpenCL detection."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Number of platforms: 1\n",
        )

        caps = HardwareCapabilities()
        self.detector._detect_opencl(caps)

        self.assertTrue(caps.opencl_available)

    @patch("ci_hardware_detector.platform.system")
    @patch("ci_hardware_detector.subprocess.run")
    def test_detect_metal_on_macos(self, mock_run, mock_platform):
        """Test Metal detection on macOS."""
        mock_platform.return_value = "Darwin"
        mock_run.return_value = Mock(returncode=0, stdout="Metal device found")

        caps = HardwareCapabilities()
        self.detector._detect_metal(caps)

        self.assertTrue(caps.metal_available)

    @patch("ci_hardware_detector.platform.system")
    def test_detect_metal_on_linux(self, mock_platform):
        """Test Metal detection on non-macOS."""
        mock_platform.return_value = "Linux"

        caps = HardwareCapabilities()
        self.detector._detect_metal(caps)

        self.assertFalse(caps.metal_available)

    def test_detect_all(self):
        """Test full hardware detection."""
        with patch.multiple(
            self.detector,
            _detect_cpu=Mock(),
            _detect_memory=Mock(),
            _detect_nvidia_gpu=Mock(),
            _detect_amd_gpu=Mock(),
            _detect_intel_gpu=Mock(),
            _detect_cuda=Mock(),
            _detect_opencl=Mock(),
            _detect_rocm=Mock(),
            _detect_metal=Mock(),
        ):
            caps = self.detector.detect()

            # All detection methods should be called
            self.detector._detect_cpu.assert_called_once()
            self.detector._detect_memory.assert_called_once()
            self.detector._detect_nvidia_gpu.assert_called_once()
            self.detector._detect_amd_gpu.assert_called_once()

            self.assertIsInstance(caps, HardwareCapabilities)

    def test_is_ci_environment(self):
        """Test CI environment detection."""
        # Test with CI variable
        with patch.dict(os.environ, {"CI": "true"}):
            self.assertTrue(self.detector.is_ci_environment())

        # Test with GITHUB_ACTIONS
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            self.assertTrue(self.detector.is_ci_environment())

        # Test with no CI variables
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(self.detector.is_ci_environment())

    def test_filter_capabilities_for_ci(self):
        """Test filtering capabilities for CI environment."""
        caps = HardwareCapabilities(
            cpu_count=32,
            memory_gb=128.0,
            gpu_available=True,
            gpu_count=4,
        )

        with patch.object(self.detector, "is_ci_environment", return_value=True):
            filtered = self.detector.filter_capabilities_for_ci(caps)

            # Should limit resources in CI
            self.assertLessEqual(filtered.cpu_count, 4)
            self.assertLessEqual(filtered.memory_gb, 16.0)

    def test_save_json_output(self):
        """Test saving capabilities to JSON file."""
        import tempfile

        caps = HardwareCapabilities(
            cpu_count=8,
            memory_gb=16.0,
            gpu_available=True,
            gpu_count=1,
            gpu_models=["Test GPU"],
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            self.detector.save_to_file(caps, f.name)

            # Read back and verify
            with open(f.name, "r") as rf:
                data = json.load(rf)

            self.assertEqual(data["cpu_count"], 8)
            self.assertEqual(data["gpu_count"], 1)
            self.assertIn("Test GPU", data["gpu_models"])

            os.unlink(f.name)

    @patch("ci_hardware_detector.subprocess.run")
    def test_command_timeout(self, mock_run):
        """Test command timeout handling."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)

        caps = HardwareCapabilities()
        self.detector._detect_nvidia_gpu(caps)

        # Should handle timeout gracefully
        self.assertFalse(caps.gpu_available)

    def test_main_detect_command(self):
        """Test main function with detect command."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            test_args = ["ci-hardware-detector.py", "detect", "--output", f.name]

            with patch("sys.argv", test_args):
                with patch.object(self.detector, "detect") as mock_detect:
                    mock_detect.return_value = HardwareCapabilities(cpu_count=4)

                    # Import and run main
                    from ci_hardware_detector import main

                    with self.assertRaises(SystemExit) as cm:
                        main()

                    self.assertEqual(cm.exception.code, 0)

            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
