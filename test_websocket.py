#!/usr/bin/env python3
import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket():
    """Test WebSocket connection to the server"""
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Send a test message
            test_message = {
                "type": "command",
                "command": "help"
            }
            
            await websocket.send(json.dumps(test_message))
            logger.info("Sent test message")
            
            # Wait for response
            response = await websocket.recv()
            logger.info(f"Received response: {response}")
            
    except Exception as e:
        logger.error(f"WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
