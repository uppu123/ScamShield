$job = Start-Job { python -m backend.app }
Start-Sleep -Seconds 2
streamlit run frontend/app.py
Stop-Job $job -ErrorAction SilentlyContinue
