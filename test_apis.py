import sys
import asyncio
from app import get_stats, get_near_expiry, get_donations, get_expired

async def test_endpoints():
    print("Testing get_stats")
    stats = await get_stats()
    print("Stats:", stats)
    
    print("\nTesting get_near_expiry")
    near = await get_near_expiry()
    print("Near Expiry count:", len(near))
    if near:
        print("First Near Expiry Item:", near[0]['product_name'], "status:", near[0]['status'])
        
    print("\nTesting get_donations")
    donations = await get_donations()
    print("Donations count:", len(donations))
    if donations:
        print("First Donation Item:", donations[0]['product_name'], "status:", donations[0]['status'])

    print("\nTesting get_expired")
    expired = await get_expired()
    print("Expired count:", len(expired))
    if expired:
        print("First Expired Item:", expired[0]['product_name'], "status:", expired[0]['status'])

if __name__ == "__main__":
    asyncio.run(test_endpoints())
