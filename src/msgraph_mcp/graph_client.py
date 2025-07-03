"""
Microsoft Graph API client for MCP Server.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlencode
import json

import httpx
from asyncio_throttle import Throttler
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .auth import GraphAuthManager
from .config import GraphConfig

logger = logging.getLogger(__name__)


class GraphAPIError(Exception):
    """Exception raised for Microsoft Graph API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class RateLimitError(GraphAPIError):
    """Exception raised when rate limits are exceeded."""
    pass


class GraphClient:
    """Microsoft Graph API client with rate limiting and retry logic."""
    
    def __init__(self, config: GraphConfig, auth_manager: GraphAuthManager):
        """Initialize the Graph client."""
        self.config = config
        self.auth_manager = auth_manager
        self.base_url = config.graph_base_url
        
        # Setup rate limiting
        self.throttler = Throttler(
            rate_limit=config.max_requests_per_second,
            period=1.0
        )
        
        # Setup HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=config.request_timeout,
            verify=config.validate_ssl
        )
        
        logger.info(f"Graph client initialized for {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
    
    def _build_url(self, endpoint: str, query_params: Optional[Dict[str, Any]] = None) -> str:
        """Build a complete URL for a Graph API endpoint."""
        # Remove leading slash if present
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
        
        url = urljoin(self.base_url + '/', endpoint)
        
        if query_params:
            # Filter out None values and convert all values to strings
            filtered_params = {k: str(v) for k, v in query_params.items() if v is not None}
            if filtered_params:
                url += '?' + urlencode(filtered_params)
        
        return url
    
    @retry(
        retry=retry_if_exception_type((httpx.RequestError, GraphAPIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        query_params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the Graph API with retry logic."""
        
        async with self.throttler:
            try:
                # Get authentication headers
                auth_headers = await self.auth_manager.get_auth_headers_async()
                
                # Merge headers
                request_headers = auth_headers.copy()
                if headers:
                    request_headers.update(headers)
                
                # Build URL
                url = self._build_url(endpoint, query_params)
                
                logger.debug(f"Making {method} request to {url}")
                
                # Make request
                if data:
                    response = await self.http_client.request(
                        method,
                        url,
                        headers=request_headers,
                        json=data
                    )
                else:
                    response = await self.http_client.request(
                        method,
                        url,
                        headers=request_headers
                    )
                
                # Handle response
                await self._handle_response(response)
                
                # Return JSON response or empty dict for no content
                if response.status_code == 204:  # No Content
                    return {}
                
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"content": response.text}
                
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                raise GraphAPIError(f"Request failed: {e}")
            except Exception as e:
                logger.error(f"Unexpected error during request: {e}")
                raise
    
    async def _handle_response(self, response: httpx.Response) -> None:
        """Handle HTTP response and raise appropriate exceptions."""
        if response.is_success:
            return
        
        error_details = None
        try:
            error_data = response.json()
            if "error" in error_data:
                error_details = error_data["error"]
        except json.JSONDecodeError:
            pass
        
        status_code = response.status_code
        error_message = f"HTTP {status_code}: {response.text}"
        error_code = None
        
        if error_details:
            error_message = error_details.get("message", error_message)
            error_code = error_details.get("code")
        
        # Handle specific status codes
        if status_code == 429:  # Too Many Requests
            retry_after = response.headers.get("Retry-After", "60")
            raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
        elif status_code == 401:  # Unauthorized
            raise GraphAPIError("Authentication failed", status_code, error_code)
        elif status_code == 403:  # Forbidden
            raise GraphAPIError("Insufficient permissions", status_code, error_code)
        elif status_code == 404:  # Not Found
            raise GraphAPIError("Resource not found", status_code, error_code)
        else:
            raise GraphAPIError(error_message, status_code, error_code)
    
    # GET methods
    async def get(
        self,
        endpoint: str,
        query_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request to the Graph API."""
        return await self._make_request("GET", endpoint, query_params)
    
    # POST methods
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a POST request to the Graph API."""
        return await self._make_request("POST", endpoint, query_params, data)
    
    # PATCH methods
    async def patch(
        self,
        endpoint: str,
        data: Dict[str, Any],
        query_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a PATCH request to the Graph API."""
        return await self._make_request("PATCH", endpoint, query_params, data)
    
    # DELETE methods
    async def delete(
        self,
        endpoint: str,
        query_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a DELETE request to the Graph API."""
        return await self._make_request("DELETE", endpoint, query_params)
    
    # PUT methods
    async def put(
        self,
        endpoint: str,
        data: Dict[str, Any],
        query_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a PUT request to the Graph API."""
        return await self._make_request("PUT", endpoint, query_params, data)
    
    # Paginated requests
    async def get_all_pages(
        self,
        endpoint: str,
        query_params: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all pages of a paginated response.
        
        Args:
            endpoint: API endpoint
            query_params: Query parameters
            max_pages: Maximum number of pages to fetch (None for all)
            
        Returns:
            List of all items from all pages
        """
        all_items = []
        page_count = 0
        next_url = None
        
        # Make initial request
        response = await self.get(endpoint, query_params)
        
        while True:
            # Extract items from current page
            if "value" in response:
                all_items.extend(response["value"])
            else:
                # Single item response
                all_items.append(response)
                break
            
            page_count += 1
            
            # Check if we've reached max pages
            if max_pages and page_count >= max_pages:
                break
            
            # Check for next page
            next_url = response.get("@odata.nextLink")
            if not next_url:
                break
            
            # Make request for next page
            try:
                # Extract endpoint and query params from next URL
                if next_url.startswith(self.base_url):
                    next_endpoint = next_url[len(self.base_url):].lstrip('/')
                    response = await self.get(next_endpoint)
                else:
                    # Fallback: make direct request to next URL
                    auth_headers = await self.auth_manager.get_auth_headers_async()
                    http_response = await self.http_client.get(next_url, headers=auth_headers)
                    await self._handle_response(http_response)
                    response = http_response.json()
                    
            except Exception as e:
                logger.error(f"Error fetching next page: {e}")
                break
        
        logger.debug(f"Retrieved {len(all_items)} items across {page_count} pages")
        return all_items
    
    # Utility methods
    async def test_connection(self) -> bool:
        """Test the connection to Microsoft Graph."""
        try:
            await self.get("me")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get_service_info(self) -> Dict[str, Any]:
        """Get information about the Microsoft Graph service."""
        try:
            # Try to get service root info
            response = await self.get("")
            return response
        except Exception:
            # Fallback to basic info
            return {
                "service": "Microsoft Graph",
                "version": "beta",
                "base_url": self.base_url
            }