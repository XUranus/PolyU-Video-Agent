# Server Module —

## Environment Setup
 - **Conda** required

```bash
conda env create -f environment.yml
conda activate PolyU-Video-Agent
```

## Getting Start
```bash
python server.py runserver
```

## API Routes

- **`GET /health/`**  
  Returns: `{"status": "ok", "service": "PolyU Video Agent"}`

- **`POST /api/upload/`**  
  Upload a video (placeholder).  
  Returns: `{"message": "...", "video_id": "temp_id_12345"}` (202 Accepted)

- **`POST /api/query/`**  
  Query a video by `video_id` and natural language `query`.  
  Example request:
  ```json
  {"video_id": "lec_01", "query": "When was GBM explained?"}
  ```
  Returns placeholder answer with mock timestamps.

> All logic is currently stubbed (`TODO`). CSRF is disabled for development.  
> Run with: `python server.py runserver`

