import asyncio
import httpx
import os

CL_API_KEY = os.getenv("CL_API_KEY")
CL_BASE_URL = "https://cl.kaisek.com"  


async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(
            f"{CL_BASE_URL}/api/flow",  
            json={
                "message": "Hello from test"
            },
            headers={
                "x-api-key": CL_API_KEY,
            },
        )

        print(res.status_code)
        print(res.text)


if __name__ == "__main__":
    asyncio.run(main())