# Image Processing API

A FastAPI application that processes images from URLs provided via CSV files and stores the results in a PostgreSQL database.

## Prerequisites

- Python 3.9+
- PostgreSQL

## Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your_username/your_repository.git
   cd your_repository
   ```

2. **Create and Activate a Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: `venv\Scripts\activate`
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure PostgreSQL:**
   - Create a database:
     ```sql
     CREATE DATABASE image_processing;
     ```
   - Set `DATABASE_URL` in `main.py`:
     ```python
     DATABASE_URL = "postgresql://postgres:your_password@localhost:5432/image_processing"
     ```

5. **Run the Server:**
   ```bash
   uvicorn main:app --reload
   ```

## Usage

1. **Upload CSV:**
   ```bash
   curl -X POST "http://127.0.0.1:8000/upload/" -F "file=@your_file.csv"
   ```

2. **Check Status:**
   ```bash
   curl "http://127.0.0.1:8000/status/{request_id}"
   ```

## Notes

- Processed images are saved in the `static/` directory.
- Prereq is to ensure PostgreSQL is running and credentials are correct
