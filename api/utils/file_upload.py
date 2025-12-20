from dropbox.files import WriteMode
from dotenv import load_dotenv
import dropbox, os, asyncio
import asyncio
from dropbox.exceptions import ApiError

load_dotenv(".env")

DROPBOX_KEY = os.getenv("DROPBOX_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_KEY)


# Handle File Uploads to Dropbox
def upload_to_dropbox(file_bytes: str, dropbox_path: str) -> str:
    """Upload file to dropbox and return a shareable link"""

    dbx.files_upload(file_bytes, dropbox_path, mode=WriteMode("overwrite"))

    shared_link = dbx.sharing_create_shared_link_with_settings(dropbox_path)
    return shared_link.url.replace("?dl=0", "?raw=1")


async def upload_to_dropbox_async(file_bytes: bytes, dropbox_path: str) -> str:
    """
    Asynchronously upload a file to Dropbox and return a shareable raw link.
    Safe for retries and duplicate uploads.
    """

    loop = asyncio.get_running_loop()

    def _upload_and_share() -> str:
        # 1️⃣ Upload (idempotent)
        dbx.files_upload(
            file_bytes,
            dropbox_path,
            mode=WriteMode("overwrite"),
            mute=True,
        )

        # 2️⃣ Try to create shared link
        try:
            shared_link = dbx.sharing_create_shared_link_with_settings(dropbox_path)
            return shared_link.url.replace("?dl=0", "?raw=1")

        # 3️⃣ If link already exists → reuse it
        except ApiError as e:
            if e.error.is_shared_link_already_exists():
                links = dbx.sharing_list_shared_links(path=dropbox_path).links
                if links:
                    return links[0].url.replace("?dl=0", "?raw=1")

            raise

    return await loop.run_in_executor(None, _upload_and_share)


# Handle File Deletes in Dropbox
def delete_from_dropbox(dropbox_path: str) -> None:
    """Delete a file from Dropbox given it's path"""
    
    dbx.files_delete_v2(dropbox_path)
    
    return None
