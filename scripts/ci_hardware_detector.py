#!/usr/bin/env python3
"""
CI Hardware Detector - GPU and specialized hardware detection for CI optimization.

This module detects available hardware capabilities and routes CI jobs to
appropriate runners based on hardware requirements.
"""

import json
import logging
import platform
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import psutil


@dataclass
class GPUInfo:
    """Information about a GPU device."""

    id: int
    name: str
    memory_mb: int
    compute_capability: Optional[str] = None
    driver_version: Optional[str] = None
    cuda_version: Optional[str] = None
    available: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SystemCapabilities:
    """System hardware capabilities."""

    cpu_cores: int
    memory_mb: int
    disk_space_gb: int
    gpu_devices: List[GPUInfo]
    has_docker: bool
    has_cuda: bool
    has_opencl: bool
    architecture: str
    operating_system: str
    capabilities: Set[str]

    def __post_init__(self):
        # Convert set to list for JSON serialization
        if isinstance(self.capabilities, set):
            object.__setattr__(self, "capabilities", list(self.capabilities))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["gpu_devices"] = [gpu.to_dict() for gpu in self.gpu_devices]
        return data


class CIHardwareDetector:
    """
    Detects hardware capabilities for CI job routing and optimization.

    Features:
    - GPU detection (NVIDIA, AMD, Intel)
    - CUDA/OpenCL capability detection
    - System resource assessment
    - Docker and container support
    - Specialized hardware identification
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        # Whitelist of allowed commands for security
        self.allowed_commands = {"nvidia-smi", "rocm-smi", "lspci", "docker", "nvcc", "clinfo"}

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def _run_command(self, command: List[str], capture_output: bool = True) -> Optional[str]:
        """Run a command and return output with security validation."""
        # Security check: validate command against whitelist
        if not command:
            return None

        cmd_name = command[0]
        if cmd_name not in self.allowed_commands:
            self.logger.warning(f"Command '{cmd_name}' not in whitelist, skipping for security")
            return None

        try:
            # Use shell=False (default) for security
            result = subprocess.run(
                command, capture_output=capture_output, text=True, timeout=30, shell=False
            )
            return result.stdout if result.returncode == 0 else None
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def detect_nvidia_gpus(self) -> List[GPUInfo]:
        """Detect NVIDIA GPUs using nvidia-smi."""
        gpus: List[GPUInfo] = []

        try:
            # Check if nvidia-smi is available
            if not shutil.which("nvidia-smi"):
                return gpus

            # Get GPU information in JSON format
            output = self._run_command(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,memory.total,driver_version",
                    "--format=csv,noheader,nounits",
                ]
            )

            if not output:
                return gpus

            # Parse nvidia-smi output
            for line in output.strip().split("\n"):
                if line.strip():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 4:
                        try:
                            gpu_id = int(parts[0])
                            name = parts[1]
                            memory_mb = int(parts[2])
                            driver_version = parts[3]

                            # Get CUDA version if available
                            cuda_version = None
                            cuda_output = self._run_command(
                                [
                                    "nvidia-smi",
                                    "--query-gpu=cuda_version",
                                    "--format=csv,noheader,nounits",
                                ]
                            )
                            if cuda_output:
                                cuda_version = (
                                    cuda_output.strip().split("\n")[gpu_id]
                                    if len(cuda_output.strip().split("\n")) > gpu_id
                                    else None
                                )

                            gpu = GPUInfo(
                                id=gpu_id,
                                name=name,
                                memory_mb=memory_mb,
                                driver_version=driver_version,
                                cuda_version=cuda_version,
                            )
                            gpus.append(gpu)

                        except (ValueError, IndexError) as e:
                            self.logger.warning(f"Failed to parse GPU info: {e}")

            self.logger.info(f"Detected {len(gpus)} NVIDIA GPU(s)")

        except Exception as e:
            self.logger.warning(f"Failed to detect NVIDIA GPUs: {e}")

        return gpus

    def detect_amd_gpus(self) -> List[GPUInfo]:
        """Detect AMD GPUs using rocm-smi or similar tools."""
        gpus: List[GPUInfo] = []

        try:
            # Check for ROCm tools
            if shutil.which("rocm-smi"):
                output = self._run_command(["rocm-smi", "--showmeminfo", "vram"])
                if output:
                    # Parse ROCm output (simplified)
                    lines = output.strip().split("\n")
                    gpu_count = 0
                    for line in lines:
                        if "GPU" in line and "vram" in line.lower():
                            gpu = GPUInfo(
                                id=gpu_count,
                                name=f"AMD GPU {gpu_count}",
                                memory_mb=0,  # Would need more parsing
                            )
                            gpus.append(gpu)
                            gpu_count += 1

            # Fallback: check for AMD devices in lspci
            if not gpus:
                lspci_output = self._run_command(["lspci", "-v"])
                if lspci_output:
                    gpu_count = 0
                    for line in lspci_output.split("\n"):
                        if "VGA" in line and ("AMD" in line or "ATI" in line):
                            gpu = GPUInfo(
                                id=gpu_count,
                                name=(
                                    line.split(":")[-1].strip()
                                    if ":" in line
                                    else f"AMD GPU {gpu_count}"
                                ),
                                memory_mb=0,
                            )
                            gpus.append(gpu)
                            gpu_count += 1

            if gpus:
                self.logger.info(f"Detected {len(gpus)} AMD GPU(s)")

        except Exception as e:
            self.logger.warning(f"Failed to detect AMD GPUs: {e}")

        return gpus

    def detect_intel_gpus(self) -> List[GPUInfo]:
        """Detect Intel GPUs."""
        gpus: List[GPUInfo] = []

        try:
            # Check lspci for Intel graphics
            lspci_output = self._run_command(["lspci", "-v"])
            if lspci_output:
                gpu_count = 0
                for line in lspci_output.split("\n"):
                    if ("VGA" in line or "Display" in line) and "Intel" in line:
                        gpu = GPUInfo(
                            id=gpu_count,
                            name=(
                                line.split(":")[-1].strip()
                                if ":" in line
                                else f"Intel GPU {gpu_count}"
                            ),
                            memory_mb=0,  # Intel integrated graphics share system memory
                        )
                        gpus.append(gpu)
                        gpu_count += 1

            if gpus:
                self.logger.info(f"Detected {len(gpus)} Intel GPU(s)")

        except Exception as e:
            self.logger.warning(f"Failed to detect Intel GPUs: {e}")

        return gpus

    def detect_cuda_support(self) -> bool:
        """Check if CUDA is available."""
        try:
            # Check for CUDA runtime
            cuda_paths = ["/usr/local/cuda/bin/nvcc", "/opt/cuda/bin/nvcc"]

            for cuda_path in cuda_paths:
                if Path(cuda_path).exists():
                    return True

            # Check if nvcc is in PATH
            if shutil.which("nvcc"):
                return True

            # Check for CUDA libraries
            cuda_lib_paths = [
                "/usr/local/cuda/lib64",
                "/usr/lib/x86_64-linux-gnu",
                "/opt/cuda/lib64",
            ]

            for lib_path in cuda_lib_paths:
                cuda_lib = Path(lib_path) / "libcudart.so"
                if cuda_lib.exists():
                    return True

            return False

        except Exception as e:
            self.logger.warning(f"Failed to detect CUDA support: {e}")
            return False

    def detect_opencl_support(self) -> bool:
        """Check if OpenCL is available."""
        try:
            # Check for OpenCL headers and libraries
            opencl_paths = [
                "/usr/include/CL/cl.h",
                "/usr/local/include/CL/cl.h",
                "/opt/intel/opencl/include/CL/cl.h",
            ]

            for header_path in opencl_paths:
                if Path(header_path).exists():
                    return True

            # Check for OpenCL libraries
            opencl_lib_paths = [
                "/usr/lib/x86_64-linux-gnu/libOpenCL.so",
                "/usr/local/lib/libOpenCL.so",
                "/opt/intel/opencl/lib64/libOpenCL.so",
            ]

            for lib_path in opencl_lib_paths:
                if Path(lib_path).exists():
                    return True

            return False

        except Exception as e:
            self.logger.warning(f"Failed to detect OpenCL support: {e}")
            return False

    def detect_docker_support(self) -> bool:
        """Check if Docker is available and working."""
        try:
            if not shutil.which("docker"):
                return False

            # Test Docker connectivity
            output = self._run_command(["docker", "version", "--format", "json"])
            if output:
                docker_info = json.loads(output)
                return "Server" in docker_info

            return False

        except Exception as e:
            self.logger.warning(f"Failed to detect Docker support: {e}")
            return False

    def get_system_resources(self) -> Dict[str, Any]:
        """Get system resource information."""
        try:
            # CPU information
            cpu_count = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()

            # Memory information
            memory = psutil.virtual_memory()
            memory_mb = int(memory.total / (1024 * 1024))

            # Disk information
            disk = psutil.disk_usage("/")
            disk_space_gb = int(disk.total / (1024 * 1024 * 1024))

            # Network information
            network_info = psutil.net_if_stats()

            return {
                "cpu": {
                    "cores": cpu_count,
                    "frequency_mhz": int(cpu_freq.max) if cpu_freq else None,
                    "architecture": platform.machine(),
                },
                "memory": {
                    "total_mb": memory_mb,
                    "available_mb": int(memory.available / (1024 * 1024)),
                },
                "disk": {
                    "total_gb": disk_space_gb,
                    "free_gb": int(disk.free / (1024 * 1024 * 1024)),
                },
                "network": {"interfaces": len(network_info)},
            }

        except Exception as e:
            self.logger.error(f"Failed to get system resources: {e}")
            return {}

    def detect_specialized_capabilities(self) -> Set[str]:
        """Detect specialized hardware capabilities."""
        capabilities = set()

        # Basic capabilities
        capabilities.add("basic")

        # Architecture-specific capabilities
        arch = platform.machine().lower()
        if arch in ["x86_64", "amd64"]:
            capabilities.add("x86_64")
        elif arch in ["aarch64", "arm64"]:
            capabilities.add("arm64")

        # Operating system capabilities
        os_name = platform.system().lower()
        capabilities.add(os_name)

        # Container capabilities
        if self.detect_docker_support():
            capabilities.add("docker")
            capabilities.add("containers")

        # GPU capabilities
        nvidia_gpus = self.detect_nvidia_gpus()
        if nvidia_gpus:
            capabilities.add("gpu")
            capabilities.add("nvidia-gpu")
            if self.detect_cuda_support():
                capabilities.add("cuda")

        amd_gpus = self.detect_amd_gpus()
        if amd_gpus:
            capabilities.add("gpu")
            capabilities.add("amd-gpu")

        intel_gpus = self.detect_intel_gpus()
        if intel_gpus:
            capabilities.add("gpu")
            capabilities.add("intel-gpu")

        # Compute capabilities
        if self.detect_opencl_support():
            capabilities.add("opencl")

        # Check for high-performance features
        try:
            # Check for AVX support
            if "avx" in Path("/proc/cpuinfo").read_text().lower():
                capabilities.add("avx")
        except Exception:
            pass

        # Memory capabilities
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024 * 1024 * 1024)

        if memory_gb >= 16:
            capabilities.add("high-memory")
        if memory_gb >= 32:
            capabilities.add("very-high-memory")

        # Storage capabilities
        try:
            # Check for SSD (simplified heuristic)
            disk_io = psutil.disk_io_counters()
            if disk_io and disk_io.read_time > 0:
                # This is a very rough heuristic
                avg_read_time = (
                    disk_io.read_time / disk_io.read_count if disk_io.read_count > 0 else 0
                )
                if avg_read_time < 10:  # Arbitrary threshold
                    capabilities.add("ssd-storage")
        except Exception:
            pass

        return capabilities

    def detect_all_capabilities(self) -> SystemCapabilities:
        """Detect all system capabilities."""
        self.logger.info("Starting hardware detection...")

        # Detect GPUs
        all_gpus = []
        all_gpus.extend(self.detect_nvidia_gpus())
        all_gpus.extend(self.detect_amd_gpus())
        all_gpus.extend(self.detect_intel_gpus())

        # Get system resources
        resources = self.get_system_resources()

        # Detect capabilities
        capabilities = self.detect_specialized_capabilities()

        system_caps = SystemCapabilities(
            cpu_cores=resources.get("cpu", {}).get("cores", 1),
            memory_mb=resources.get("memory", {}).get("total_mb", 1024),
            disk_space_gb=resources.get("disk", {}).get("total_gb", 10),
            gpu_devices=all_gpus,
            has_docker=self.detect_docker_support(),
            has_cuda=self.detect_cuda_support(),
            has_opencl=self.detect_opencl_support(),
            architecture=platform.machine(),
            operating_system=platform.system(),
            capabilities=capabilities,
        )

        self.logger.info(
            f"Detection complete. Found {len(all_gpus)} GPU(s) and {len(capabilities)} capabilities"
        )
        return system_caps

    def can_run_job(
        self, job_requirements: List[str], system_caps: Optional[SystemCapabilities] = None
    ) -> Tuple[bool, List[str]]:
        """
        Check if system can run a job with given requirements.

        Returns:
            Tuple of (can_run, missing_requirements)
        """
        if system_caps is None:
            system_caps = self.detect_all_capabilities()

        missing = []
        system_capabilities = set(system_caps.capabilities)

        for requirement in job_requirements:
            if requirement not in system_capabilities:
                missing.append(requirement)

        can_run = len(missing) == 0
        return can_run, missing

    def get_optimal_runner_config(
        self, job_requirements: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get optimal runner configuration for given job requirements."""
        system_caps = self.detect_all_capabilities()

        config = {
            "runner_id": f"runner-{platform.node()}",
            "capabilities": system_caps.capabilities,
            "resources": {
                "cpu_cores": system_caps.cpu_cores,
                "memory_mb": system_caps.memory_mb,
                "disk_space_gb": system_caps.disk_space_gb,
                "gpu_count": len(system_caps.gpu_devices),
            },
            "specialized": {
                "has_docker": system_caps.has_docker,
                "has_cuda": system_caps.has_cuda,
                "has_opencl": system_caps.has_opencl,
            },
        }

        # Add job-specific optimizations
        if job_requirements:
            can_run, missing = self.can_run_job(job_requirements, system_caps)
            config["job_compatibility"] = {
                "can_run": can_run,
                "missing_requirements": missing,
                "recommended": can_run and len(missing) == 0,
            }

        return config


