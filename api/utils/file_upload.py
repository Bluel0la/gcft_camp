from dropbox.files import WriteMode
from dotenv import load_dotenv
import dropbox, os

load_dotenv(".env")

DROPBOX_KEY = os.getenv("DROPBOX_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_KEY)

# Handle File Uploads to Dropbox
def upload_to_dropbox(file_bytes: str, dropbox_path: str) -> str:
    """Upload file to dropbox and return a shareable link"""
    
    dbx.files_upload(file_bytes, dropbox_path, mode=WriteMode("overwrite"))
    
    shared_link = dbx.sharing_create_shared_link_with_settings(dropbox_path)
    return shared_link.url.replace("?dl=0", "?raw=1")

# Handle File Deletes in Dropbox
def delete_from_dropbox(dropbox_path: str) -> None:
    """Delete a file from Dropbox given it's path"""
    
    dbx.files_delete_v2(dropbox_path)
    
    return None
