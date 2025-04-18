import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from uuid import UUID
import json

from app.core.supabase import get_supabase

logger = logging.getLogger(__name__)

async def execute_query(
    table: str,
    select_columns: str = "*",
    filters: Optional[Dict[str, Any]] = None,
    order_column: Optional[str] = None,
    order_desc: bool = False,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    joins: Optional[List[Dict[str, str]]] = None,
    in_filters: Optional[Dict[str, List[Any]]] = None,
    like_filters: Optional[Dict[str, str]] = None,
    not_filters: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Execute a query against Supabase.
    
    Args:
        table: Table name
        select_columns: Columns to select
        filters: Equality filters
        order_column: Column to order by
        order_desc: Whether to order in descending order
        limit: Maximum number of results
        offset: Offset for pagination
        joins: Joins to other tables
        in_filters: Filters using "in" operator
        like_filters: Filters using "like" operator
        not_filters: Filters using "not" operator
        
    Returns:
        Tuple of (result data, error message or None)
    """
    try:
        supabase = get_supabase()
        
        query = supabase.table(table).select(select_columns)
        
        # Apply joins
        if joins:
            for join in joins:
                # Each join should have 'table', 'column', and 'foreign_column'
                if all(k in join for k in ["table", "column", "foreign_column"]):
                    # We need to modify the select statement
                    query = supabase.table(table).select(f"{select_columns}, {join['table']}(*)")
                    # Supabase doesn't have explicit join methods, it uses nested selects
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if value is None:
                    query = query.is_(key, "null")
                else:
                    query = query.eq(key, value)
        
        # Apply in filters
        if in_filters:
            for key, values in in_filters.items():
                query = query.in_(key, values)
        
        # Apply like filters
        if like_filters:
            for key, value in like_filters.items():
                query = query.like(key, f"%{value}%")
        
        # Apply not filters
        if not_filters:
            for key, value in not_filters.items():
                if value is None:
                    query = query.not_.is_(key, "null")
                else:
                    query = query.not_.eq(key, value)
        
        # Apply ordering
        if order_column:
            query = query.order(order_column, desc=order_desc)
        
        # Apply pagination
        if limit is not None:
            query = query.limit(limit)
        
        if offset is not None:
            query = query.range(offset, offset + (limit or 1000) - 1)
        
        # Execute query
        response = await query.execute()
        
        return response.data, None
    
    except Exception as e:
        logger.error(f"Error executing Supabase query on {table}: {str(e)}")
        return [], str(e)

async def get_by_id(table: str, id: Union[str, UUID], select_columns: str = "*") -> Optional[Dict[str, Any]]:
    """
    Get a record by ID.
    
    Args:
        table: Table name
        id: Record ID
        select_columns: Columns to select
        
    Returns:
        Record or None if not found
    """
    try:
        supabase = get_supabase()
        
        # Convert UUID to string if needed
        id_str = str(id) if isinstance(id, UUID) else id
        
        response = await supabase.table(table).select(select_columns).eq("id", id_str).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        return None
    
    except Exception as e:
        logger.error(f"Error getting record by ID from {table}: {str(e)}")
        return None

async def create_record(table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Create a new record.
    
    Args:
        table: Table name
        data: Record data
        
    Returns:
        Created record or None if creation failed
    """
    try:
        supabase = get_supabase()
        
        # Convert UUID values to strings
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, UUID):
                processed_data[key] = str(value)
            elif isinstance(value, dict) or isinstance(value, list):
                # Handle JSON data
                processed_data[key] = value
            else:
                processed_data[key] = value
        
        response = await supabase.table(table).insert(processed_data).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        return None
    
    except Exception as e:
        logger.error(f"Error creating record in {table}: {str(e)}")
        return None

