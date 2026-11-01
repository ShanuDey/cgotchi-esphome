"""Control page for the display simulator: a small FastAPI app that edits settings.txt.

    config         paths
    meta           what can be set (plain data: pages, expressions, voices, themes, fps range)
    face_headers   reads that data from the face component's headers (no second copy)
    models         the request and response models of the API
    settings_file  the settings.txt reader and writer
    deps           what the routes depend on
    routes         the API endpoints
    app            builds the FastAPI app
    launcher       starts, stops and restarts the simulator itself (in WSL on Windows)
"""
