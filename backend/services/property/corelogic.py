"""
CoreLogic Property API client.
Provides property valuations, sales history, and rental estimates.

Supports both sandbox and production environments:
- Sandbox: https://property-sandbox-api.corelogic.asia
- Production: https://property-api.corelogic.asia

Set CORELOGIC_USE_SANDBOX=true/false to switch environments.
Override with CORELOGIC_BASE_URL if using a custom endpoint.
"""

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

from config import get_settings
from database import SessionLocal, APICache

settings = get_settings()

# CoreLogic API endpoints
CORELOGIC_SANDBOX_URL = "https://property-sandbox-api.corelogic.asia"
CORELOGIC_PRODUCTION_URL = "https://property-api.corelogic.asia"


class CoreLogicClient:
    """
    Client for CoreLogic Property API.
    
    Authentication: OAuth 2.0 Client Credentials flow
    
    Environment variables:
    - CORELOGIC_CLIENT_ID: Your OAuth client ID
    - CORELOGIC_CLIENT_SECRET: Your OAuth client secret
    - CORELOGIC_USE_SANDBOX: Set to 'true' for sandbox, 'false' for production
    - CORELOGIC_BASE_URL: (Optional) Override the base URL entirely
    """
    
    def __init__(self):
        self.client_id = settings.corelogic_client_id
        self.client_secret = settings.corelogic_client_secret
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        
        # Determine base URL: explicit override > sandbox/production auto-detection
        if settings.corelogic_base_url:
            self.base_url = settings.corelogic_base_url
            self._environment = "custom"
        elif settings.corelogic_use_sandbox:
            self.base_url = CORELOGIC_SANDBOX_URL
            self._environment = "sandbox"
        else:
            self.base_url = CORELOGIC_PRODUCTION_URL
            self._environment = "production"
        
        print(f"[CoreLogic] Initialized client for {self._environment} environment: {self.base_url}")
    
    @property
    def is_configured(self) -> bool:
        """Check if CoreLogic credentials are configured."""
        return bool(self.client_id and self.client_secret)
    
    async def _get_access_token(self) -> str:
        """
        Get or refresh OAuth 2.0 access token using client credentials flow.
        
        Token endpoint: {base_url}/oauth/token
        Grant type: client_credentials
        """
        # Return cached token if still valid
        if self._access_token and self._token_expires and datetime.utcnow() < self._token_expires:
            return self._access_token
        
        if not self.is_configured:
            raise Exception("CoreLogic credentials not configured. Set CORELOGIC_CLIENT_ID and CORELOGIC_CLIENT_SECRET.")
        
        token_url = f"{self.base_url}/oauth/token"
        print(f"[CoreLogic] Requesting access token from: {token_url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    token_url,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                    },
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self._access_token = data["access_token"]
                    expires_in = data.get("expires_in", 3600)
                    self._token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                    print(f"[CoreLogic] Auth successful, token expires in {expires_in}s")
                    return self._access_token
                else:
                    # Provide helpful error messages for common issues
                    error_text = response.text
                    if response.status_code == 401:
                        raise Exception(
                            f"CoreLogic auth failed (401): Invalid credentials. "
                            f"Check CORELOGIC_CLIENT_ID and CORELOGIC_CLIENT_SECRET. "
                            f"Response: {error_text}"
                        )
                    elif response.status_code == 404:
                        raise Exception(
                            f"CoreLogic auth failed (404): Token endpoint not found. "
                            f"Check if CORELOGIC_BASE_URL is correct. "
                            f"Tried: {token_url}. Response: {error_text}"
                        )
                    elif "No such proxy" in error_text:
                        raise Exception(
                            f"CoreLogic auth failed: API endpoint not recognized by gateway. "
                            f"This may indicate the endpoint has changed. "
                            f"Tried: {token_url}. "
                            f"Try setting CORELOGIC_USE_SANDBOX=false for production. "
                            f"Response: {error_text}"
                        )
                    else:
                        raise Exception(
                            f"CoreLogic auth failed ({response.status_code}): {error_text}"
                        )
            except httpx.TimeoutException:
                raise Exception(f"CoreLogic auth timeout connecting to {token_url}")
            except httpx.ConnectError as e:
                raise Exception(f"CoreLogic connection error: {e}. Check if {self.base_url} is reachable.")
    
    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to CoreLogic API."""
        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"CoreLogic API error: {response.status_code} - {response.text}")
    
    async def get_property(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get property details by address.
        
        Returns property ID and basic details.
        """
        # Check cache first
        cached = self._get_cached(f"property:{address}")
        if cached:
            return cached
        
        try:
            data = await self._request("/Property", params={
                "$filter": f"contains(FullAddress, '{address}')",
                "$top": 1
            })
            
            properties = data.get("value", [])
            if properties:
                result = properties[0]
                self._set_cached(f"property:{address}", result)
                return result
            return None
            
        except Exception as e:
            print(f"CoreLogic property lookup failed: {e}")
            return None
    
    async def get_avm(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Automated Valuation Model (AVM) estimate.
        
        Returns estimated value and confidence level.
        """
        cached = self._get_cached(f"avm:{property_id}")
        if cached:
            return cached
        
        try:
            data = await self._request(f"/Property/{property_id}/AVM")
            
            result = {
                "value": data.get("estimatedValue"),
                "low": data.get("lowEstimate"),
                "high": data.get("highEstimate"),
                "confidence": data.get("confidenceLevel"),
                "valuation_date": data.get("valuationDate")
            }
            
            self._set_cached(f"avm:{property_id}", result)
            return result
            
        except Exception as e:
            print(f"CoreLogic AVM failed: {e}")
            return None
    
    async def get_rental_avm(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Get rental AVM estimate.
        
        Returns estimated weekly rent.
        """
        cached = self._get_cached(f"rental_avm:{property_id}")
        if cached:
            return cached
        
        try:
            data = await self._request(f"/Property/{property_id}/RentalAVM")
            
            result = {
                "weekly_low": data.get("lowEstimate"),
                "weekly_mid": data.get("estimatedRent"),
                "weekly_high": data.get("highEstimate"),
                "confidence": data.get("confidenceLevel")
            }
            
            self._set_cached(f"rental_avm:{property_id}", result)
            return result
            
        except Exception as e:
            print(f"CoreLogic Rental AVM failed: {e}")
            return None
    
    async def get_sales_history(self, property_id: str) -> List[Dict[str, Any]]:
        """
        Get transaction history for a property.
        
        Returns list of past sales with dates and prices.
        """
        cached = self._get_cached(f"sales:{property_id}")
        if cached:
            return cached
        
        try:
            data = await self._request(f"/Property/{property_id}/SalesHistory")
            
            sales = []
            for sale in data.get("value", []):
                sales.append({
                    "date": sale.get("contractDate"),
                    "price": sale.get("price"),
                    "type": sale.get("saleType")
                })
            
            self._set_cached(f"sales:{property_id}", sales)
            return sales
            
        except Exception as e:
            print(f"CoreLogic sales history failed: {e}")
            return []
    
    async def get_comparable_sales(
        self,
        address: str,
        bedrooms: int,
        property_type: str,
        radius_km: float = 1.0,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Get comparable sales in the area.
        
        Filters by property type, bedrooms, and recent sales.
        """
        cache_key = f"comps:{address}:{bedrooms}:{property_type}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # This would use CoreLogic's spatial search
            # Simplified for demo
            data = await self._request("/Sales", params={
                "$filter": f"Bedrooms eq {bedrooms}",
                "$top": 10
            })
            
            comps = []
            for sale in data.get("value", []):
                comps.append({
                    "address": sale.get("address"),
                    "price": sale.get("price"),
                    "date": sale.get("saleDate"),
                    "bedrooms": sale.get("bedrooms"),
                    "bathrooms": sale.get("bathrooms"),
                    "land_size": sale.get("landSize"),
                    "distance_km": None  # Would be calculated
                })
            
            self._set_cached(cache_key, comps)
            return comps
            
        except Exception as e:
            print(f"CoreLogic comparable sales failed: {e}")
            return []
    
    def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache."""
        db = SessionLocal()
        try:
            cache_entry = db.query(APICache).filter(
                APICache.cache_key == key,
                APICache.provider == "corelogic"
            ).first()
            
            if cache_entry:
                # Check expiry (24 hour cache for CoreLogic)
                if cache_entry.expires_at and datetime.utcnow() > cache_entry.expires_at:
                    db.delete(cache_entry)
                    db.commit()
                    return None
                return cache_entry.response_data
            return None
        finally:
            db.close()
    
    def _set_cached(self, key: str, data: Any) -> None:
        """Set value in cache."""
        db = SessionLocal()
        try:
            cache_entry = db.query(APICache).filter(
                APICache.cache_key == key,
                APICache.provider == "corelogic"
            ).first()
            
            if cache_entry:
                cache_entry.response_data = data
                cache_entry.expires_at = datetime.utcnow() + timedelta(hours=24)
            else:
                cache_entry = APICache(
                    cache_key=key,
                    provider="corelogic",
                    response_data=data,
                    expires_at=datetime.utcnow() + timedelta(hours=24)
                )
                db.add(cache_entry)
            
            db.commit()
        finally:
            db.close()


# Singleton instance
_client: Optional[CoreLogicClient] = None


def get_corelogic_client() -> CoreLogicClient:
    """Get CoreLogic client instance."""
    global _client
    if _client is None:
        _client = CoreLogicClient()
    return _client


async def enrich_with_corelogic(address: str, bedrooms: int = None, property_type: str = None) -> Dict[str, Any]:
    """
    Enrich property data with CoreLogic information.
    
    Returns combined AVM, rental estimate, and comparable sales.
    """
    if not settings.corelogic_client_id:
        # Return mock data if API not configured
        return get_mock_corelogic_data(address)
    
    client = get_corelogic_client()
    
    # Get property ID
    property_data = await client.get_property(address)
    if not property_data:
        return get_mock_corelogic_data(address)
    
    property_id = property_data.get("PropertyKey")
    
    # Fetch all data in parallel
    avm = await client.get_avm(property_id)
    rental = await client.get_rental_avm(property_id)
    sales = await client.get_sales_history(property_id)
    comps = await client.get_comparable_sales(
        address,
        bedrooms=bedrooms or 3,
        property_type=property_type or "house"
    )
    
    return {
        "property_id": property_id,
        "avm": avm.get("value") if avm else None,
        "avm_confidence": avm.get("confidence") if avm else None,
        "avm_range": {
            "low": avm.get("low") if avm else None,
            "high": avm.get("high") if avm else None
        },
        "rental_estimate": {
            "low": rental.get("weekly_low") if rental else None,
            "mid": rental.get("weekly_mid") if rental else None,
            "high": rental.get("weekly_high") if rental else None
        },
        "last_sold_price": sales[0].get("price") if sales else None,
        "last_sold_date": sales[0].get("date") if sales else None,
        "sales_history": sales,
        "comparable_sales": comps,
        "gross_yield_estimate": calculate_gross_yield(
            avm.get("value") if avm else None,
            rental.get("weekly_mid") if rental else None
        )
    }


def calculate_gross_yield(value: Optional[int], weekly_rent: Optional[int]) -> Optional[float]:
    """Calculate gross rental yield."""
    if value and weekly_rent and value > 0:
        annual_rent = weekly_rent * 52
        return round((annual_rent / value) * 100, 2)
    return None


def get_mock_corelogic_data(address: str) -> Dict[str, Any]:
    """Return mock CoreLogic data for development/demo."""
    return {
        "property_id": None,
        "avm": 1250000,
        "avm_confidence": "Medium",
        "avm_range": {
            "low": 1150000,
            "high": 1350000
        },
        "rental_estimate": {
            "low": 650,
            "mid": 720,
            "high": 780
        },
        "last_sold_price": 890000,
        "last_sold_date": "2019-03-15",
        "sales_history": [
            {"date": "2019-03-15", "price": 890000, "type": "auction"},
            {"date": "2012-08-22", "price": 620000, "type": "private_sale"}
        ],
        "comparable_sales": [
            {"address": "125 Smith St", "price": 1280000, "date": "2024-01-15", "bedrooms": 3, "distance_km": 0.2},
            {"address": "98 Smith St", "price": 1195000, "date": "2023-11-20", "bedrooms": 3, "distance_km": 0.3},
            {"address": "142 Jones St", "price": 1320000, "date": "2024-02-01", "bedrooms": 3, "distance_km": 0.5}
        ],
        "gross_yield_estimate": 3.0,
        "_mock": True
    }





