import logging
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Response, status, Query

from config import set_logger
from models import Call, Message
from exceptions import TableNotFound
from db.dynamo import Dynamo

# ENVS
load_dotenv()
aws_region = os.getenv("AWSREGION")
aws_access_key_id = os.getenv("AWSACCESSKEY")
aws_secret_access_key = os.getenv("AWSSECRETACCESSKEY")
aws_endpoint = os.getenv("AWSENDPOINT")

set_logger()
logger = logging.getLogger(__name__)


def get_db():
    db = Dynamo(aws_region, aws_access_key_id, aws_secret_access_key, aws_endpoint)
    return db


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    db = Dynamo(aws_region, aws_access_key_id, aws_secret_access_key, aws_endpoint)
    if not db.list_tables():
        raise TableNotFound()
    app.state.path_keys = sorted(list(db.call_table.get_partition_keys()))
    logger.info("Database ready")


@app.get("/", status_code=200)
async def home() -> Message:
    return Message(message="Try with a python module path!")


@app.get("/calls/{module_path}")
async def module_calls(
    module_path: str,
    response: Response,
    page_number: int = Query(0, ge=0),
    page_size: int = Query(20, ge=1, le=100),
    db: Dynamo = Depends(get_db),
) -> list[Call] | None:
    calls = db.call_table.get_calls(module_path, page_number, page_size)
    response.status_code = status.HTTP_200_OK if calls else status.HTTP_204_NO_CONTENT
    return calls

@app.get("/calls")
async def module_calls(
    page_number: int = Query(0, ge=0), page_size: int = Query(200, ge=1, le=1000)
) -> list[str] | None:
    key_list = app.state.path_keys
    start = page_number * page_size
    end = start + page_size
    return key_list[start:end]


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down")
