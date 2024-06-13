
from composio.core.local import Tool, Action
from .actions.sql_query import SQLQUERY

class SQL(Tool):
    """
    This class enables us to execute sql queries in a database
    """

    def actions(self) -> list[Action]:
        return [SQLQUERY]
    
    def triggers(self) -> list:
        return []