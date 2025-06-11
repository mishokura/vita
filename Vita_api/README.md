1) install dependencies: pip install -r requirements.txt
2) rename .env.example: mv .env.example .env
3) create db file: type nul > career.db (error message can be ignored)

To run API server:
    uvicorn main:app --reload

To run Tests:
    python __main__test__.py