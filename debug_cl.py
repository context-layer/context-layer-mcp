import asyncio
import httpx
import os

CL_API_KEY = os.getenv("CL_API_KEY")
CL_BASE_URL = os.getenv("CL_BASE_URL", "https://cl.kaisek.com")


async def main():
    headers = {
        "x-api-key": CL_API_KEY,
        "Content-Type": "application/json",
    }
    url = f"{CL_BASE_URL}/api/execute"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(
            url,
            json={"message": "Hello from test"},
            headers=headers,
        )
        print("--- plain message ---")
        print(res.status_code)
        print(res.text)

        res = await client.post(
            url,
            json={
                "message": (
                    "Step: Generate invoice\n\nState:\n- amount: 100\n- currency: USD"
                )
            },
            headers=headers,
        )
        print("\n--- structured NL (State Bridge shape) ---")
        print(res.status_code)
        print(res.text)

        res = await client.post(
            url,
            json={"message": "Finalize invoice", "workflowEnd": True},
            headers=headers,
        )
        print("\n--- workflowEnd flag ---")
        print(res.status_code)
        print(res.text)


if __name__ == "__main__":
    asyncio.run(main())
