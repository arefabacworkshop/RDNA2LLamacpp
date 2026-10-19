#!/usr/bin/env python3
"""
RDNA2LLamacpp - Automated Build & Update System
Compiles llama.cpp with AMD ROCm (TheRock) acceleration tailored for RDNA2 (gfx103X) GPUs.
Reads settings from build_config.ini, auto-detects toolchains, bundles dependencies, and verifies binaries.
"""

import argparse
import configparser
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

# FlashAttention vector quantization pairs (symmetric + hybrid)
FA_QUANTS = (
    "q4_0-q4_0;q4_1-q4_1;q5_0-q5_0;q5_1-q5_1;q8_0-q8_0;f16-f16;bf16-bf16;"
    "q8_0-q4_0;q8_0-q4_1;q8_0-q5_0;q8_0-q5_1;q5_0-q4_0;q5_0-q5_1;q5_1-q4_0;q4_1-q4_0"
)

ROCM_RUNTIME_DLLS = [
    "amdhip64_7.dll",
    "amd_comgr.dll",
    "hipblas.dll",
    "libhipblaslt.dll",
    "libtensilelite-host.dll",
    "origami.dll",
    "rocblas.dll",
    "rocm_kpack.dll",
    "rocsolver.dll",
]


def print_step(msg: str):
    print(f"\n{'=' * 65}")
    print(f"[*] {msg}")
    print(f"{'=' * 65}")


def load_config(config_path: Path) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    if config_path.is_file():
        cfg.read(config_path, encoding="utf-8")
    return cfg


def auto_detect_rocm(configured_path: str = "") -> str:
    if configured_path and os.path.isdir(configured_path):
        clang_test = os.path.join(configured_path, "lib", "llvm", "bin", "clang++.exe")
        if os.path.isfile(clang_test):
            return configured_path

    env_paths = [os.environ.get("ROCM_PATH", ""), os.environ.get("HIP_PATH", "")]
    common_paths = [
        r"G:\opt\rocm",
        r"C:\opt\rocm",
        r"D:\opt\rocm",
    ]
    # Check standard ROCm installs
    common_paths.extend(sorted(glob.glob(r"C:\Program Files\AMD\ROCm\*\."), reverse=True))

    for p in env_paths + common_paths:
        if p and os.path.isdir(p):
            test_file = os.path.join(p, "lib", "llvm", "bin", "clang++.exe")
            if os.path.isfile(test_file):
                return p
    return ""


def auto_detect_llama_dir(configured_dir: str = "", script_dir: Path = None) -> str:
    if configured_dir and os.path.isdir(configured_dir):
        if os.path.isfile(os.path.join(configured_dir, "CMakeLists.txt")):
            return configured_dir

    candidates = [
        script_dir.parent / "llama.cpp",
        script_dir / "llama.cpp",
        Path(r"G:\llama.cpp"),
        Path(r"C:\llama.cpp"),
    ]
    for c in candidates:
        if c.is_dir() and (c / "CMakeLists.txt").is_file():
            return str(c)

    return ""


def find_vcvars64() -> str:
    known_paths = [
        r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat",
        r"C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat",
        r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat",
    ]
    for p in known_paths:
        if os.path.isfile(p):
            return p

    vswhere = r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
    if os.path.isfile(vswhere):
        try:
            cmd = [vswhere, "-all", "-property", "installationPath"]
            out = subprocess.check_output(cmd, text=True, errors="replace")
            for line in out.splitlines():
                line = line.strip()
                cand = os.path.join(line, "VC", "Auxiliary", "Build", "vcvars64.bat")
                if os.path.isfile(cand):
                    return cand
        except Exception:
            pass

    return ""


def find_rc_compiler() -> str:
    pattern = r"C:\Program Files (x86)\Windows Kits\10\bin\*\x64\rc.exe"
    matches = glob.glob(pattern)
    if matches:
        matches.sort()
        return matches[-1]
    return ""


def get_vcvars_env(vcvars_path: str, rocm_path: str, rc_path: str) -> dict:
    cmd = f'cmd.exe /c "call \"{vcvars_path}\" >nul && set"'
    raw = subprocess.check_output(cmd, shell=True, text=True, errors="replace")
    env = {}
    for line in raw.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.upper()] = v

    rocm_llvm_bin = os.path.join(rocm_path, "lib", "llvm", "bin")
    rocm_bin = os.path.join(rocm_path, "bin")
    rc_dir = os.path.dirname(rc_path) if rc_path else ""

    curr_path = env.get("PATH", "")
    new_path = f"{rocm_llvm_bin};{rocm_bin};{rc_dir};{curr_path}"
    env["PATH"] = new_path
    env["HIP_PATH"] = rocm_path
    env["HIP_PLATFORM"] = "amd"
    return env


def run_command_stream(cmd: list, cwd: str, env: dict):
    print(f">> Running: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    for line in iter(proc.stdout.readline, ""):
        print(line, end="")
    proc.stdout.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"Command failed with exit code {rc}")


