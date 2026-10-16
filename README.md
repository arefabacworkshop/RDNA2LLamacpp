# 🦙 RDNA2LLamacpp

<div align="center">

[![GitHub Release](https://img.shields.io/github/v/release/arefabacworkshop/RDNA2LLamacpp?logo=github&logoColor=white&style=for-the-badge)](https://github.com/arefabacworkshop/RDNA2LLamacpp/releases/latest)
[![Release Date](https://img.shields.io/github/release-date/arefabacworkshop/RDNA2LLamacpp?logo=github&logoColor=white&style=for-the-badge)](https://github.com/arefabacworkshop/RDNA2LLamacpp/releases/latest)
[![License](https://img.shields.io/github/license/arefabacworkshop/RDNA2LLamacpp?style=for-the-badge)](LICENSE)

[![ROCm 7.0](https://img.shields.io/badge/ROCm-7.0%20(TheRock)-red?logo=amd&logoColor=white&style=for-the-badge)](https://github.com/ROCm/ROCm)
[![llama.cpp](https://img.shields.io/badge/Powered%20By-llama.cpp-blue?logo=llama&logoColor=white&style=for-the-badge)](https://github.com/ggerganov/llama.cpp)
[![GPU Target](https://img.shields.io/badge/GPU-AMD%20RDNA2%20(gfx103X)-00B04F?logo=amd&logoColor=white&style=for-the-badge)](#-supported-gpus)
[![OS](https://img.shields.io/badge/OS-Windows%20%7C%20Ubuntu-0078D6?logo=windows&logoColor=white&style=for-the-badge)](#-nightly-downloads)

**Automated, nightly, high-performance builds of [llama.cpp](https://github.com/ggerganov/llama.cpp) accelerated with AMD ROCm™ 7 (TheRock), specifically engineered for AMD Radeon RX 6000 series (RDNA2) GPUs.**

[Quick Start](#-quick-start) • [Downloads](#-nightly-downloads) • [Supported GPUs](#-supported-gpus) • [RDNA2 Optimization](#-rdna2-performance-tuning) • [Manual Build](#-manual-compilation)

</div>

---

## ⚡ Why RDNA2LLamacpp?

Running local LLMs on consumer AMD GPUs under Windows and Linux has historically been difficult: official ROCm SDKs are massive (20+ GB), setup is error-prone, and standard releases often lack discrete RDNA2 device kernels.

**RDNA2LLamacpp solves this:**
- **Zero SDK Installation**: Binaries are 100% self-contained. All necessary ROCm runtime libraries (`amdhip64`, `rocblas`, `hipblaslt`, and pre-compiled `.kpack` GPU kernels) are bundled alongside the executable. Just extract and run.
- **Dedicated RDNA2 Machine Code**: Compiled specifically for discrete RDNA2 sub-architectures (`gfx1030`, `gfx1031`, `gfx1032`, `gfx1034`), avoiding multi-architecture bloat.
- **Nightly Freshness**: Our automated GitHub Actions pipeline automatically detects and integrates the latest daily `llama.cpp` upstream master with the freshest AMD TheRock nightly runtime.

---

## 🎯 Supported GPUs

This repository targets all discrete **AMD Radeon RX 6000 Series (RDNA2 / `gfx103X`)** graphics cards:

| Architecture ID | Graphics Cards | VRAM |
| :--- | :--- | :--- |
| **`gfx1030`** | AMD Radeon **RX 6950 XT**, **RX 6900 XT**, **RX 6800 XT**, **RX 6800** | 16 GB GDDR6 |
| **`gfx1031`** | AMD Radeon **RX 6750 XT**, **RX 6700 XT**, **RX 6700** | 10–12 GB GDDR6 |
| **`gfx1032`** | AMD Radeon **RX 6650 XT**, **RX 6600 XT**, **RX 6600** | 8 GB GDDR6 |
| **`gfx1034`** | AMD Radeon **RX 6500 XT**, **RX 6400** | 4 GB GDDR6 |

> [!NOTE]
> All releases package a unified fat binary covering `gfx1030;gfx1031;gfx1032;gfx1034`, ensuring out-of-the-box compatibility across all cards above.

---

## 🚀 Nightly Downloads

| Operating System | Package | Direct Download |
| :--- | :--- | :--- |
| **Windows 10 / 11 (x64)** | `llama-b*-windows-rocm-gfx103X-x64.zip` | [![Download Windows](https://img.shields.io/badge/Download-Windows%20Build-0078D6?style=flat-square&logo=windows&logoColor=white)](https://github.com/arefabacworkshop/RDNA2LLamacpp/releases/latest) |
| **Ubuntu 22.04+ (x64)** | `llama-b*-ubuntu-rocm-gfx103X-x64.zip` | [![Download Ubuntu](https://img.shields.io/badge/Download-Ubuntu%20Build-E95420?style=flat-square&logo=ubuntu&logoColor=white)](https://github.com/arefabacworkshop/RDNA2LLamacpp/releases/latest) |

---

## 🧪 Quick Start

### 1. Download & Extract
Download the archive for your operating system from [Latest Releases](https://github.com/arefabacworkshop/RDNA2LLamacpp/releases/latest) and extract it to your preferred folder.

### 2. Run Inference
You can immediately launch `llama-server` (OpenAI-compatible local server) or `llama-cli` with any GGUF model:

#### Windows (PowerShell / Command Prompt):
```cmd
llama-server.exe -m "C:\models\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf" -ngl 99 -fa -b 512 -ub 256
```

#### Ubuntu:
```bash
./llama-server -m ~/models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf -ngl 99 -fa -b 512 -ub 256
```

---

## 💡 RDNA2 Performance Tuning

To maximize token generation speed on RDNA2 hardware, use these recommended parameters:

- **`-ngl 99` (GPU Layer Offload)**: Offloads all model layers to your Radeon GPU VRAM.
- **`-fa` (Flash Attention)**: Essential on RDNA2. Bypasses intermediate $O(N^2)$ attention matrices, saving gigabytes of VRAM and drastically speeding up long context prompts.
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
├── LICENSE                          # MIT License
└── README.md                        # Documentation & quick start
```

---

## 📋 Manual Compilation

If you prefer building from source on your own machine rather than downloading pre-compiled releases, refer to our detailed step-by-step guide:  
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
