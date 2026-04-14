# Computer Vision Panorama Stitching Pipeline

A real-time, step-by-step image stitching pipeline built with **OpenCV**, **FastAPI**, and **Next.js**. This application takes overlapping images and elegantly reconstructs a seamless panorama while visualizing the underlying Computer Vision algorithms (Harris Corners, SIFT, RANSAC) in the browser.

## Features

- **Harris Corner Detection**: Identifies local distinct features and corners.
- **SIFT Feature Matching**: Matches scale-invariant features across images using BFMatcher and Lowe's ratio test.
- **Robust RANSAC Homography**: Calculates the optimal perspective transformation, automatically rejecting degenerate geometry and outliers.
- **Distance-Weighted Alpha Blending**: Warps images and dynamically blends overlapping regions to hide seams.
- **Real-Time Visualization**: Utilizes Server-Sent Events (SSE) to stream the OpenCV processing steps to the frontend, providing a live look at the algorithm's progress.

## Tech Stack

- **Backend**: Python, FastAPI, OpenCV, NumPy
- **Frontend**: Next.js, React, Tailwind CSS
- **Communication**: SSE (Server-Sent Events) for real-time pipeline streaming

## Project Structure

```text
cv-project/
├── backend/            # FastAPI server & OpenCV pipeline logic
│   ├── main.py         # App entry point
│   ├── routers/        # API endpoints (SSE streaming)
│   └── services/       # Core CV algorithms (panorama.py)
├── frontend/           # Next.js user interface
└── test/               # Python smoke tests and validation utils
```

## Getting Started

### Prerequisites
- Node.js (v18+)
- Python (3.10+)

### 1. Start the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or `.\venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```
The backend API will run on `http://127.0.0.1:8000`.

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:3000` in your web browser. 


