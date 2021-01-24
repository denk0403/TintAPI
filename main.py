# uvicorn main:app --port 8000  // Run locally

import asyncio
import os
import platform
import subprocess
import uuid
from concurrent.futures.process import ProcessPoolExecutor
from enum import Enum
from subprocess import TimeoutExpired
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# From Stack Overflow
# Enables concurrent processing
async def run_in_process(fn, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        app.state.executor, fn, *args
    )  # wait and return result


# From Stack Overflow
@app.on_event("startup")
async def on_startup():
    app.state.executor = ProcessPoolExecutor()


# From Stack Overflow
@app.on_event("shutdown")
async def on_shutdown():
    app.state.executor.shutdown()


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


def run_machine(ts: TintSubmission, machine: MachineType) -> TintOutput:
    """Run the given machine type with the given tint code."""

    # create tint file
    tint_file_name = f"./{str(uuid.uuid4().hex)}.txt"
    tint_file = open(tint_file_name, "w")
    tint_file.write(ts.program)
    tint_file.close()

    # create test file
    test_file_name = f"./{str(uuid.uuid4().hex)}.txt"
    test_file = open(test_file_name, "w")
    test_file.write(ts.tests)
    test_file.close()

    opSys = platform.platform().lower()  # current operating system
    try:

        # match binary to current operating system
        if opSys.find("linux") >= 0:
            binary_file = "./tint-linux"
        elif opSys.find("macos") >= 0:
            binary_file = "./tint-mac"
        else:
            raise Exception(opSys)

        # build command
        if ts.verbose:
            tint_args = [
                binary_file,
                "-m",
                machine.value,
                "-v",
                tint_file_name,
                test_file_name,
            ]
        else:
            tint_args = [
                binary_file,
                "-m",
                machine.value,
                tint_file_name,
                test_file_name,
            ]

        # run process
        process = subprocess.run(tint_args, capture_output=True, timeout=3)

        output = process.stdout
        status = 200
    except TimeoutExpired:
        output = "Error: Program took too long or encountered an infinite loop"
        status = 400
    except Exception:
        output = "Error: Something went wrong"
        status = 400
    finally:
        # clean up
        os.remove(tint_file_name)
        os.remove(test_file_name)

    return {"status": status, "output": output}


@app.post(
    "/api/one-way-tm",
    description="Runs a one-way turing machine program on the given tests.",
    response_model=TintOutput,
)
async def run_one_way_turing_machine(tm: TintSubmission) -> TintOutput:
    """Endpoint for running a one-way turing machine in Tint."""

    res = await run_in_process(run_machine, tm, MachineType.ONE_WAY_TM)
    return res


@app.post(
    "/api/two-way-tm",
    description="Runs a two-way turing machine program on the given tests.",
    response_model=TintOutput,
)
async def run_two_way_turing_machine(tm: TintSubmission) -> TintOutput:
    """Endpoint for running a two-way turing machine in Tint."""

    res = await run_in_process(run_machine, tm, MachineType.TWO_WAY_TM)
    return res


@app.post(
    "/api/dfa",
    description="Runs a dfa program on the given tests.",
    response_model=TintOutput,
)
async def run_dfa(tm: TintSubmission) -> TintOutput:
    """Endpoint for running a deterministic finite automata in Tint."""

    res = await run_in_process(run_machine, tm, MachineType.DFA)
    return res


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
    """Endpoint for confirming the API is responding."""

    return {"status": 200}
