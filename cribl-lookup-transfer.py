import requests
import os
import json
from pathlib import Path
import argparse
import configparser
import gzip

def get_bearer_token(client_id, client_secret):
    if not client_id or not client_secret:
        raise ValueError("CRIBL_CLIENT_ID and CRIBL_CLIENT_SECRET must be set as environment variables")
    
    url = "https://login.cribl.cloud/oauth/token"
    headers = {"Content-Type": "application/json"}
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": "https://api.cribl.cloud"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Failed to obtain bearer token: {e}")
        return None

def check_lookup_exists(token, organization_id, worker_group, lookup_filename):
    url = f"https://app.cribl.cloud/organizations/{organization_id}/workspaces/main/app/api/v1/m/{worker_group}/system/lookups/{lookup_filename}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if not data or "items" not in data or not data["items"]:
            return False
        return any(item.get("id") == lookup_filename for item in data["items"])
    
    except requests.exceptions.RequestException as e:
        print(f"Failed to check if lookup '{lookup_filename}' exists in {worker_group}: {e}")
        return False

def download_lookup_file(token, organization_id, worker_group, lookup_filename, local_filename):
    url = f"https://app.cribl.cloud/organizations/{organization_id}/workspaces/main/app/api/v1/m/{worker_group}/system/lookups/{lookup_filename}/content?raw=1"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        with open(local_filename, 'wb') as f:
            f.write(response.content)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to download '{lookup_filename}' from {worker_group}: {e}")
        return False

def upload_lookup_file(token, organization_id, worker_group, lookup_filename):
    url = f"https://app.cribl.cloud/organizations/{organization_id}/workspaces/main/app/api/v1/m/{worker_group}/system/lookups?filename={lookup_filename}"
    content_type = "text/csv" if lookup_filename.endswith('.csv') else "application/gzip"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-type": content_type,
        "accept": "application/json"
    }
    
    try:
        # Open file in appropriate mode based on extension
        open_func = gzip.open if lookup_filename.endswith('.gz') else open
        mode = 'rb'

        with open_func(lookup_filename, mode) as f:
            response = requests.put(url, headers=headers, data=f)
        response.raise_for_status()
        
        response_data = response.json()

        temp_filename = response_data.get("filename")
        
        if not temp_filename:
            print(f"Upload response missing 'filename' or 'version': {response_data}")
            return None
        if not temp_filename.startswith(lookup_filename.split('.')[0]):  # Check base filename
            print(f"Unexpected temporary filename '{temp_filename}' in response: {response_data}")
            return None
        
        return temp_filename
    except requests.exceptions.RequestException as e:
        print(f"Failed to upload '{lookup_filename}' to {worker_group}: {e}")
        return None

def create_lookup(token, organization_id, worker_group, lookup_filename, temp_filename):
    url = f"https://app.cribl.cloud/organizations/{organization_id}/workspaces/main/app/api/v1/m/{worker_group}/system/lookups"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "id": lookup_filename,
        "fileInfo": { "filename": temp_filename }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Created new lookup '{lookup_filename}' in {worker_group}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to create lookup '{lookup_filename}' in {worker_group}: {e}")
        return False

def update_lookup(token, organization_id, worker_group, lookup_filename, temp_filename):
    url = f"https://app.cribl.cloud/organizations/{organization_id}/workspaces/main/app/api/v1/m/{worker_group}/system/lookups/{lookup_filename}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    payload = {
        "id": lookup_filename,
        "fileInfo": {"filename": temp_filename}
    }
    
    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Updated existing lookup '{lookup_filename}' in {worker_group}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to update lookup '{lookup_filename}' in {worker_group}: {e}")
        return False

