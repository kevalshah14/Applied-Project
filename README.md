# Natural Language Robot Control Framework

A **transferable framework** for controlling robots using natural language, powered by Large Language Models (LLMs) as planners and executors.

[![GitHub](https://img.shields.io/badge/GitHub-Repository-black.svg)](https://github.com/kevalshah14/Applied-Project)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Demo

[Watch the Project Demo Video](https://github.com/kevalshah14/Applied-Project/blob/master/Report/Applied%20Project%20Demo.mp4)


## Overview

This project enables users to control robotic systems through conversational natural language commands. The core innovation is a **tool abstraction layer** that decouples the LLM's intelligence from robot-specific hardware, making the system easily transferable to different robots.

### Key Features

- 🗣️ **Natural Language Control** – Command robots using plain English
- 🔧 **Transferable Architecture** – Swap robot hardware by only changing tool implementations
- 👁️ **Open-Vocabulary Object Detection** – Find any object using Gemini VLM
- 🎯 **Precise Segmentation** – SAM 2.1 for accurate object localization
- 📏 **3D Depth Perception** – OAK-D stereo camera for spatial awareness
- 🤖 **LLM as Planner & Executor** – Gemini 2.5 Flash with automatic function calling

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│                   (Next.js Frontend)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────▼───────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              LLM Agent (Gemini 2.5 Flash)           │    │
│  │         System Prompt + Automatic Tool Calling      │    │
│  └─────────────────────────┬───────────────────────────┘    │
│                            │                                │
│  ┌─────────────────────────▼───────────────────────────┐    │
│  │              Tool Abstraction Layer                 │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │    │
│  │  │find_obj  │ │pickup    │ │place     │ │gripper │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘  │    │
│  └─────────────────────────┬───────────────────────────┘    │
└─────────────────────────────┼───────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Perception  │    │    Control    │    │   External    │
│   (OAK-D +    │    │   (Dobot +    │    │   AI APIs     │
│    SAM 2.1)   │    │   pydobot)    │    │   (Gemini)    │
└───────────────┘    └───────────────┘    └───────────────┘
```

## Project Structure

```
Applied-Project/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── state.py             # Shared state (image store)
│   ├── ai/
│   │   ├── chat.py          # LLM chat with tool configuration
│   │   └── tools.py         # Robot tool definitions
│   ├── perception/
│   │   ├── stream.py        # Camera streaming manager
│   │   ├── depth.py         # Depth estimation utilities
│   │   └── init.py          # DepthAI pipeline setup
│   ├── controls/
│   │   ├── __init__.py      # Robot controller export
│   │   └── robot_control.py # Dobot hardware interface
│   └── data_collection/     # Data collection for ACT fine-tuning
│       ├── __init__.py      # Module exports
│       ├── collect_data.py  # Record demonstrations in HDF5
│       └── convert_to_lerobot.py  # Convert to LeRobot format
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js app router pages
│   │   └── components/      # React components
│   ├── package.json
│   └── tailwind.config.js
├── Report.tex               # Academic paper
└── README.md
```

## Hardware Requirements

- **Robot Arm**: Dobot Magician (4-DOF) with suction gripper
- **Camera**: Luxonis OAK-D / OAK-D Lite stereo camera
- **Computer**: Any machine capable of running Python 3.11+ and Node.js 18+

## Software Requirements

- Python 3.11+
- Node.js 18+
- Google Gemini API key

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/kevalshah14/Applied-Project.git
cd Applied-Project
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (using uv recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync

# Or with pip
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the `backend/` directory:

```env
APIKEY=your_google_gemini_api_key
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

## Usage

### 1. Start the Backend

```bash
cd backend
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```

### 3. Open the Interface

Navigate to [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Example Commands

| Command | Description |
|---------|-------------|
| "Show me the camera" | Activates live camera stream |
| "Where is the apple?" | Finds and returns 3D coordinates |
| "Pick up the banana" | Executes full pick sequence |
| "Place it in the box" | Moves to target and releases |
| "Go home" | Returns robot to home position |
| "Open the gripper" | Releases suction |

## Defined Tools

| Tool | Description |
|------|-------------|
| `access_camera` | Activates camera stream for visualization |
| `find_object(description)` | Locates object and returns 3D coordinates (mm) |
| `get_depth(x, y)` | Returns depth at a specific 2D point |
| `pickup_object(x, y, z)` | Executes pick sequence: approach, lower, grasp, lift |
| `place_object(x, y, z)` | Moves to target location and releases gripper |
| `open_gripper()` | Opens gripper / releases suction |
| `close_gripper()` | Closes gripper / activates suction |
| `go_home()` | Moves robot to safe home position |
| `get_robot_pose()` | Returns current end-effector pose |

## Transferability

The key design principle is **hardware abstraction**. To adapt this system to a different robot:

1. **Replace `robot_control.py`** – Implement the same interface for your robot
2. **Update gripper tools** – Match your gripper's API
3. **Re-calibrate** – Adjust camera-to-robot transformation

**What stays the same:**
- LLM prompts and tool descriptions
- Frontend interface
- Perception pipeline (Gemini + SAM)

## Data Collection for ACT Fine-tuning

This project includes a data collection pipeline that enables **progressive improvement** through imitation learning. The LLM initially uses tools for manipulation, then transitions to invoking trained **ACT** policies once sufficient demonstration data is collected.

### Progressive Learning Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 1: Tool-Based Execution                │
│  User: "Pick up the red cube"                                   │
│  LLM → find_object() → pickup_object() → [Success recorded]    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [50+ demonstrations collected]
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 2: Policy Training                     │
│  HDF5 episodes → LeRobot format → Fine-tune ACT                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 3: Policy Invocation                   │
│  User: "Pick up the red cube"                                   │
│  LLM → execute_policy("pick_red_cube") → [Faster execution]    │
└─────────────────────────────────────────────────────────────────┘
```

### Key Capabilities

| Phase | Approach | Speed | Flexibility |
|-------|----------|-------|-------------|
| Initial | Tool-based | Slower | High (any task) |
| Learned | Policy-based | Fast | Task-specific |
| Hybrid | LLM decides | Optimal | Best of both |

### Collecting Demonstrations

```bash
cd backend/data_collection

# Collect 50 episodes for a pick-and-place task
python collect_data.py \
    --task "pick_red_cube" \
    --num-episodes 50 \
    --output-dir data/dobot/demonstrations
```

**During collection:**
1. Press Enter when ready to start each episode
2. Physically guide the robot through the demonstration (kinesthetic teaching)
3. Press Ctrl+C when the demonstration is complete
4. Repeat for all episodes

### Converting to LeRobot Format

```bash
python convert_to_lerobot.py \
    --input-dir data/dobot/demonstrations \
    --repo-id your_username/dobot_pick_cube \
    --task "pick red cube"
```

**Options:**
- `--push-to-hub` – Upload dataset to HuggingFace Hub
- `--mode video` – Use video compression for smaller files

### Data Format

Each episode records:
| Data | Shape | Description |
|------|-------|-------------|
| Robot State | (5,) | x, y, z, r, suction |
| Image | (224, 224, 3) | RGB from OAK-D camera |
| Action | (5,) | Change in state (delta) |

### Training ACT Policies

After collecting and converting data, train ACT policies:

```bash
# See: https://github.com/huggingface/lerobot
# ACT training example:
python lerobot/scripts/train.py \
    policy=act \
    env=your_env \
    dataset_repo_id=your_username/dobot_pick_cube
```

### LLM as Meta-Controller

Once policies are trained, the LLM evolves from executor to orchestrator:

- **Novel tasks** → LLM uses tools (`find_object`, `pickup_object`, etc.)
- **Learned tasks** → LLM invokes policy (`execute_policy("pick_red_cube")`)
- **Hybrid tasks** → LLM uses tools for novel parts, policies for learned parts

This creates a **self-improving system** where the robot becomes progressively more capable while maintaining flexibility for new situations.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Send message, receive streamed response |
| `/health` | GET | Health check |
| `/image/{id}` | GET | Retrieve annotated image by ID |
| `/stream` | GET | Live camera MJPEG stream |

## Technology Stack

### Backend
- **FastAPI** – Async web framework
- **Google Gemini** – LLM with function calling
- **Ultralytics SAM 2.1** – Segmentation
- **DepthAI** – OAK-D camera SDK
- **pydobot** – Dobot control library
- **OpenCV** – Image processing

### Frontend
- **Next.js 14** – React framework with App Router
- **TypeScript** – Type safety
- **Tailwind CSS** – Styling

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.

## Acknowledgments

- Google DeepMind for Gemini
- Meta AI for Segment Anything Model
- Luxonis for DepthAI SDK
- Dobot for pydobot library
- Stanford/Google for ACT (Action Chunking with Transformers)
- HuggingFace for LeRobot framework
