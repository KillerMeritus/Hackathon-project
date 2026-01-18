"""
Simple MCP Server for Demo
A basic HTTP server that provides MCP-compatible tools
"""
from flask import Flask, jsonify, request
import json

app = Flask(__name__)

# Available tools
TOOLS = [
    {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "calculate",
        "description": "Perform basic math calculations",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression to evaluate"}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "fetch_data",
        "description": "Fetch sample data for analysis",
        "parameters": {
            "type": "object",
            "properties": {
                "data_type": {"type": "string", "description": "Type of data: sales, users, products"}
            },
            "required": ["data_type"]
        }
    }
]

# Sample data
SAMPLE_DATA = {
    "sales": {
        "q4_2024": {
            "total_revenue": 2500000,
            "orders": 15000,
            "average_order_value": 166.67,
            "top_categories": ["Electronics", "Fashion", "Home"],
            "growth_rate": "15%"
        }
    },
    "users": {
        "total": 50000,
        "active": 35000,
        "new_q4": 8000
    },
    "products": {
        "total": 5000,
        "in_stock": 4500,
        "top_sellers": ["iPhone 15", "Nike Shoes", "Samsung TV"]
    }
}

@app.route('/tools', methods=['GET'])
def list_tools():
    """List available tools"""
    return jsonify({"tools": TOOLS})

@app.route('/tools/<tool_name>/execute', methods=['POST'])
def execute_tool(tool_name):
    """Execute a tool"""
    params = request.json or {}
    
    if tool_name == "get_weather":
        city = params.get("city", "Unknown")
        return jsonify({
            "result": f"Weather in {city}: Sunny, 25°C, Humidity 60%"
        })
    
    elif tool_name == "calculate":
        expr = params.get("expression", "0")
        try:
            result = eval(expr)
            return jsonify({"result": f"Result: {result}"})
        except:
            return jsonify({"result": "Error: Invalid expression"})
    
    elif tool_name == "fetch_data":
        data_type = params.get("data_type", "sales")
        data = SAMPLE_DATA.get(data_type, {"error": "Unknown data type"})
        return jsonify({"result": json.dumps(data, indent=2)})
    
    return jsonify({"error": f"Unknown tool: {tool_name}"})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    print("🚀 MCP Server starting on http://localhost:9090")
    print("Available tools: get_weather, calculate, fetch_data")
    app.run(host='0.0.0.0', port=9090, debug=False)
