from google.cloud import bigquery

# === Configuration ===
project_identifier = "Connect"          # 🔁 replace with your project ID
dataset_identifier = "tablero_1"      # choose a short, clear name
dataset_region = "us-central1"                # example: "us", "europe-west1"

# === Create client ===
client = bigquery.Client(project=project_identifier)

# === Define dataset ===
dataset_reference = bigquery.Dataset(f"{project_identifier}.{dataset_identifier}")
dataset_reference.location = dataset_region

# === Create dataset if not exists ===
try:
    created_dataset = client.create_dataset(dataset_reference, exists_ok=True)
    print(f"[DEBUG] Dataset created or already exists: {created_dataset.full_dataset_id}")
except Exception as error:
    print(f"[DEBUG] Error while creating dataset: {error}")
