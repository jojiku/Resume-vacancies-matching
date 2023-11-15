from pydantic import BaseModel


class DownloadingRequest(BaseModel):
    """Contract for downloading request from user
    with specified links list and task_name
    """

    links_list: list