def main():
    script_dir = Path(__file__).resolve().parent
    config_file = script_dir / "build_config.ini"
    cfg = load_config(config_file)

    # Read config defaults
    cfg_gpu = cfg.get("GPU", "gpu_target", fallback="gfx1030")
    cfg_rocm = cfg.get("Paths", "rocm_path", fallback="")
    cfg_llama = cfg.get("Paths", "llama_dir", fallback="")
    cfg_deploy = cfg.get("Paths", "deploy_path", fallback="")
    cfg_jobs = cfg.getint("Build", "jobs", fallback=0)
    cfg_pull = cfg.getboolean("Build", "auto_pull", fallback=True)
    cfg_clean = cfg.getboolean("Build", "clean_build", fallback=False)

    parser = argparse.ArgumentParser(description="RDNA2LLamacpp - Automated Build & Update Tool")
    parser.add_argument("--gpu-target", default=cfg_gpu, help="Target AMD GPU architecture (e.g. gfx1030, gfx1031).")
    parser.add_argument("--rocm-path", default=cfg_rocm, help="Path to ROCm toolchain directory.")
    parser.add_argument("--llama-dir", default=cfg_llama, help="Path to llama.cpp source directory.")
    parser.add_argument("--dest", default=cfg_deploy, help="Optional deployment folder.")
    parser.add_argument("--no-pull", action="store_true", help="Skip git pull on llama.cpp.")
    parser.add_argument("--clean", action="store_true", default=cfg_clean, help="Clean build folder before compilation.")
    parser.add_argument("--jobs", "-j", type=int, default=cfg_jobs, help="Parallel compile jobs (0 = auto).")
    args = parser.parse_args()

    print_step("Step 1: Discovering Build Environment & Dependencies")

    # 1. Locate ROCm
    rocm_path = auto_detect_rocm(args.rocm_path)
    if not rocm_path:
        print("[-] Error: ROCm toolchain not found.")
        print("    Please install AMD ROCm / TheRock or specify 'rocm_path' in build_config.ini.")
        sys.exit(1)
    print(f"[+] Using ROCm Toolchain: {rocm_path}")

    clang_exe = os.path.join(rocm_path, "lib", "llvm", "bin", "clang.exe")
    clangxx_exe = os.path.join(rocm_path, "lib", "llvm", "bin", "clang++.exe")
    if not os.path.isfile(clang_exe) or not os.path.isfile(clangxx_exe):
        print(f"[-] Error: Clang compiler not found inside {rocm_path}.")
        sys.exit(1)

    # 2. Locate MSVC & Windows SDK
    vcvars = find_vcvars64()
    if not vcvars:
        print("[-] Error: Visual Studio 2022 vcvars64.bat not found.")
        print("    Please install Visual Studio 2022 with C++ Desktop Development.")
        sys.exit(1)
    print(f"[+] Found MSVC Environment: {vcvars}")

    rc_exe = find_rc_compiler()
    if not rc_exe:
        print("[-] Error: Windows SDK rc.exe not found.")
        sys.exit(1)
    print(f"[+] Found Windows SDK Resource Compiler: {rc_exe}")

    # 3. Locate or clone llama.cpp
    llama_dir = auto_detect_llama_dir(args.llama_dir, script_dir)
    if not llama_dir:
        default_clone = script_dir / "llama.cpp"
        print(f"[*] llama.cpp repository not found. Cloning into {default_clone}...")
        subprocess.run(["git", "clone", "--single-branch", "--branch", "master", "https://github.com/ggml-org/llama.cpp.git", str(default_clone)], check=True)
        llama_dir = str(default_clone)

    print(f"[+] Using llama.cpp Directory: {llama_dir}")

    # Determine CPU job count
    jobs = args.jobs
    if jobs <= 0:
        jobs = min(os.cpu_count() or 6, 8)
    print(f"[+] Compilation Jobs: {jobs}")
    print(f"[+] Target GPU Architecture: {args.gpu_target}")

    # Load MSVC environment
    print("[*] Initializing compiler environment variables...")
    build_env = get_vcvars_env(vcvars, rocm_path, rc_exe)

    # Step 2: Git Pull
    should_pull = cfg_pull and not args.no_pull
    if should_pull:
        print_step("Step 2: Updating llama.cpp (git pull)")
        try:
            run_command_stream(["git", "pull", "origin", "master"], cwd=llama_dir, env=build_env)
            rev = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=llama_dir, text=True).strip()
            msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], cwd=llama_dir, text=True).strip().splitlines()[0]
            print(f"[+] Current llama.cpp HEAD: {rev} ({msg})")
        except Exception as e:
            print(f"[-] Warning during git pull: {e}")
    else:
        print_step("Step 2: Skipping git pull")

    # Step 3: CMake Configure
    print_step("Step 3: Configuring CMake with Ninja")
    build_dir = os.path.join(llama_dir, "build")

    if args.clean and os.path.exists(build_dir):
        print(f"[*] Removing old build directory: {build_dir}")
        shutil.rmtree(build_dir)

    os.makedirs(build_dir, exist_ok=True)

    cmake_args = [
        "cmake",
        "-S", llama_dir,
        "-B", build_dir,
        "-G", "Ninja",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_SYSTEM_PROCESSOR=AMD64",
        "-DCMAKE_CROSSCOMPILING=ON",
        "-DCMAKE_SYSTEM_NAME=Windows",
        f"-DCMAKE_C_COMPILER={clang_exe.replace(os.sep, '/')}",
        f"-DCMAKE_CXX_COMPILER={clangxx_exe.replace(os.sep, '/')}",
        f"-DCMAKE_RC_COMPILER={rc_exe.replace(os.sep, '/')}",
        f"-DCMAKE_CXX_FLAGS=-I{rocm_path.replace(os.sep, '/')}/include",
        "-DGGML_HIP=ON",
        f"-DGPU_TARGETS={args.gpu_target}",
        "-DBUILD_SHARED_LIBS=ON",
        "-DLLAMA_BUILD_TESTS=OFF",
        "-DGGML_OPENMP=OFF",
        "-DGGML_CUDA_FORCE_CUBLAS=OFF",
        "-DGGML_RPC=ON",
        "-DGGML_HIP_ROCWMMA_FATTN=OFF",
        "-DLLAMA_BUILD_BORINGSSL=ON",
        "-DGGML_NATIVE=OFF",
        "-DGGML_STATIC=OFF",
        f"-DGGML_CUDA_FA_QUANTS={FA_QUANTS}",
    ]

    run_command_stream(cmake_args, cwd=llama_dir, env=build_env)

    # Step 4: Ninja Build
    print_step(f"Step 4: Compiling with Ninja ({jobs} parallel jobs)")
    run_command_stream(["ninja", "-C", "build", f"-j{jobs}"], cwd=llama_dir, env=build_env)

    # Step 5: Bundle ROCm Runtime Dependencies
    print_step("Step 5: Bundling Standalone ROCm Runtime DLLs & Kernels")
    bin_dir = os.path.join(build_dir, "bin")
    rocm_bin = os.path.join(rocm_path, "bin")

    for dll in ROCM_RUNTIME_DLLS:
        src = os.path.join(rocm_bin, dll)
        if os.path.isfile(src):
            dst = os.path.join(bin_dir, dll)
            shutil.copy2(src, dst)
            print(f"[+] Bundled DLL: {dll}")
        else:
            print(f"[-] Warning: {dll} not found in {rocm_bin}")

    src_rocblas = os.path.join(rocm_bin, "rocblas")
    dst_rocblas = os.path.join(bin_dir, "rocblas")
    if os.path.isdir(src_rocblas):
        print("[*] Copying rocblas kernel libraries...")
        shutil.copytree(src_rocblas, dst_rocblas, dirs_exist_ok=True)
        print("[+] Bundled rocblas GPU kernels.")

    # Step 6: Deploy to Target Folder
    if args.dest and os.path.isdir(args.dest):
        print_step(f"Step 6: Deploying Binaries to {args.dest}")
        dest_path = Path(args.dest)
        for f in glob.glob(os.path.join(bin_dir, "*.exe")) + glob.glob(os.path.join(bin_dir, "*.dll")):
            shutil.copy2(f, dest_path / os.path.basename(f))
            print(f"[+] Deployed: {os.path.basename(f)}")

        if os.path.isdir(dst_rocblas):
            shutil.copytree(dst_rocblas, dest_path / "rocblas", dirs_exist_ok=True)
            print("[+] Deployed rocblas library.")
        print(f"[+] Deployment complete in {args.dest}")
    else:
        print_step("Step 6: Standalone Binaries Ready")
        print(f"[+] All self-contained binaries and DLLs are located at: {bin_dir}")

    # Step 7: Verification
    print_step("Step 7: Verifying Binary and GPU Detection")
    verify_dir = args.dest if (args.dest and os.path.isdir(args.dest)) else bin_dir
    cli_exe = os.path.join(verify_dir, "llama-cli.exe")
    if os.path.isfile(cli_exe):
        clean_env = {"PATH": f"C:\\Windows\\system32;C:\\Windows;{verify_dir}"}
        print("[*] llama-cli version:")
        subprocess.run([cli_exe, "--version"], env=clean_env, cwd=verify_dir)
        print("\n[*] GPU Device Detection:")
        subprocess.run([cli_exe, "--list-devices"], env=clean_env, cwd=verify_dir)

    print("\n" + "=" * 65)
    print("[*] SUCCESS! RDNA2LLamacpp build and update completed.")
    print("=" * 65)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[-] ERROR: {e}")
        sys.exit(1)
