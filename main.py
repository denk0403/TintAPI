import os
import platform
import subprocess
import uuid
from enum import Enum
from subprocess import TimeoutExpired
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


class MachineType(Enum):
    DFA = "dfa"
    ONE_WAY_TM = "one-way-tm"
    TWO_WAY_TM = "two-way-tm"


async def run_machine(ts: TintSubmission, machine: MachineType):
    tint_file_name = f"./{str(uuid.uuid4().hex)}.txt"
    tint_file = open(tint_file_name, "w")
    tint_file.write(ts.program)
    tint_file.close()

    test_file_name = f"./{str(uuid.uuid4().hex)}.txt"
    test_file = open(test_file_name, "w")
    test_file.write(ts.tests)
    test_file.close()

    opSys = platform.platform().lower()
    try:
        if opSys.find("linux") >= 0:
            tint_args = [
                "./tint-linux",
                "-m",
                machine.value,
                "-v" if ts.verbose else "",
                tint_file_name,
                test_file_name,
            ]
            tint_args = filter(lambda arg: arg != "", tint_args)

            process = subprocess.run(tint_args, capture_output=True, timeout=5)
            output = process.stdout
            status = 200
        else:
            output = "Error: Something went wrong"
            status = 400
    except TimeoutExpired:
        output = "Error: Program took too long or encountered an infinite loop"
        status = 400
    finally:
        os.remove(tint_file_name)
        os.remove(test_file_name)

    return {"status": status, "output": output}


@app.post(
    "/api/one-way-tm",
    description="Runs a one-way turing machine program on the given tests.",
    response_model=TintOutput,
)
async def run_one_way_turing_machine(tm: TintSubmission) -> TintOutput:
    return await run_machine(tm, MachineType.ONE_WAY_TM)


@app.post(
    "/api/two-way-tm",
    description="Runs a two-way turing machine program on the given tests.",
    response_model=TintOutput,
)
async def run_two_way_turing_machine(tm: TintSubmission) -> TintOutput:
    return await run_machine(tm, MachineType.TWO_WAY_TM)


@app.post(
    "/api/dfa",
    description="Runs a dfa program on the given tests.",
    response_model=TintOutput,
)
async def run_dfa(tm: TintSubmission) -> TintOutput:
    return await run_machine(tm, MachineType.DFA)


class StartOutput(BaseModel):
    status: int

    class Config:
        schema_extra = {
            "example": {
                "status": 200,
            }
        }


@app.get(
    "/api/start",
    description="Starts the API and confirms it is awake.",
    response_model=StartOutput,
)
async def confirmAwake() -> StartOutput:
    return {"status": 200}
