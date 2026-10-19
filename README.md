# 🦙 RDNA2LLamacpp

<div align="center">

[![Build Pipeline](https://img.shields.io/github/actions/workflow/status/arefabacworkshop/RDNA2LLamacpp/build-llamacpp-rocm.yml?branch=main&logo=github&logoColor=white&style=for-the-badge)](https://github.com/arefabacworkshop/RDNA2LLamacpp/actions)
[![License](https://img.shields.io/github/license/arefabacworkshop/RDNA2LLamacpp?style=for-the-badge)](LICENSE)
[![ROCm 7.0](https://img.shields.io/badge/ROCm-7.0%20(TheRock)-red?logo=amd&logoColor=white&style=for-the-badge)](https://github.com/ROCm/ROCm)
[![llama.cpp](https://img.shields.io/badge/Powered%20By-llama.cpp-blue?logo=llama&logoColor=white&style=for-the-badge)](https://github.com/ggerganov/llama.cpp)
[![GPU Target](https://img.shields.io/badge/GPU-AMD%20RDNA2%20(gfx103X)-00B04F?logo=amd&logoColor=white&style=for-the-badge)](#-supported-gpus)
[![OS](https://img.shields.io/badge/OS-Windows%20%7C%20Ubuntu-0078D6?logo=windows&logoColor=white&style=for-the-badge)](#-building--running)

**Automated CI/CD and build framework for [llama.cpp](https://github.com/ggerganov/llama.cpp) accelerated with AMD ROCm™ 7 (TheRock), specifically engineered for discrete AMD Radeon RX 6000 series (RDNA2 / gfx103X) GPUs.**

[Supported GPUs](#-supported-gpus) • [Building & Running](#-building--running) • [RDNA2 Performance](#-rdna2-performance-tuning) • [Manual Build](#-manual-compilation)

</div>

---

## ⚡ Why RDNA2LLamacpp?

Running local LLMs on consumer AMD GPUs under Windows and Linux has historically been difficult: official ROCm SDKs are massive (20+ GB), setup is error-prone, and standard releases often lack discrete RDNA2 device kernels.

**RDNA2LLamacpp solves this:**
- **Zero SDK Installation**: Binaries can be packaged 100% self-contained. All necessary ROCm runtime libraries (`amdhip64`, `rocblas`, `hipblaslt`, and pre-compiled `.kpack` GPU kernels) are bundled alongside the executable.
- **Dedicated RDNA2 Machine Code**: Compiled specifically for discrete RDNA2 sub-architectures (`gfx1030`, `gfx1031`, `gfx1032`, `gfx1034`), avoiding multi-architecture bloat.
- **Automated Workflow**: An automated GitHub Actions pipeline that pairs upstream `llama.cpp` with AMD's freshest TheRock multi-arch nightly runtime.

---

## 🎯 Supported GPUs

This repository targets all discrete **AMD Radeon RX 6000 Series (RDNA2 / `gfx103X`)** graphics cards:

| Architecture ID | Graphics Cards | VRAM |
| :--- | :--- | :--- |
| **`gfx1030`** | AMD Radeon **RX 6950 XT**, **RX 6900 XT**, **RX 6800 XT**, **RX 6800** | 16 GB GDDR6 |
| **`gfx1031`** | AMD Radeon **RX 6750 XT**, **RX 6700 XT**, **RX 6700** | 10–12 GB GDDR6 |
| **`gfx1032`** | AMD Radeon **RX 6650 XT**, **RX 6600 XT**, **RX 6600** | 8 GB GDDR6 |
| **`gfx1034`** | AMD Radeon **RX 6500 XT**, **RX 6400** | 4 GB GDDR6 |

---

## 🚀 Building & Running

### Option 1: 1-Click Local Build & Update (Windows - Recommended)

The easiest and fastest way to build `llama.cpp` locally for your specific RDNA2 GPU. No manual terminal commands required:

1. **Configure Paths (Optional)**: Open [`build_config.ini`](build_config.ini) to set your GPU target and paths:
   ```ini
   [GPU]
   # gfx1030 (RX 6800/6900), gfx1031 (RX 6700), gfx1032 (RX 6600), gfx1034 (RX 6400/6500)
   gpu_target = gfx1030

   [Paths]
   rocm_path = C:\opt\rocm   # Path to your ROCm / TheRock extraction (or leave empty to auto-detect)
   llama_dir =               # Path to llama.cpp (auto-cloned if left empty)
   deploy_path =             # Optional: target directory to deploy the final binaries
   ```
2. **Double-click `Build_or_Update.bat`** (or run `python build_rdna2.py`).
3. **What happens automatically:**
   - 🔍 Auto-detects your MSVC 2022 compiler and Windows SDK.
   - 🔄 Pulls the latest upstream `llama.cpp` commits via `git pull`.
   - ⚡ Configures CMake + Ninja with custom FlashAttention kernels (symmetric + all hybrid combinations like `q5_0-q5_1`, `q8_0-q4_0`, etc.).
   - 📦 Bundles all required ROCm runtime DLLs (`amdhip64_7.dll`, `rocblas.dll`, `hipblas.dll`, etc.) and pre-compiled `.hsaco` GPU kernels into `build/bin`.
   - 🚀 (Optional) Copies the standalone binaries into your server deployment directory.
   - ✅ Verifies hardware recognition and GPU VRAM detection with `llama-cli.exe --list-devices`.

### Option 2: Automated CI via GitHub Actions
You can build the binaries directly in GitHub Actions without installing build tools locally:
1. Go to the [**Actions** tab](https://github.com/arefabacworkshop/RDNA2LLamacpp/actions/workflows/build-llamacpp-rocm.yml) in the repository.
2. Select **Build Llama.cpp + ROCm** and click **Run workflow**.
3. Once completed, download the self-contained build artifacts from the workflow run summary (`llama-windows-rocm-gfx103X-x64` or `llama-ubuntu-rocm-gfx103X-x64`).

### Option 3: Manual Step-by-Step Compilation
For advanced users who want to run the raw CMake and Ninja commands manually:  
👉 **[docs/manual_instructions.md](docs/manual_instructions.md)**

---

## 🧪 Running Inference

Once you have compiled or downloaded the binaries, run `llama-server` (OpenAI-compatible server) or `llama-cli`:

### Windows:
```cmd
llama-server.exe -m "C:\models\your_model_Q4_K_M.gguf" -ngl 99 -fa -b 512 -ub 256
```

### Ubuntu:
```bash
./llama-server -m ~/models/your_model_Q4_K_M.gguf -ngl 99 -fa -b 512 -ub 256
```

---

## 💡 RDNA2 Performance Tuning

To maximize token generation speed on RDNA2 hardware, use these recommended parameters:

- **`-ngl 99` (GPU Layer Offload)**: Offloads all model layers to your Radeon GPU VRAM.
- **`-fa` (Flash Attention)**: Essential on RDNA2. Bypasses intermediate $O(N^2)$ attention matrices, saving gigabytes of VRAM and drastically speeding up long context prompts.
- **`-ctk` / `-ctv` (KV Cache Quantization)**: Supports pure and hybrid quantized caches (`-ctk q8_0 -ctv q4_0`, `-ctk q5_0 -ctv q5_1`, etc.) with full compiled FlashAttention vector acceleration.
- **`-b 512 -ub 256` (Batch Tuning)**: Matches physical micro-batches to RDNA2 SIMD32 compute units to maintain high occupancy.
- **Quantization Choice (`Q4_K_M` / `Q5_K_M`)**: RDNA2 features on-chip high-speed **Infinity Cache** (96 MB on RX 6700 series, 128 MB on RX 6800/6900 series). Medium 4-bit and 5-bit models fit more working memory directly inside the cache for maximum memory bandwidth.
- **Windows HAGS**: In Windows *Settings > System > Display > Graphics > Default graphics settings*, enable **Hardware-accelerated GPU scheduling** for lower kernel dispatch latency.

---

## 🛠️ Repository Structure

```
RDNA2LLamacpp/
├── .github/
│   ├── actions/
│   │   └── test-llamacpp-build/     # Automated smoke-test action using Qwen3 GGUF
│   ├── ISSUE_TEMPLATE/              # Tailored RDNA2 bug reports & issue configs
│   └── workflows/
│       ├── build-llamacpp-rocm.yml  # Main CI/CD matrix build & release pipeline
│       └── test-llamacpp-rocm.yml   # Dispatchable test workflow for hardware runners
├── docs/
│   └── manual_instructions.md       # Complete local manual compilation guide
├── utils/
│   └── gather_required_libs.py      # Dynamic Linux shared library dependency resolver
├── build_config.ini                 # Simple user configuration file (paths, GPU target, etc.)
├── build_rdna2.py                   # Automated Python build & dependency bundling engine
├── Build_or_Update.bat              # 1-Click Windows batch launcher
├── LICENSE                          # MIT License
└── README.md                        # Documentation & setup guide
```

---

## 📋 Manual Compilation Guide

For the complete local setup guide, commands, and dependency lists:  
👉 **[docs/manual_instructions.md](docs/manual_instructions.md)**

---

## 🤝 Upstream Projects & Credits

This project builds upon the hard work of:
- **[llama.cpp](https://github.com/ggerganov/llama.cpp)** by Georgi Gerganov and contributors.
- **[TheRock](https://github.com/ROCm/TheRock)** (AMD ROCm™ multi-architecture compute platform).
- Upstream pipeline foundations from [aigdat/llamacpp-rocm](https://github.com/aigdat/llamacpp-rocm) & [lemonade-sdk](https://github.com/lemonade-sdk/lemonade).

---

## 📄 License

This repository is distributed under the [MIT License](LICENSE).
