from pydantic import BaseModel, Field

class MedicineInfo(BaseModel):
    name: str = Field(..., description="name of the medicine",
                      alias="ten")

class PatientRecord(BaseModel):
    record_id: str = Field(..., description="ID")
    # TODO
    list_of_medicine: list[MedicineInfo]
    