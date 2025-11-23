import logging

import ray.data
import s3fs

# Enable debug logging for PyArrow and Ray
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("pyarrow").setLevel(logging.DEBUG)
logging.getLogger("ray").setLevel(logging.DEBUG)

# Test MinIO connectivity first
print("Testing MinIO connectivity...")
import requests

try:
    # Test if MinIO is reachable
    response = requests.get(
        "https://minio-api.storage.internal.opencloudhub.org", verify=False
    )
    print(f"✓ MinIO endpoint is reachable: {response.status_code}")
except Exception as e:
    print(f"❌ Cannot reach MinIO: {e}")

# Try creating S3 filesystem with explicit SSL verification disabled
try:
    # For PyArrow, we need to handle SSL differently
    # Since you're in dev container with host network and MinIO in Minikube,
    # you might need to use the Minikube IP directly

    s3_fs = s3fs.S3FileSystem(
        anon=False,
        endpoint_url="https://minio-api.storage.internal.opencloudhub.org",
        key="admin",
        secret="12345678",
        client_kwargs={
            "verify": False,  # Disable SSL verification for self-signed certs
        },
    )

    print("\n✓ S3 filesystem created")

    # Try reading the file
    print("\nTrying to read file...")
    ds = ray.data.read_text(
        "s3://dvcstore/files/md5/08/25611024168fef9b4469750163f003", filesystem=s3_fs
    )

    print(f"✓ Dataset created: {ds.count()} rows")
    ds.show(5)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback

    traceback.print_exc()
