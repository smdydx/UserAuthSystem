
"""
Response Compression Middleware for FastAPI
"""
import gzip
import brotli
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import json
from typing import Dict, Any

class CompressionMiddleware(BaseHTTPMiddleware):
    """Advanced response compression middleware"""
    
    def __init__(self, app, minimum_size: int = 500):
        super().__init__(app)
        self.minimum_size = minimum_size
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Skip compression for small responses
        if hasattr(response, 'body') and len(response.body) < self.minimum_size:
            return response
        
        # Get accepted encodings
        accept_encoding = request.headers.get('accept-encoding', '')
        
        # Try Brotli first (better compression)
        if 'br' in accept_encoding and hasattr(response, 'body'):
            compressed_body = brotli.compress(response.body)
            if len(compressed_body) < len(response.body):
                response.headers['content-encoding'] = 'br'
                response.headers['content-length'] = str(len(compressed_body))
                return Response(
                    content=compressed_body,
                    status_code=response.status_code,
                    headers=response.headers,
                    media_type=response.media_type
                )
        
        # Fallback to Gzip
        elif 'gzip' in accept_encoding and hasattr(response, 'body'):
            compressed_body = gzip.compress(response.body)
            if len(compressed_body) < len(response.body):
                response.headers['content-encoding'] = 'gzip'
                response.headers['content-length'] = str(len(compressed_body))
                return Response(
                    content=compressed_body,
                    status_code=response.status_code,
                    headers=response.headers,
                    media_type=response.media_type
                )
        
        return response

class ResponseOptimizationMiddleware(BaseHTTPMiddleware):
    """Optimize JSON responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Optimize JSON responses
        if (hasattr(response, 'media_type') and 
            response.media_type == 'application/json' and 
            hasattr(response, 'body')):
            
            try:
                # Parse and re-serialize with minimal separators
                data = json.loads(response.body)
                optimized_body = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
                
                return Response(
                    content=optimized_body,
                    status_code=response.status_code,
                    headers=response.headers,
                    media_type=response.media_type
                )
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        
        return response
