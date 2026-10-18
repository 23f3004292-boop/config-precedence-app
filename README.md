# 12-Factor Config Precedence API

## Local run
```bash
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/effective-config`.

Try overrides:
`http://127.0.0.1:8000/effective-config?set=port=9000&set=debug=true`

## Render deployment
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Add these Render environment variables:
  - `APP_DEBUG=false`
  - `APP_LOG_LEVEL=error`

The platform-provided `PORT` variable is used for binding the web server; the `port` field in `/effective-config` reports the merged application configuration.
