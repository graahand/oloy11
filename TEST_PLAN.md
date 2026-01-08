# Test Plan

## Pre-Requisites
-   [ ] Install `pytest`, `httpx` (for TestClient).
-   [ ] Setup test database (SQLite in-memory or file).

## Unit Tests

### 1. Model Manager (Singleton)
-   **Test:** Ensure `ModelManager` returns the same instance.
-   **Test:** Ensure model loads correctly (mock `ultralytics.YOLO` if possible, or use a small dummy model).

### 2. Image Preprocessing
-   **Test:** Resize function returns correct dimensions.
-   **Test:** Invalid image format raises error.

### 3. Auth Handler
-   **Test:** Password hashing is consistent (verify matches hash).
-   **Test:** Token generation returns valid JWT.

## Integration Tests (API Endpoints)

### 1. Image Upload & Inference
-   **Test:** `POST /predict/image` with valid image file.
-   **Test:** `POST /predict/image` with valid URL.
-   **Test:** `POST /predict/image` with invalid file type.
-   **Test:** Check response structure (contains `boxes`, `masks` if applicable).
-   **Test:** Verify arguments (`conf`, `iou`) affect results (mocking might be needed for determinism).

### 2. Video Analysis
-   **Test:** `POST /predict/video` with small video file.
-   **Test:** Check response contains frame-by-frame or summary analysis.

### 3. User Auth & History
-   **Test:** `POST /register` creates user.
-   **Test:** `POST /login` returns token.
-   **Test:** Access protected route without token (401).
-   **Test:** `GET /history` returns record after an inference task.
