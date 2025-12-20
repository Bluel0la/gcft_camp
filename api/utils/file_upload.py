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
def upload_to_dropbox(file_bytes: bytes, dropbox_path: str) -> str:
    """Upload file to Dropbox and return a shareable raw link"""

    dbx.files_upload(
        file_bytes,
        dropbox_path,
        mode=WriteMode.overwrite,
        mute=True,
    )

    try:
        link = dbx.sharing_create_shared_link_with_settings(dropbox_path)
        url = link.url
    except ApiError as e:
        if e.error.is_shared_link_already_exists():
            links = dbx.sharing_list_shared_links(path=dropbox_path).links
            if not links:
                raise
            url = links[0].url
        else:
            raise

    return url.replace("?dl=0", "?raw=1")


async def upload_to_dropbox_async(file_bytes: bytes, dropbox_path: str) -> str:
    """
    Asynchronously upload a file to Dropbox and return a shareable raw link.
    Safe for retries and duplicate uploads.
    """

    loop = asyncio.get_running_loop()

    def _upload_and_share() -> str:
        return upload_to_dropbox(file_bytes, dropbox_path)

    return await loop.run_in_executor(None, _upload_and_share)


# Handle File Deletes in Dropbox
def delete_from_dropbox(dropbox_path: str) -> None:
    dbx.files_delete_v2(dropbox_path)