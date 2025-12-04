# Applied Robotics Project

An AI-powered robotic manipulation system with vision capabilities, featuring real-time camera streaming, depth perception, object detection, and conversational control through a modern web interface.

## 🏗️ Architecture

This project consists of two main components:

### Backend (Python/FastAPI)
- **AI Chat**: Google Gemini-powered conversational interface with function calling
- **Robot Control**: Manipulation capabilities with gripper and movement control
- **Perception**: Camera streaming and depth sensing using OAK-D depth camera
- **Object Detection**: SAM (Segment Anything Model) for object segmentation

### Frontend (Next.js/React)
- **Chat Interface**: Real-time conversational UI with the robot
- **Camera Stream**: Live video feed from the robot's camera
- **Depth Visualization**: 3D coordinate display for depth sensing
- **Modern UI**: Built with Tailwind CSS and responsive design

## 🚀 Features

### 🤖 AI-Powered Control
- Natural language commands for robot control
- Automatic function calling for camera access, object detection, and manipulation
- Conversational memory and context awareness

### 📹 Vision Capabilities
- Real-time camera streaming from OAK-D depth camera
- Depth sensing and 3D coordinate calculation
- Object detection and segmentation using SAM model
- Point cloud processing and spatial understanding

### 🎛️ Robot Manipulation
- Gripper control (open/close)
- Position control and movement
- Home position navigation
- Object pickup and manipulation

### 💬 Interactive Interface
- Live chat with typing indicators
- Markdown support for rich responses
- Embedded camera streams and depth results
- Responsive design for desktop and mobile

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance web framework
- **Google Gemini AI**: Advanced language model with function calling
- **DepthAI**: OAK-D camera integration for depth sensing
- **Ultralytics SAM**: Object segmentation and detection
- **OpenCV**: Computer vision processing
- **Uvicorn**: ASGI server for production deployment

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **React Markdown**: Rich text rendering
- **WebSockets**: Real-time communication

## 📋 Prerequisites

- Python 3.13+
- Node.js 18+
- OAK-D depth camera (optional for development)
- Google Gemini API key

## 🔧 Installation

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

3. **Set up environment variables:**
   Create a `.env` file in the backend directory:
   ```env
   APIKEY=your_google_gemini_api_key_here
   ```

4. **Download SAM model:**
   The SAM model will auto-download on first run, or you can manually place `sam2.1_b.pt` in the `models/` directory.

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

## 🚀 Running the Application

### Development Mode

1. **Start the backend server:**
   ```bash
   cd backend
   uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the frontend (in a new terminal):**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open your browser:**
   Navigate to `http://localhost:3000`

### Production Mode

1. **Build the frontend:**
   ```bash
   cd frontend
   npm run build
   npm start
   ```

2. **Start the backend:**
   ```bash
   cd backend
   uv run uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## 📖 Usage

### Basic Interaction

1. **Start a conversation:** Type messages in the chat interface
2. **Access camera:** Say "show me the camera" or "what do you see?"
3. **Find objects:** Ask "where is the [object]?" to locate items
4. **Control robot:** Use commands like "open gripper", "close gripper", "go home"
5. **Pick up objects:** Say "pick up the [object]" after locating it

### Available Commands

The AI understands natural language commands for:
- **Camera Control**: "access camera", "show stream", "what do you see?"
- **Object Detection**: "find [object]", "locate [object]", "where is [object]?"
- **Robot Movement**: "go home", "move to position"
- **Gripper Control**: "open gripper", "close gripper", "release object"
- **Object Manipulation**: "pick up [object]", "grab [object]"

### Camera Features

- **Live Streaming**: Real-time video feed from OAK-D camera
- **Depth Sensing**: Click on points to get 3D coordinates
- **Object Segmentation**: AI-powered object detection and masking

## 🔧 Configuration

### Environment Variables

- `APIKEY`: Google Gemini API key (required)

### Camera Configuration

The system uses OAK-D depth camera with:
- RGB camera for color imaging
- Stereo depth for 3D sensing
- Automatic calibration loading
- Configurable resolution and frame rates

### Robot Control

Currently configured for:
- Simulated robot movements (can be extended for real hardware)
- Home position: (0, 0, 0.3) meters
- Gripper states: open/closed
- Coordinate system: millimeters for precision

## 🏗️ Project Structure

```
├── backend/
│   ├── ai/                 # AI chat and tools
│   ├── controls/           # Robot control logic
│   ├── perception/         # Camera and depth processing
│   ├── models/             # ML models (SAM)
│   ├── main.py            # FastAPI application
│   ├── state.py           # Global state management
│   └── pyproject.toml     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js app router
│   │   └── components/    # React components
│   └── package.json       # Node dependencies
└── README.md
```

## 🔍 API Endpoints

### Backend API

- `GET /health` - Health check
- `POST /chat` - Send chat message (streaming response)
- `GET /image/{image_id}` - Retrieve processed images
- `WebSocket /ws/stream` - Camera stream WebSocket

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Troubleshooting

### Common Issues

1. **Camera not found**: Ensure OAK-D camera is connected and powered
2. **API key error**: Check that `APIKEY` environment variable is set
3. **Model download failed**: Check internet connection for SAM model download
4. **Port conflicts**: Ensure ports 3000 (frontend) and 8000 (backend) are available

### Debug Mode

Enable debug logging by setting environment variable:
```bash
DEBUG=1
```

## 🔮 Future Enhancements

- Real robot hardware integration
- Multi-camera support
- Advanced path planning
- Voice commands
- AR/VR interface
- Cloud deployment options

## 📞 Support

For questions or issues, please create an issue in the GitHub repository.
