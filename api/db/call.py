import logging
from dataclasses import dataclass

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class CallDTO:
    id: str
    path_: str
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
                KeyConditionExpression=Key("path_").eq(path),
                Limit=start_count or page_size,
            )
            if page_number > 1:
                if  "LastEvaluatedKey" in response:
                    response = self.table.query(
                        KeyConditionExpression=Key("path_").eq(path),
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

    def get_partition_keys(self) -> set[str]:
        """
        Get all the partition keys.

        :return: The list of sorted partition keys.
        """
        try:
            keys = set()
            response = self.table.scan()
            keys.update(item['path_'] for item in response['Items'])
            while response.get('LastEvaluatedKey'):
                response = self.table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey'],
                    ProjectionExpression='path_'
                )
                keys.update(item['path_'] for item in response['Items'])
        except ClientError as err:
            logger.critical(
                "Couldn't scan for calls released in. %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return keys
