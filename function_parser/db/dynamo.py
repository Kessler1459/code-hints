import logging

import boto3
from botocore.exceptions import ClientError

from function_parser.db.call import Call

logger = logging.getLogger(__name__)

class Dynamo:
    call_table: Call

    def __init__(self) -> None:
        logger.info('Connecting DB')
        self.resource = boto3.resource(
            "dynamodb",
            region_name="us-east-1",
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            endpoint_url='http://localhost:8000'
        )
        CALLTABLENAME = 'calls'
        self.call_table = Call(self.resource, CALLTABLENAME, self.exists(CALLTABLENAME))

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
            table = self.resource.Table(table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                exists = False
            else:
                logger.critical(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    table_name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
        return exists