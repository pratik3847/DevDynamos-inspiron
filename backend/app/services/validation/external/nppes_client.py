"""
NPPES API Client
Validates NPIs against the official CMS National Provider Identifier registry
API Documentation: https://npiregistry.cms.hhs.gov/api-page
"""
import requests
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class NPPESClient:
    """Client for NPPES NPI Registry API"""
    
    BASE_URL = "https://npiregistry.cms.hhs.gov/api/"
    VERSION = "2.1"
    
    # Rate limiting: CMS allows ~1200 requests per 5 minutes
    MAX_REQUESTS_PER_PERIOD = 1200
    PERIOD_SECONDS = 300  # 5 minutes
    
    def __init__(self, timeout: int = 10, enable_cache: bool = True, cache_ttl: int = 2592000):
        """
        Initialize NPPES client
        
        Args:
            timeout: Request timeout in seconds
            enable_cache: Enable caching of results
            cache_ttl: Cache time-to-live in seconds (default 30 days)
        """
        self.timeout = timeout
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._request_times: list = []
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = time.time()
        
        # Remove old requests outside the time window
        self._request_times = [
            t for t in self._request_times 
            if now - t < self.PERIOD_SECONDS
        ]
        
        # Check if we can make another request
        if len(self._request_times) >= self.MAX_REQUESTS_PER_PERIOD:
            return False
        
        return True
    
    def _record_request(self):
        """Record a request for rate limiting"""
        self._request_times.append(time.time())
    
    def _get_from_cache(self, npi: str) -> Optional[Dict[str, Any]]:
        """Get NPI data from cache"""
        if not self.enable_cache:
            return None
        
        cached = self._cache.get(npi)
        if not cached:
            return None
        
        # Check if cache is expired
        cached_time = cached.get("cached_at")
        if cached_time:
            age = time.time() - cached_time
            if age > self.cache_ttl:
                # Cache expired
                del self._cache[npi]
                return None
        
        return cached
    
    def _save_to_cache(self, npi: str, data: Dict[str, Any]):
        """Save NPI data to cache"""
        if not self.enable_cache:
            return
        
        data["cached_at"] = time.time()
        self._cache[npi] = data
    
    def validate_npi(self, npi: str) -> Dict[str, Any]:
        """
        Validate NPI against NPPES registry
        
        Args:
            npi: 10-digit NPI number
        
        Returns:
            Dict with validation results:
            {
                "valid": bool,
                "npi": str,
                "status": str,  # "Active", "Deactivated", or None
                "type": str,  # "Individual" (Type 1) or "Organization" (Type 2)
                "name": str,
                "taxonomy": str,
                "state": str,
                "error": str,  # Error message if validation failed
                "cached": bool  # Whether result came from cache
            }
        """
        # Check cache first
        cached = self._get_from_cache(npi)
        if cached:
            cached["cached"] = True
            return cached
        
        # Check rate limit
        if not self._check_rate_limit():
            return {
                "valid": None,
                "npi": npi,
                "error": "Rate limit exceeded. Please try again later.",
                "cached": False
            }
        
        try:
            # Make API request
            params = {
                "number": npi,
                "version": self.VERSION
            }
            
            self._record_request()
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            result = self._parse_response(npi, data)
            
            # Cache result
            self._save_to_cache(npi, result)
            result["cached"] = False
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                "valid": None,
                "npi": npi,
                "error": "Request timeout. NPPES API did not respond in time.",
                "cached": False
            }
        except requests.exceptions.RequestException as e:
            return {
                "valid": None,
                "npi": npi,
                "error": f"API request failed: {str(e)}",
                "cached": False
            }
        except Exception as e:
            return {
                "valid": None,
                "npi": npi,
                "error": f"Unexpected error: {str(e)}",
                "cached": False
            }
    
    def _parse_response(self, npi: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse NPPES API response"""
        result_count = data.get("result_count", 0)
        
        if result_count == 0:
            return {
                "valid": False,
                "npi": npi,
                "status": None,
                "type": None,
                "name": None,
                "taxonomy": None,
                "state": None,
                "error": "NPI not found in NPPES registry"
            }
        
        # Get first result
        results = data.get("results", [])
        if not results:
            return {
                "valid": False,
                "npi": npi,
                "error": "No results returned from NPPES"
            }
        
        provider = results[0]
        
        # Extract basic info
        enumeration_type = provider.get("enumeration_type", "")
        basic = provider.get("basic", {})
        
        # Get status
        status = basic.get("status", "Unknown")
        
        # Get name
        if enumeration_type == "NPI-1":  # Individual
            first_name = basic.get("first_name", "")
            last_name = basic.get("last_name", "")
            name = f"{first_name} {last_name}".strip()
        else:  # Organization
            name = basic.get("organization_name", "")
        
        # Get primary taxonomy
        taxonomies = provider.get("taxonomies", [])
        primary_taxonomy = None
        for tax in taxonomies:
            if tax.get("primary"):
                primary_taxonomy = tax.get("desc", "")
                break
        
        # Get state from practice location
        addresses = provider.get("addresses", [])
        state = None
        for addr in addresses:
            if addr.get("address_purpose") == "LOCATION":
                state = addr.get("state", "")
                break
        
        return {
            "valid": status == "A",  # A = Active
            "npi": npi,
            "status": "Active" if status == "A" else "Deactivated" if status == "D" else "Unknown",
            "type": "Individual" if enumeration_type == "NPI-1" else "Organization",
            "name": name,
            "taxonomy": primary_taxonomy,
            "state": state,
            "error": None if status == "A" else f"NPI status is {status}"
        }
    
    def batch_validate(self, npis: list) -> Dict[str, Dict[str, Any]]:
        """
        Validate multiple NPIs
        
        Args:
            npis: List of NPI numbers
        
        Returns:
            Dict mapping NPI to validation result
        """
        results = {}
        
        for npi in npis:
            results[npi] = self.validate_npi(npi)
            
            # Small delay to respect rate limits
            time.sleep(0.1)
        
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "cache_enabled": self.enable_cache,
            "cache_ttl_days": self.cache_ttl / 86400,
            "recent_requests": len(self._request_times)
        }
    
    def clear_cache(self):
        """Clear the cache"""
        self._cache.clear()
    
    def clear_expired_cache(self):
        """Remove expired entries from cache"""
        if not self.enable_cache:
            return
        
        now = time.time()
        expired_keys = []
        
        for npi, data in self._cache.items():
            cached_time = data.get("cached_at", 0)
            age = now - cached_time
            
            if age > self.cache_ttl:
                expired_keys.append(npi)
        
        for key in expired_keys:
            del self._cache[key]


# Global singleton instance
_nppes_client = None


def get_nppes_client(enable_cache: bool = True, cache_ttl: int = 2592000) -> NPPESClient:
    """
    Get singleton instance of NPPES client
    
    Args:
        enable_cache: Enable caching
        cache_ttl: Cache TTL in seconds (default 30 days)
    
    Returns:
        NPPESClient instance
    """
    global _nppes_client
    
    if _nppes_client is None:
        _nppes_client = NPPESClient(
            enable_cache=enable_cache,
            cache_ttl=cache_ttl
        )
    
    return _nppes_client
