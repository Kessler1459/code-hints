import logging

import boto3
from botocore.exceptions import ClientError

from .call import Call

logger = logging.getLogger(__name__)

CALLTABLENAME = "calls"


class Dynamo:
    call_table: Call

    def __init__(
        self,
        aws_region: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_endpoint: str,
        init_tables=False
    ) -> None:
        self.resource = boto3.resource(
            "dynamodb",
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url=aws_endpoint or None,
        )
        self.call_table = Call(self.resource, CALLTABLENAME)
        if init_tables:
            logger.info("Starting DB")
            self.init_tables()

    def init_tables(self):
        if not self.exists(CALLTABLENAME):
            self.call_table.create_table()

    def list_tables(self) -> list[str]:
        """
        Lists the Amazon DynamoDB tables for the current account.

        :return: The list of tables.
        """
        try:
            return [table.name for table in self.resource.tables.all()]
        except ClientError as err:
            logger.critical(
                "Couldn't list tables. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def exists(self, table_name: str):
        """
        Determines whether a table exists. As a side effect, stores the table in
        a member variable.

        :param table_name: The name of the table to check.
        :return: True when the table exists; otherwise, False.
        """
        try:
            tables = self.list_tables()
            return table_name in tables
        except ClientError as err:
            logger.critical(
                "Couldn't check for existence of %s. Here's why: %s: %s",
                table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
