from mcp.server.fastmcp import FastMCP


http_client = None
mcp = FastMCP(name="AI Assistant MCP server", host="0.0.0.0", port=8001)

@mcp.tool()
def test_tool():
    """This is a test tool. Skip this tool."""
    return {"message": "This is a test tool"}


if __name__ == "__main__":
    print("Starting MCP server...")
    mcp.run(transport="sse")
    print("Started MCP server")
