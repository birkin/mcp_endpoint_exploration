import urllib

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather")

@mcp.tool()
def get_weather(city: str) -> str:
    """Get the current weather for a given city."""
    url = f'https://wttr.in/{urllib.parse.quote_plus(city)}?format=%C+%t'
    return urllib.request.urlopen(url).read().decode('utf-8')

if __name__ == '__main__':
    mcp.run(transport='stdio')
