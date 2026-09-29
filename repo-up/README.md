# Repo-Up

Repo-Up is a web-based tool designed to analyze uploaded codebase repositories (via ZIP files) and provide insights about them, such as detecting the languages, frameworks, and project size (file/folder counts).

## Features

- **Project Upload**: Easily upload your project as a `.zip` file for analysis.
- **Language Detection**: Automatically detects programming languages used in the project (e.g., Python, JavaScript, TypeScript).
- **Framework Detection**: Identifies popular frameworks within your codebase:
  - **Node.js**: React, Next.js, Express, NestJS
  - **Python**: Django, Flask, FastAPI
- **Project Statistics**: Quickly view the total file and folder counts, ignoring heavy directories like `node_modules` or `venv`.

## Tech Stack

### Frontend
- **React 19** with **TypeScript** and **Vite**
- **Tailwind CSS** for a cohesive, dark-themed design system
- **Framer Motion** for smooth animations and transitions
- **Lucide React** for UI icons
- **Recharts** for data visualization

### Backend
- **Python (FastAPI / Flask)** serving API endpoints
- Custom Python analysis utilities to extract metadata and detect frameworks via pattern matching and configuration files (`package.json`, `requirements.txt`, etc.).

## Getting Started

### Prerequisites
- Node.js & npm (for the frontend)
- Python 3.8+ (for the backend)

### Installation

1. **Clone the repository** (or download the source):
   ```bash
   git clone <repository-url>
   cd repo-up
   ```

2. **Frontend Setup**:
   ```bash
   # Install dependencies
   npm install

   # Start the development server
   npm run dev
   ```

3. **Backend Setup**:
   ```bash
   cd backend
   
   # Create a virtual environment and activate it
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install backend dependencies (make sure to create requirements.txt if needed)
   pip install -r requirements.txt
   
   # Start the backend server (Example for FastAPI)
   uvicorn main:app --reload --port 8000
   ```

## Usage
1. Open the application in your browser (usually `http://localhost:5173`).
2. On the Landing screen, click to upload a `.zip` file containing your codebase.
3. Wait for the analysis to complete on the Progress screen.
4. View your project insights on the Results screen!
