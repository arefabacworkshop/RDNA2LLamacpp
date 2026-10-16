# Manual Build Instructions (AMD RDNA2 / gfx103X)

> These steps guide you through building **llama.cpp** with **AMD ROCm™ 7 (TheRock)** acceleration specifically for **AMD RDNA2 GPUs** (`gfx1030`, `gfx1031`, `gfx1032`, `gfx1034`).
>
> For the automated GitHub Actions CI/CD matrix and release packaging, see the [GitHub Actions workflow](../.github/workflows/build-llamacpp-rocm.yml).

- [Supported RDNA2 GPUs](#supported-rdna2-gpus)
- [Download ROCm Nightly Tarball](#download-a-rocm-nightly-tarball)
- [Windows Build](#windows)
- [Ubuntu Build](#ubuntu)
- [Portable Packaging (Standalone Binaries)](#portable-packaging-optional)
- [Recommended Runtime Settings](#recommended-runtime-settings)

---

## Supported RDNA2 GPUs

| Sub-Architecture | Discrete AMD Radeon GPUs |
| :--- | :--- |
| **`gfx1030`** | Radeon RX 6950 XT, RX 6900 XT, RX 6800 XT, RX 6800 |
| **`gfx1031`** | Radeon RX 6750 XT, RX 6700 XT, RX 6700 |
| **`gfx1032`** | Radeon RX 6650 XT, RX 6600 XT, RX 6600 |
| **`gfx1034`** | Radeon RX 6500 XT, RX 6400 |

You can target all cards at once using `"gfx1030;gfx1031;gfx1032;gfx1034"`, or specify only your card's target (e.g., `"gfx1030"`) to produce a smaller, tailored binary.

---

## Download a ROCm Nightly Tarball

AMD TheRock publishes multi-arch nightlies at [nightly.repo.amd.com/rocm/core/tarball/](https://nightly.repo.amd.com/rocm/core/tarball/).

Download the newest tarball for your operating system:
- **Windows:** `therock-dist-windows-gfx103X-all-<version>.tar.gz`
- **Linux:** `therock-dist-linux-gfx103X-all-<version>.tar.gz`

*(Skip any files containing `-tests-` in the filename).*

---

## Windows

### 1. Install Build Tools

Install Visual Studio 2022 (Desktop Development with C++, CMake, ATL, Windows 11 SDK) and Ninja:

```powershell
winget install Kitware.CMake Ninja-build.Ninja Git.Git
```
*(Alternatively, install via Chocolatey: `choco install cmake ninja git -y`)*

> [!IMPORTANT]
> Use Visual Studio 2022 (MSVC 14.4x). Do not use preview MSVC 14.5x toolsets, as their `<cmath>` header introduces a `constexpr` symbol conflict with ROCm Clang.

### 2. Extract ROCm

Extract the downloaded Windows tarball to `C:\opt\rocm`:

```powershell
mkdir C:\opt\rocm
tar -xzf therock-dist-windows-gfx103X-all-<version>.tar.gz -C C:\opt\rocm --strip-components=1
```

Clone `llama.cpp`:

```powershell
git clone --filter=blob:none --single-branch --branch master https://github.com/ggerganov/llama.cpp.git
```

### 3. Build

Open **x64 Native Tools Command Prompt for VS 2022** and run:

```cmd
set HIP_PATH=C:\opt\rocm
set HIP_PLATFORM=amd
set PATH=%HIP_PATH%\lib\llvm\bin;%HIP_PATH%\bin;%PATH%

cd llama.cpp
mkdir build
cd build

cmake .. -G Ninja ^
  -DCMAKE_C_COMPILER="C:\opt\rocm\lib\llvm\bin\clang.exe" ^
  -DCMAKE_CXX_COMPILER="C:\opt\rocm\lib\llvm\bin\clang++.exe" ^
  -DCMAKE_CXX_FLAGS="-IC:\opt\rocm\include -mwavefrontsize64=0" ^
  -DCMAKE_CROSSCOMPILING=ON ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DGPU_TARGETS="gfx1030;gfx1031;gfx1032;gfx1034" ^
  -DBUILD_SHARED_LIBS=ON ^
  -DLLAMA_BUILD_TESTS=OFF ^
  -DGGML_HIP=ON ^
  -DGGML_OPENMP=OFF ^
  -DGGML_CUDA_FORCE_CUBLAS=OFF ^
  -DGGML_RPC=ON ^
  -DGGML_HIP_ROCWMMA_FATTN=OFF ^
  -DLLAMA_BUILD_BORINGSSL=ON ^
  -DGGML_NATIVE=OFF ^
  -DGGML_STATIC=OFF ^
  -DCMAKE_SYSTEM_NAME=Windows

cmake --build . -j %NUMBER_OF_PROCESSORS%
```

Executables will be built into `llama.cpp\build\bin`.

---

## Ubuntu

### 1. Install Build Tools

```bash
sudo apt update
sudo apt install -y cmake ninja-build git wget curl
```

### 2. Extract ROCm

```bash
sudo mkdir -p /opt/rocm
sudo tar -xzf therock-dist-linux-gfx103X-all-<version>.tar.gz -C /opt/rocm --strip-components=1

export HIP_PATH=/opt/rocm
export ROCM_PATH=/opt/rocm
export HIP_PLATFORM=amd
export PATH=/opt/rocm/bin:/opt/rocm/llvm/bin:$PATH
export LD_LIBRARY_PATH=/opt/rocm/lib:/opt/rocm/lib64:/opt/rocm/llvm/lib:${LD_LIBRARY_PATH:-}
```

Clone `llama.cpp`:

```bash
git clone --filter=blob:none --single-branch --branch master https://github.com/ggerganov/llama.cpp.git
```

### 3. Build

```bash
cd llama.cpp
mkdir build
cd build

cmake .. -G Ninja \
  -DCMAKE_C_COMPILER=/opt/rocm/llvm/bin/clang \
  -DCMAKE_CXX_COMPILER=/opt/rocm/llvm/bin/clang++ \
  -DCMAKE_CXX_FLAGS="-I/opt/rocm/include -mwavefrontsize64=0" \
  -DCMAKE_CROSSCOMPILING=ON \
  -DCMAKE_BUILD_TYPE=Release \
  -DGPU_TARGETS="gfx1030;gfx1031;gfx1032;gfx1034" \
  -DBUILD_SHARED_LIBS=ON \
  -DLLAMA_BUILD_TESTS=OFF \
  -DGGML_HIP=ON \
  -DGGML_OPENMP=OFF \
  -DGGML_CUDA_FORCE_CUBLAS=OFF \
  -DGGML_RPC=ON \
  -DGGML_HIP_ROCWMMA_FATTN=OFF \
  -DLLAMA_BUILD_BORINGSSL=ON \
  -DGGML_NATIVE=OFF \
  -DGGML_STATIC=OFF \
  -DCMAKE_SYSTEM_NAME=Linux

cmake --build . -j $(nproc)
```

Binaries will be placed in `llama.cpp/build/bin`.

---

## Portable Packaging (Optional)

To create a standalone folder with all required ROCm runtime libraries copied directly next to the binaries (no need for ROCm in system PATH):

### Windows (PowerShell):
```powershell
$rocmBin = "C:\opt\rocm\bin"
$outDir = "llama.cpp\build\bin"

# Copy core DLLs
Copy-Item "$rocmBin\amdhip64_*.dll" $outDir
Copy-Item "$rocmBin\rocm_kpack.dll" $outDir -ErrorAction SilentlyContinue
Copy-Item "$rocmBin\amd_comgr*.dll" $outDir
Copy-Item "$rocmBin\rocblas.dll" $outDir
Copy-Item "$rocmBin\hipblas.dll" $outDir
Copy-Item "$rocmBin\hipblaslt.dll" $outDir
Copy-Item "$rocmBin\rocsolver.dll" $outDir
Copy-Item "$rocmBin\origami.dll" $outDir -ErrorAction SilentlyContinue
Copy-Item "$rocmBin\libtensilelite-host.dll" $outDir -ErrorAction SilentlyContinue

# Copy kernel libraries
Copy-Item -Recurse "$rocmBin\rocblas\library" "$outDir\rocblas\library"
Copy-Item -Recurse "$rocmBin\hipblaslt\library" "$outDir\hipblaslt\library" -ErrorAction SilentlyContinue
Copy-Item -Recurse "C:\opt\rocm\.kpack" "$outDir\.kpack" -ErrorAction SilentlyContinue
```

---

## Recommended Runtime Settings

To maximize performance on RDNA2 hardware:
- **Enable Flash Attention**: Add `-fa` to drastically reduce VRAM usage and accelerate long-context prompt processing.
- **Tune Batching**: Add `-b 512 -ub 256` to saturate memory throughput.
- **Optimal Quantization**: Use **`Q4_K_M`** or **`Q5_K_M`** to fit critical weights into AMD's high-speed **Infinity Cache**.

```bash
llama-server -m your_model_Q4_K_M.gguf -ngl 99 -fa -b 512 -ub 256
```
