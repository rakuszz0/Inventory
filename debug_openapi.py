import traceback
from fastapi import FastAPI
from server.main import app  # pastikan ini import app kamu

def test_openapi(app: FastAPI):
    try:
        # generate OpenAPI schema
        openapi_schema = app.openapi()
        print(" OpenAPI schema generated successfully!")
        print(f"Paths found: {list(openapi_schema['paths'].keys())}")
    except Exception as e:
        print("Failed to generate OpenAPI schema!")
        traceback.print_exc()

if __name__ == "__main__":
    test_openapi(app)