def main():
    """CLI interface for hardware detector."""
    import argparse

    parser = argparse.ArgumentParser(description="CI Hardware Detector")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", type=Path, help="Output file for capabilities")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Detect command
    subparsers.add_parser("detect", help="Detect all hardware capabilities")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check if system can run job")
    check_parser.add_argument("--requirements", nargs="+", help="Job requirements to check")

    # GPU command
    subparsers.add_parser("gpu", help="Detect GPU devices only")

    # Config command
    config_parser = subparsers.add_parser("config", help="Generate optimal runner config")
    config_parser.add_argument("--job-requirements", nargs="*", help="Job requirements")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    detector = CIHardwareDetector()

    if args.command == "detect":
        capabilities = detector.detect_all_capabilities()
        result = capabilities.to_dict()

        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Capabilities saved to {args.output}")
        else:
            print(json.dumps(result, indent=2))

    elif args.command == "check":
        if not args.requirements:
            print("Error: --requirements is required for check command")
            return

        can_run, missing = detector.can_run_job(args.requirements)

        result = {
            "can_run": can_run,
            "missing_requirements": missing,
            "checked_requirements": args.requirements,
        }

        print(json.dumps(result, indent=2))

    elif args.command == "gpu":
        nvidia_gpus = detector.detect_nvidia_gpus()
        amd_gpus = detector.detect_amd_gpus()
        intel_gpus = detector.detect_intel_gpus()

        result = {
            "nvidia_gpus": [gpu.to_dict() for gpu in nvidia_gpus],
            "amd_gpus": [gpu.to_dict() for gpu in amd_gpus],
            "intel_gpus": [gpu.to_dict() for gpu in intel_gpus],
            "total_gpus": len(nvidia_gpus) + len(amd_gpus) + len(intel_gpus),
            "has_cuda": detector.detect_cuda_support(),
            "has_opencl": detector.detect_opencl_support(),
        }

        print(json.dumps(result, indent=2))

    elif args.command == "config":
        config = detector.get_optimal_runner_config(args.job_requirements)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(config, f, indent=2)
            print(f"Runner config saved to {args.output}")
        else:
            print(json.dumps(config, indent=2))

    else:
        parser.print_help()
        exit(1)


if __name__ == "__main__":
    main()