def commit_changes(token, organization_id, worker_group, lookup_filename):
    url = f"https://app.cribl.cloud/organizations/{organization_id}/workspaces/main/app/api/v1/m/{worker_group}/version/commit"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "message": "Automated lookup file update",
        "group": worker_group,
        "files": [
            f"groups/{worker_group}/data/lookups/{lookup_filename}",
            f"groups/{worker_group}/data/lookups/{Path(lookup_filename).with_suffix('.yml')}"
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()

        commit_id = response_data["items"][0].get("commit")

        if not commit_id:
            print(f"Commit response missing 'commit' ID: {response.json()}")
            return None
        return commit_id
    except requests.exceptions.RequestException as e:
        print(f"Failed to commit changes for '{lookup_filename}' in {worker_group}: {e}")
        return None

def deploy_changes(token, organization_id, worker_group, commit_id):
    url = f"https://app.cribl.cloud/organizations/{organization_id}/workspaces/main/app/api/v1/master/groups/{worker_group}/deploy"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    payload = {"version": commit_id}
    
    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to deploy changes to {worker_group}: {e}")
        return False

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Transfer lookup files between Cribl worker groups",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--config",
        type=Path,
        default="config.ini",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--client-id",
        help="Cribl client ID (overrides config file)"
    )
    parser.add_argument(
        "--client-secret",
        help="Cribl client secret (overrides config file)"
    )
    parser.add_argument(
        "--organization-id",
        help="Cribl.cloud organization ID (overrides config file)"
    )
    parser.add_argument(
        "--lookup-filename",
        help="Lookup file name (overrides config file)"
    )
    parser.add_argument(
        "--source-group",
        help="Source worker group (overrides config file)"
    )
    parser.add_argument(
        "--target-group",
        help="Target worker group (overrides config file)"
    )

    return parser.parse_args()

def load_config(config_path):
    config = configparser.ConfigParser()
    defaults = {
        "cribl": {
            "client_id": "",
            "client_secret": "",
            "organization_id": "",
            "lookup_filename": "",
            "source_worker_group": "default_search",
            "target_worker_group": "default"
        }
    }
    config.read_dict(defaults)

    if config_path.exists():
        config.read(config_path)

    return config["cribl"]



if __name__ == "__main__":
    try:
        # 1. Parse command line arguments
        args = parse_arguments()

        # 2. Load configuration
        config = load_config(args.config)

        # 3. Override config with command line args if provided
        client_id = args.client_id or config["client_id"]
        client_secret = args.client_secret or config["client_secret"]
        organization_id = args.organization_id or config["organization_id"]
        lookup_filename = args.lookup_filename or config["lookup_filename"]
        source_worker_group = args.source_group or config["source_worker_group"]
        target_worker_group = args.target_group or config["target_worker_group"]
        local_filename = lookup_filename

        # 4. Get the token
        token = get_bearer_token(client_id, client_secret)
        if not token:
            exit(1)
        print(f"Bearer token obtained: {token[:10]}...")


        # 5. Check for the file on the source worker group
        if not check_lookup_exists(token, organization_id, source_worker_group, lookup_filename):
            print(f"Lookup file '{lookup_filename}' does not exist in {source_worker_group}")
            exit(1)

        # 6. Download the file if it exists
        if not download_lookup_file(token, organization_id, source_worker_group, lookup_filename, local_filename):
            exit(1)
        print(f"Successfully downloaded '{lookup_filename}' from {source_worker_group} to '{local_filename}'")

        # 7. Upload the file to the target worker group and get the temp filename
        temp_filename = upload_lookup_file(token, organization_id, target_worker_group, lookup_filename)
        if not temp_filename:
            exit(1)
        print(f"Uploaded '{lookup_filename}' to {target_worker_group}, temporary filename: '{temp_filename}'")

        # 8. Check for the file on the target worker group and create/update accordingly
        if check_lookup_exists(token, organization_id, target_worker_group, lookup_filename):
            print("Does exist on target.")
            if not update_lookup(token, organization_id, target_worker_group, lookup_filename, temp_filename):
                exit(1)
        else:
            print("Does not exist on target.")
            if not create_lookup(token, organization_id, target_worker_group, lookup_filename, temp_filename):
                exit(1)

        # 9. Commit the changes
        commit_id = commit_changes(token, organization_id, target_worker_group, lookup_filename)
        if not commit_id:
            exit(1)
        print(f"Changes committed with ID: {commit_id}")

        # 10. Deploy the changes
        if not deploy_changes(token, organization_id, target_worker_group, commit_id):
            exit(1)
        print(f"Successfully deployed changes to {target_worker_group}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)