from dropbox.files import WriteMode
from dotenv import load_dotenv
import dropbox, os, asyncio
import asyncio
from dropbox.exceptions import ApiError

load_dotenv(".env")


# Initialize Dropbox Client
def get_dropbox_client() -> dropbox.Dropbox:
    return dropbox.Dropbox(
        oauth2_refresh_token=os.getenv("DROPBOX_REFRESH_TOKEN"),
        app_key=os.getenv("DROPBOX_APP_KEY"),
        app_secret=os.getenv("DROPBOX_APP_SECRET"),
    )
dbx = get_dropbox_client()


# Handle File Uploads to Dropbox
from urllib.parse import urlparse, urlunparse


def upload_to_dropbox(file_bytes: bytes, dropbox_path: str) -> str:
    """Upload file to Dropbox and return a cleaned shareable link"""

    dbx.files_upload(file_bytes, dropbox_path, mode=WriteMode("overwrite"))

    shared_link = dbx.sharing_create_shared_link_with_settings(dropbox_path)

    parsed = urlparse(shared_link.url)

    # Rebuild the URL
    cleaned_url = (
        urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                "",  # params
                "",  # query removed
                "",  # fragment
            )
        )
    )

    return cleaned_url


# Handle File Deletes in Dropbox
def delete_from_dropbox(dropbox_path: str) -> None:
    """Delete a file from Dropbox given it's path"""

    dbx.files_delete_v2(dropbox_path)

    return None
