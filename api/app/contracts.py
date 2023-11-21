from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ValidationInfo,
)


class YtDownloadRequest(BaseModel):
    """
    Represents a request to download a YouTube video.

    Fields:
    - yt_link: A string field representing the YouTube video link.
    - time_intervals: A list field containing pairs of time intervals (from-to)
    of the video in '%H:%M:%S' format. It is optional and can be set to `None`.
    - target_fps: An integer field representing the target FPS of the video.
    It has a default value of 10 and must be within the range of 5 to 30.
    """

    yt_link: str = Field(title="YouTube video link")
    time_intervals: list | None = Field(
        default=None,
        title="List with pairs of time intervals (from-to) of video in '%H:%M:%S' format",
    )
    target_fps: int | None = Field(
        default=10,
        title="Target FPS of the video (from 5 to 30)",
    )

    @field_validator("time_intervals")
    @classmethod
    def check_timestamps(cls, v: str, info: ValidationInfo) -> str:
        """
        Validates the time intervals of the video.

        Args:
        - v: The value of the time_intervals field.
        - info: ValidationInfo object containing information about the field being validated.

        Returns:
        - The validated value of the time_intervals field.

        Raises:
        - ValueError: If the time intervals are not in the correct format or if the start timestamp is greater than or equal to the ending timestamp.
        """
        if not v:
            return v

        for timestamp_pair in v:
            if len(timestamp_pair) != 2:
                raise ValueError("Every interval should be in pair")

            try:
                st = datetime.strptime(timestamp_pair[0], "%H:%M:%S")
                to = datetime.strptime(timestamp_pair[1], "%H:%M:%S")

                assert to > st
            except Exception as e:
                if isinstance(e, AssertionError):
                    raise ValueError("Start timestamp must be smaller than ending")
                else:
                    raise ValueError(
                        f"Some values of {info.field_name} are not in '%H:%M:%S' format"
                    )

        return v

    @field_validator("target_fps")
    @classmethod
    def check_target_fps(cls, v: str) -> str:
        """
        Validates the target FPS of the video.

        Args:
        - v: The value of the target_fps field.

        Returns:
        - The validated value of the target_fps field.

        Raises:
        - ValueError: If the target FPS is not within the range of 5 to 30 (inclusive).
        """
        if not 5 <= v <= 30:
            raise ValueError(f"Target FPS value must be in range 5-30 (inclusive)")

        return v