async def update_record(table: str, id: Union[str, UUID], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update a record.
    
    Args:
        table: Table name
        id: Record ID
        data: Record data to update
        
    Returns:
        Updated record or None if update failed
    """
    try:
        supabase = get_supabase()
        
        # Convert UUID to string if needed
        id_str = str(id) if isinstance(id, UUID) else id
        
        # Convert UUID values to strings
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, UUID):
                processed_data[key] = str(value)
            elif isinstance(value, dict) or isinstance(value, list):
                # Handle JSON data
                processed_data[key] = value
            else:
                processed_data[key] = value
        
        response = await supabase.table(table).update(processed_data).eq("id", id_str).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        return None
    
    except Exception as e:
        logger.error(f"Error updating record in {table}: {str(e)}")
        return None

async def delete_record(table: str, id: Union[str, UUID]) -> bool:
    """
    Delete a record.
    
    Args:
        table: Table name
        id: Record ID
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        supabase = get_supabase()
        
        # Convert UUID to string if needed
        id_str = str(id) if isinstance(id, UUID) else id
        
        response = await supabase.table(table).delete().eq("id", id_str).execute()
        
        return bool(response.data)
    
    except Exception as e:
        logger.error(f"Error deleting record from {table}: {str(e)}")
        return False

async def upsert_record(
    table: str,
    data: Dict[str, Any],
    unique_columns: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Upsert a record (insert if not exists, update if exists).
    
    Args:
        table: Table name
        data: Record data
        unique_columns: Columns that determine uniqueness
        
    Returns:
        Upserted record or None if operation failed
    """
    try:
        supabase = get_supabase()
        
        # Convert UUID values to strings
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, UUID):
                processed_data[key] = str(value)
            elif isinstance(value, dict) or isinstance(value, list):
                # Handle JSON data
                processed_data[key] = value
            else:
                processed_data[key] = value
        
        response = await supabase.table(table).upsert(processed_data, on_conflict=",".join(unique_columns)).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        return None
    
    except Exception as e:
        logger.error(f"Error upserting record in {table}: {str(e)}")
        return None

async def count_records(
    table: str,
    filters: Optional[Dict[str, Any]] = None,
    in_filters: Optional[Dict[str, List[Any]]] = None,
    like_filters: Optional[Dict[str, str]] = None,
    not_filters: Optional[Dict[str, Any]] = None
) -> int:
    """
    Count records in a table.
    
    Args:
        table: Table name
        filters: Equality filters
        in_filters: Filters using "in" operator
        like_filters: Filters using "like" operator
        not_filters: Filters using "not" operator
        
    Returns:
        Number of records
    """
    try:
        # Execute a query with count only
        result, error = await execute_query(
            table=table,
            select_columns="count(*)",
            filters=filters,
            in_filters=in_filters,
            like_filters=like_filters,
            not_filters=not_filters
        )
        
        if error:
            return 0
        
        if result and len(result) > 0:
            # The count is returned in a different format
            count = result[0].get("count", 0)
            return int(count)
        
        return 0
    
    except Exception as e:
        logger.error(f"Error counting records in {table}: {str(e)}")
        return 0

async def execute_rpc(
    function_name: str,
    params: Dict[str, Any]
) -> Tuple[Any, Optional[str]]:
    """
    Execute a stored procedure via RPC.
    
    Args:
        function_name: Name of the function to call
        params: Function parameters
        
    Returns:
        Tuple of (result, error message or None)
    """
    try:
        supabase = get_supabase()
        
        # Convert UUID values to strings
        processed_params = {}
        for key, value in params.items():
            if isinstance(value, UUID):
                processed_params[key] = str(value)
            elif isinstance(value, dict) or isinstance(value, list):
                # Handle JSON data
                processed_params[key] = value
            else:
                processed_params[key] = value
        
        response = await supabase.rpc(function_name, processed_params).execute()
        
        return response.data, None
    
    except Exception as e:
        logger.error(f"Error executing RPC {function_name}: {str(e)}")
        return None, str(e)
