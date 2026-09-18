# Nemo Note

Nemo Note is a local AI audio transcription application using Parakeet TDT 0.6B v3 through Parakeet.cpp.

## Requirements

* Windows 10 or Windows 11
* Git
* Python 3.11+
* Node.js
* Rust
* Microsoft Visual C++ Build Tools

## How to Run

### 1. Clone the repository

```powershell
git clone https://github.com/KalanaBamunuarachchi/nemo-note.git
cd nemo-note
```

### 2. Download the Parakeet model

Download:

`tdt-0.6b-v3-f16.gguf`

[Download model](https://huggingface.co/mudler/parakeet-cpp-gguf/resolve/main/tdt-0.6b-v3-f16.gguf)

Place the downloaded file here:

```text
engines/parakeet/models/tdt-0.6b-v3-f16.gguf
```

### 3. Download the Parakeet runtimes

Nemo Note uses Parakeet.cpp v0.5.0.

Download the following runtime packages from the [Parakeet.cpp v0.5.0 release](https://github.com/mudler/parakeet.cpp/releases/tag/v0.5.0):

```text
parakeet-v0.5.0-bin-win-cpu-x64.zip
parakeet-v0.5.0-bin-win-vulkan-x64.zip
parakeet-v0.5.0-bin-win-cuda-x64.zip
```

Extract each runtime into its corresponding folder:

```text
engines/parakeet/runtimes/cpu/
engines/parakeet/runtimes/vulkan/
engines/parakeet/runtimes/cuda/
```

The folders should contain the Parakeet executable and the other files included with each runtime package.

The final structure should look like:

```text
engines/
└── parakeet/
    ├── models/
    │   └── tdt-0.6b-v3-f16.gguf
    │
    └── runtimes/
        ├── cpu/
        │   └── parakeet runtime files
        │
        ├── vulkan/
        │   └── parakeet runtime files
        │
        └── cuda/
            └── parakeet runtime files
```

### 4. Set up the backend

Open a terminal in the project directory:

```powershell
cd backend
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

Install the Python dependencies:

```powershell
pip install -r requirements.txt
```

### 5. Set up the frontend

Open a new terminal and go to the frontend directory:

```powershell
cd frontend
```

Install the frontend dependencies:

```powershell
npm install
```

### 6. Run Nemo Note

From the `frontend` directory:

```powershell
npm run tauri dev
```

Nemo Note will start and launch the backend automatically.

Once the application opens, select an audio file, choose a processing engine, and click **Transcribe**.
