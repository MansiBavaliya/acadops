
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():
    url = "http://127.0.0.1:8000/mcp"

    async with streamable_http_client(url) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Test 1: Change available study hours to 5
            print("\n=== UPDATE AVAILABLE STUDY HOURS ===")

            result = await session.call_tool(
                "update_available_study_hours",
                {
                    "available_hours": 5
                }
            )

            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)

            if result.is_error:
                print("Update failed. Check the server output.")
                return

            # Test 2: Retrieve the latest saved plan
            print("\n=== VERIFY LATEST SAVED PLAN ===")

            result = await session.call_tool(
                "get_saved_academic_plan",
                {}
            )

            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)


if __name__ == "__main__":
    asyncio.run(main())
