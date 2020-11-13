import os
import platform
import subprocess
import uuid
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TintSubmission(BaseModel):
    program: str
    tests: str
    verbose: Optional[bool]

    class Config:
        schema_extra = {
            "example": {
                "program": "start: start \naccept: accept \nreject: reject \n\ntransitions:\n- [start, a, q1, _, R]\n- [start, _, reject, _, R]\n- [q1, a, accept, _, R]\n- [q1, _, reject, _, R]",
                "tests": "a b\n",
                "verbose": True,
            }
        }


class TintOutput(BaseModel):
    status: int
    output: str

    class Config:
        schema_extra = {
            "example": {
                "status": 200,
                "output": 'Simulating with "a b".\nstart: a b _\n      ^\nq1: _ b _\n     ^\naccept: _ _ _\n           ^\nAccepted.\n\n1 accepted.\n0 rejected.\n0 errors.\n',
            }
        }


@app.post(
    "/api/one-way-tm",
    description="Runs the turing machine program on the given tests.",
    response_model=TintOutput,
)
async def run_turing_machine(tm: TintSubmission):
    tint_file_name = f"./{str(uuid.uuid4().hex)}.txt"
    tint_file = open(tint_file_name, "w")
    tint_file.write(tm.program)
    tint_file.close()

    test_file_name = f"./{str(uuid.uuid4().hex)}.txt"
    test_file = open(test_file_name, "w")
    test_file.write(tm.tests)
    test_file.close()

    opSys = platform.platform().lower()
    try:
        if opSys.find("linux") >= 0:
            tint_args = [
                "./tint-linux",
                "-m",
                "one-way-tm",
                "-v" if tm.verbose else "",
                tint_file_name,
                test_file_name,
            ]
            tint_args = filter(lambda arg: arg != "", tint_args)

            process = subprocess.run(tint_args, capture_output=True)
            output = process.stdout
            status = 200
        else:
            output = "Something went wrong"
            status = 400
    finally:
        os.remove(tint_file_name)
        os.remove(test_file_name)

    return {"status": status, "output": output}
