# 🎌 AI Anime Recommender

An intelligent anime recommendation system powered by AI that provides personalized anime suggestions based on user preferences. Built with FastAPI backend and React frontend, featuring conversational AI and vector-based similarity search.

## ✨ Features

- 🤖 **AI-Powered Conversations**: Chat with an AI assistant to get personalized anime recommendations
- 🎯 **Vector-Based Search**: Uses ChromaDB and embeddings for semantic similarity matching
- 📱 **Beautiful UI**: Modern, responsive chat interface built with React and Tailwind CSS
- 🎨 **Anime Cards**: Displays recommended anime with images from MyAnimeList (MAL) API
- 💾 **Session Management**: Maintains conversation context across interactions
- 🚀 **Production Ready**: Dockerized for easy deployment

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangChain & LangGraph** - AI orchestration and workflow management
- **Groq** - Fast LLM inference
- **ChromaDB** - Vector database for similarity search
- **HuggingFace** - Sentence transformers for embeddings
- **Pandas** - Data processing
- **Uvicorn** - ASGI server

### Frontend
- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Jikan API** - MyAnimeList data

## 📁 Project Structure

```
AI Anime Recommender/
├── Backend/
│   ├── app/
│   │   ├── controller/       # API endpoints
│   │   ├── model/            # Pydantic models
│   │   └── service/          # Business logic
│   ├── config/               # Configuration files
│   ├── src/                  # Core modules
│   │   ├── workflow.py       # LangGraph workflow
│   │   ├── recommender.py    # Recommendation engine
│   │   └── vector_store.py   # Vector database operations
│   ├── data/                 # Anime dataset
│   ├── pipeline/             # Pipeline builders
│   ├── tests/                # Test files
│   ├── main.py               # FastAPI application
│   └── Dockerfile            # Backend container
│
├── Frontend/
│   └── anime_recommender/
│       ├── src/
│       │   ├── components/   # React components
│       │   ├── controllers/  # Business logic
│       │   ├── services/     # API services
│       │   └── api/          # HTTP client
│       ├── public/           # Static assets
│       └── Dockerfile        # Frontend container
│
└── README.md                 # This file
```

## 📋 Prerequisites

- **Python 3.12+**
- **Node.js 20+** and npm
- **Docker** (optional, for containerized deployment)
- **Groq API Key** - Get from [console.groq.com](https://console.groq.com)

## 🚀 Installation

### Backend Setup

1. **Navigate to Backend directory:**
   ```bash
   cd Backend
   ```

2. **Install dependencies:**
   ```bash
   # Using uv (recommended)
   pip install uv
   uv sync
   
   # Or using pip
   pip install -e .
   ```

3. **Set up environment variables:**
   Create a `.env` file in the Backend directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Run the backend:**
   ```bash
   python main.py
   ```
   Backend will start on `http://localhost:8000`

### Frontend Setup

1. **Navigate to Frontend directory:**
   ```bash
   cd Frontend/anime_recommender
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```
   Frontend will start on `http://localhost:5173`

## 🐳 Docker Deployment

### Backend

1. **Build the image:**
   ```bash
   cd Backend
   docker build -t anime_recommender:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 \
     -e GROQ_API_KEY=your_groq_api_key_here \
     anime_recommender:latest
   ```

### Frontend

1. **Build the image:**
   ```bash
   cd Frontend/anime_recommender
   docker build -t anime_recommender_frontend:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -p 3000:80 anime_recommender_frontend:latest
   ```

### Docker Compose (Recommended)

Create a `docker-compose.yml` in the root directory:

```yaml
version: '3.8'

services:
  backend:
    build: ./Backend
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./Backend/data:/app/data
      - ./Backend/VectorDataBase:/app/VectorDataBase

  frontend:
    build: ./Frontend/anime_recommender
    ports:
      - "3000:80"
    depends_on:
      - backend
```

Run with:
```bash
docker-compose up --build
```

## 📡 API Endpoints

### POST `/chat/recommender`

Get anime recommendations based on user query.

**Request:**
```json
{
  "session_id": "session_123456",
  "query": "I want some horror anime"
}
```

**Response:**
```json
{
  "session_id": "session_123456",
  "query": "I want some horror anime",
  "assistant_message": {
    "conversation": "Here are some horror anime recommendations...",
    "anime": [
      {
        "anime_name": "Another",
        "about_anime": "A cursed class experiences a series of gruesome deaths..."
      }
    ],
    "suggestion_for_next_question": "Could you tell me which genres you enjoy?"
  }
}
```

## 🎮 Usage

1. **Start the backend server** (if not using Docker)
2. **Start the frontend server** (if not using Docker)
3. **Open your browser** and navigate to `http://localhost:5173`
4. **Start chatting** with the AI about what kind of anime you're looking for
5. **View recommendations** displayed as beautiful cards with images and descriptions

## 🔧 Configuration

### Backend Configuration

Edit `Backend/config/llm.py` to modify LLM settings:
- Model name
- Temperature
- Max retries

Edit `Backend/config/prompts.py` to customize AI prompts.

### Frontend Configuration

Update `Frontend/anime_recommender/src/services/BackendService.ts` to change the API URL if needed.

## 🧪 Testing

### Backend Tests

```bash
cd Backend
pytest
```

### Frontend Tests

```bash
cd Frontend/anime_recommender
npm test
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- **Groq** for fast LLM inference
- **LangChain** for AI orchestration
- **Jikan API** for MyAnimeList data
- **ChromaDB** for vector search capabilities

## 📧 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

Made with ❤️ by TheCoder30ec4

