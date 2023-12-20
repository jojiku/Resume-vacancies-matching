from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

from app.config import min_max_lens, min_len, max_len


class ResumeAddingRequest(BaseModel):
    """
    Represents a request to add a resume.

    Fields:
    - gend_age: Represents the gender and age 
    of the worker. Optional field with a default value of None.
    - salary: Represents the desired salary 
    of the worker. Optional field with a default value of None.
    - job_title: Represents the job title 
    the worker is looking for. Required field.
    - city: Represents the city of residence and readiness 
    for business trips. Optional field with a default value of None.
    - employment: Represents the desired employment type 
    (e.g., full-time, part-time). Optional field with a default value of None.
    - schedule: Represents the desired work schedule 
    (e.g., full day, part day). Optional field with a default value of None.
    - experience: Represents the worker's experience. Required field.
    - last_wp: Represents the last employer of 
    the worker. Optional field with a default value of None.
    - last_jt: Represents the last job title of 
    the worker. Optional field with a default value of None.
    - edu: Represents the worker's education. Required field.
    - upd_date: Represents the last resume update. 
    Optional field with a default value of None.
    - auto: Represents if the worker owns a car. 
    Optional field with a default value of None.
    """

    gend_age: str | None = Field(
        default=None,
        title="Gender and age",
    )
    salary: str | None = Field(
        default=None,
        title="Desired salary",
    )
    job_title: str = Field(
        default=None,
        title="Job title the worker is looking for",
    )
    city: str | None = Field(
        default=None,
        title="The city of residence and readiness for business trips",
    )
    employment: str | None = Field(
        default=None,
        title="Desired employment (full, partly...)",
    )
    schedule: str | None = Field(
        default=None,
        title="Desired schedule (full day...)",
    )
    experience: str = Field(
        default=None,
        title="Worker's experience",
    )
    last_wp: str | None = Field(
        default=None,
        title="The last employer",
    )
    last_jt: str | None = Field(
        default=None,
        title="The last job title",
    )
    edu: str = Field(
        default=None,
        title="Worker's education",
    )
    upd_date: str | None = Field(
        default=None,
        title="Last resume update",
    )
    auto: str | None = Field(
        default=None,
        title="If worker owns a car",
    )

    @model_validator(mode="before")
    @classmethod
    def check_field_len(cls, values):
        """
        Validates the length of each field in the request.

        Args:
        - values: A dictionary containing the field names and their values.

        Raises:
        - AssertionError: If the length of any field 
        is not within the specified bounds.

        Returns:
        - The input values dictionary.
        """
        for k, v in values.items():
            _min, _max = min_max_lens.get(k, (min_len, max_len))
            assert (
                _min <= len(v) <= _max
            ), f"'{k}' length must be in bounds ({_min}, {_max})"

        return values


class VacancyAddingRequest(BaseModel):
    """
    Represents a request to add a job vacancy.

    Fields:
    - employer: The name of the employer. Required field.
    - vac_title: The title of the vacancy. 
    Optional field with a default value of None.
    - sal_from: The starting salary for the vacancy. 
    Optional field with a default value of None.
    - sal_to: The ending salary for the vacancy. 
    Optional field with a default value of None.
    - req_exp: The experience required for the job. Required field.
    - sch_type: The job schedule type (e.g., office, remote). 
    Optional field with a default value of None.
    - keywords: The keywords related to the job. 
    Optional field with a default value of None.
    - descr: The description of the job. Required field.
    - area: The location of the employer. 
    Optional field with a default value of None.
    - key_req: The key requirements for the job. Required field.
    - spec: The specialization of the job. Required field.
    - tags: The tags associated with the job. 
    Optional field with a default value of None.
    - publ_date: The date of job publishing. 
    Optional field with a default value of None.
    """

    employer: str = Field(
        default=None,
        title="The name of the employer",
    )
    vac_title: str | None = Field(
        default=None,
        title="The vacancy title",
    )
    sal_from: str | None = Field(
        default=None,
        title="Starting from salary",
    )
    sal_to: str | None = Field(
        default=None,
        title="Ending to salary",
    )
    req_exp: str = Field(
        default=None,
        title="The experience required for job",
    )
    sch_type: str | None = Field(
        default=None,
        title="Job schedule type (office, remote...)",
    )
    keywords: str | None = Field(
        default=None,
        title="Job keywords",
    )
    descr: str = Field(
        default=None,
        title="Job description",
    )
    area: str | None = Field(
        default=None,
        title="Employer location",
    )
    key_req: str = Field(
        default=None,
        title="Key requirements for the job",
    )
    spec: str = Field(
        default=None,
        title="Specialization",
    )
    tags: str | None = Field(
        default=None,
        title="Job tags",
    )
    publ_date: str | None = Field(
        default=None,
        title="Date of job publishing",
    )

    @model_validator(mode="before")
    @classmethod
    def check_field_len(cls, values):
        """
        Validates the length of each field in the request.

        Args:
        - values: A dictionary containing the field names and their values.

        Raises:
        - AssertionError: If the length of any field 
        is not within the specified bounds.

        Returns:
        - The input values dictionary.
        """
        for k, v in values.items():
            _min, _max = min_max_lens.get(k, (min_len, max_len))
            assert (
                _min <= len(v) <= _max
            ), f"'{k}' length must be in bounds ({_min}, {_max})"

        return values
