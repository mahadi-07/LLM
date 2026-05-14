import asyncio
from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

async def main():
    # Explicitly define stdio transport
    transport = PythonStdioTransport(
        script_path="my_server.py",
        python_cmd="../.venv/bin/python"   # optional but recommended
    )

    client = Client(transport)

    async with client:
        tools = await client.list_tools()

        print("Available tools:")
        for tool in tools:
            print(f" - {tool.name}: {tool.description}")

        result = await client.call_tool(
            "get_weather",
            {"city": "Tokyo"}
        )

        print(result)

if __name__ == "__main__":
    asyncio.run(main())