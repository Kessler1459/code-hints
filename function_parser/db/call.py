import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from function_parser.models.call import Call as ModelCall

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class CallDTO:
    id: str
    path: str
    line_number: int
    file_name: str
    url: str


class Call:
    def __init__(self, dyn_client, table_name: str):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.table_name = table_name
        self.dyn_resource = dyn_client
        self.table = self._get_table()

    def create_table(self):
        """
        Creates an Amazon DynamoDB table that can be used to store calls data.
        The table uses the module path of the calls as the partition key and the
        id as the sort key.

        """
        try:
            self.table = self.dyn_resource.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {"AttributeName": "path", "KeyType": "HASH"},  # Partition key
                    {"AttributeName": "id", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "path", "AttributeType": "S"},
                    {"AttributeName": "id", "AttributeType": "S"},
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 25,
                    "WriteCapacityUnits": 25,
                },
            )
            self.table.wait_until_exists()
            logger.info(f"Table {self.table_name} created")
            return self.table
        except ClientError as err:
            logger.critical(
                "Couldn't create table %s. Here's why: %s: %s",
                self.table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def _get_table(self):
        try:
            table = self.dyn_resource.Table(self.table_name)
            return table
        except ClientError as err:
            logger.critical(
                f"Couldn't get table {self.table_name}",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def write_batch_threaded(self, calls: set[ModelCall] | list[ModelCall]):
        """
        Fills an Amazon DynamoDB table with the specified data, using the Boto3
        Table.batch_writer() function to put the items in the table.
        Inside the context manager, Table.batch_writer builds a list of
        requests. On exiting the context manager, Table.batch_writer starts sending
        batches of write requests to Amazon DynamoDB and automatically
        handles chunking, buffering, and retrying. Uses ThreadPoolExecutor

        :param calls: The data to put in the table. Each item must contain at least
                       the keys required by the schema that was specified when the
                       table was created.
        """
        try:
            logger.info(f"Writing batch with {len(calls)} calls")
            calls = list(calls)
            BATCHSIZE = 10
            sub_batches = [
                calls[i : i + BATCHSIZE] for i in range(0, len(calls), BATCHSIZE)
            ]
            with ThreadPoolExecutor(BATCHSIZE) as executor:
                futures = [
                    executor.submit(self._write_batch, sub_batch)
                    for sub_batch in sub_batches
                ]
                for future in as_completed(futures):
                    future.result()
            logger.info("Inserted batch!")
        except ClientError as err:
            logger.critical(
                "Couldn't load data into table %s. Here's why: %s: %s",
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def _write_batch(self, calls: set[ModelCall] | list[ModelCall]):
        """
        Fills an Amazon DynamoDB table with the specified data, using the Boto3
        Table.batch_writer() function to put the items in the table.
        Inside the context manager, Table.batch_writer builds a list of
        requests. On exiting the context manager, Table.batch_writer starts sending
        batches of write requests to Amazon DynamoDB and automatically
        handles chunking, buffering, and retrying.

        :param calls: The data to put in the table. Each item must contain at least
                       the keys required by the schema that was specified when the
                       table was created.
        """
        try:
            with self.table.batch_writer() as writer:
                for call in calls:
                    dto = CallDTO(
                        call.id,
                        call.path,
                        call.line_number,
                        call.file.name,
                        call.file.web_url,
                    )
                    writer.put_item(Item=vars(dto))
        except ClientError as err:
            logger.critical(
                "Couldn't load data into table %s. Here's why: %s: %s",
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def get_calls(self, path: str, page_number: int, page_size: int):
        """
        Queries for calls with the module path.

        :param path: Path to the module.
        :return: The list of calls for that module.
        """
        page_number += 1
        start_count = (page_number * page_size) - page_size
        try:
            response = self.table.query(
                KeyConditionExpression=Key("path").eq(path),
                Limit=start_count or page_size,
            )
            if page_number > 1:
                if  "LastEvaluatedKey" in response:
                    response = self.table.query(
                        KeyConditionExpression=Key("path").eq(path),
                        Limit=page_size,
                        ExclusiveStartKey=response["LastEvaluatedKey"],
                    )
                else:
                    return []
        except ClientError as err:
            logger.critical(
                "Couldn't query for calls released in %s. Here's why: %s: %s",
                path,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return response["Items"]

    def delete_table(self):
        """
        Deletes the table.
        """
        try:
            self.table.delete()
            self.table = None
            logger.info(f"Table {self.table_name} deleted")
        except ClientError as err:
            logger.critical(
                "Couldn't delete table.",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
