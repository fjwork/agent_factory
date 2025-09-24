from google.cloud import secretmanager

def get_secret(secret_id, project_id, version_id="latest"):
    """
    Fetches a secret from GCP Secret Manager.
    Args:
        secret_id (str): The name of the secret.
        project_id (str): Your GCP project ID.
        version_id (str): The version of the secret (default is "latest").
    Returns:
        str: The secret payload as a string.
    """
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode("UTF-8")
