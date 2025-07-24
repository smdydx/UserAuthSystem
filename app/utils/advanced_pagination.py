
"""
Advanced Pagination with Cursor Support
"""
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel
from sqlalchemy.orm import Query
from sqlalchemy import desc, asc
import base64
import json

class CursorPagination(BaseModel):
    """Cursor-based pagination for large datasets"""
    first: Optional[int] = 10
    after: Optional[str] = None
    last: Optional[int] = None
    before: Optional[str] = None

class PageInfo(BaseModel):
    """Page information for cursor pagination"""
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None

class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    data: List[Any]
    page_info: PageInfo
    total_count: Optional[int] = None

def encode_cursor(value: Any) -> str:
    """Encode cursor value"""
    cursor_data = {"value": value}
    cursor_json = json.dumps(cursor_data, default=str)
    return base64.b64encode(cursor_json.encode()).decode()

def decode_cursor(cursor: str) -> Any:
    """Decode cursor value"""
    try:
        cursor_json = base64.b64decode(cursor.encode()).decode()
        cursor_data = json.loads(cursor_json)
        return cursor_data.get("value")
    except:
        return None

async def paginate_cursor(
    query: Query,
    cursor_field: str,
    pagination: CursorPagination,
    order_desc: bool = True
) -> PaginatedResponse:
    """
    Apply cursor-based pagination to query
    
    Args:
        query: SQLAlchemy query
        cursor_field: Field to use for cursor (usually 'id' or 'created_at')
        pagination: Pagination parameters
        order_desc: Whether to order descending
    """
    
    # Determine sort order
    order_func = desc if order_desc else asc
    query = query.order_by(order_func(getattr(query.column_descriptions[0]['type'], cursor_field)))
    
    # Apply cursor filters
    if pagination.after:
        after_value = decode_cursor(pagination.after)
        if after_value:
            if order_desc:
                query = query.filter(getattr(query.column_descriptions[0]['type'], cursor_field) < after_value)
            else:
                query = query.filter(getattr(query.column_descriptions[0]['type'], cursor_field) > after_value)
    
    if pagination.before:
        before_value = decode_cursor(pagination.before)
        if before_value:
            if order_desc:
                query = query.filter(getattr(query.column_descriptions[0]['type'], cursor_field) > before_value)
            else:
                query = query.filter(getattr(query.column_descriptions[0]['type'], cursor_field) < before_value)
    
    # Determine limit
    limit = pagination.first or pagination.last or 10
    
    # Fetch one extra item to check if there are more pages
    items = query.limit(limit + 1).all()
    
    # Check for more pages
    has_more = len(items) > limit
    if has_more:
        items = items[:limit]  # Remove the extra item
    
    # Generate cursors
    start_cursor = None
    end_cursor = None
    
    if items:
        start_cursor = encode_cursor(getattr(items[0], cursor_field))
        end_cursor = encode_cursor(getattr(items[-1], cursor_field))
    
    # Create page info
    page_info = PageInfo(
        has_next_page=has_more,
        has_previous_page=pagination.after is not None,
        start_cursor=start_cursor,
        end_cursor=end_cursor
    )
    
    return PaginatedResponse(
        data=items,
        page_info=page_info
    )

# Smart offset pagination with caching
class SmartPagination:
    """Smart pagination with performance optimizations"""
    
    @staticmethod
    def calculate_offset_limit(page: int, size: int, max_size: int = 100) -> Tuple[int, int]:
        """Calculate offset and limit with validation"""
        if page < 1:
            page = 1
        if size < 1:
            size = 10
        if size > max_size:
            size = max_size
        
        offset = (page - 1) * size
        return offset, size
    
    @staticmethod
    def create_response(items: List[Any], total: int, page: int, size: int) -> Dict[str, Any]:
        """Create standardized pagination response"""
        total_pages = (total + size - 1) // size  # Ceiling division
        
        return {
            "data": items,
            "pagination": {
                "current_page": page,
                "per_page": size,
                "total_items": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "prev_page": page - 1 if page > 1 else None
            }
        }
