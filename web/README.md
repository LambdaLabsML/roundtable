# Roundtable Web Interface

This directory contains the web-based terminal interface for Roundtable, providing a browser-based alternative to the command-line interface.

## Files

### Frontend
- `index.html` - Main terminal interface page
- `terminal.css` - Retro terminal styling (green-on-black theme)
- `terminal.js` - WebSocket client and terminal interaction logic

### Backend  
- `server.py` - WebSocket server that interfaces with existing Roundtable logic
- `web_ui.py` - Web UI class that mirrors the functionality of `ui/terminal.py`

## Features

### User Interface
- **Retro Terminal Aesthetic**: Black background with green monospace text
- **Blinking Cursor**: Animated cursor for authentic terminal feel
- **ASCII Art Banner**: "ROUNDTABLE" banner displayed on page load
- **Auto-scroll**: Automatically scrolls to show latest messages
- **Command History**: Use arrow keys to navigate previous commands
- **Responsive Design**: Works on desktop and mobile browsers

### Functionality  
- **Complete Command Support**: All existing terminal commands work identically
- **Real-time Discussion**: Live WebSocket updates during AI discussions
- **Session Replay**: View and replay previous discussion sessions
- **Error Handling**: Graceful error messages and connection recovery

### Architecture
- **Non-breaking**: Existing CLI functionality remains unchanged
- **WebSocket Communication**: Real-time bidirectional communication
- **Modular Design**: Clean separation between web UI and core logic
- **Compatible**: Uses same models, clients, and storage as CLI version

## Usage

### Starting the Web Server

From the root directory:

```bash
python web_main.py
```

This starts both:
- HTTP Server: http://localhost:8080 (serves the web interface)
- WebSocket Server: ws://localhost:8000/ws (handles terminal commands)

### Accessing the Interface

1. Open http://localhost:8080 in your browser
2. You'll see the Roundtable terminal interface with ASCII art banner
3. Use the same commands as the CLI version:
   - `1` - Start New Discussion
   - `2` - Load Previous Discussion  
   - `3` - Exit
   - `help` - Show help message

### Commands

The web interface supports all the same commands as the CLI version:

- **Menu Navigation**: Enter `1`, `2`, or `3` to select options
- **Start Discussion**: After selecting `1`, enter your discussion topic
- **Load Session**: After selecting `2`, choose from numbered session list
- **Navigation**: Use `c` to cancel operations, Enter to continue

### Technical Details

#### WebSocket Protocol

Messages are exchanged as JSON between client and server:

```json
// Client to Server
{
  "type": "command",
  "command": "1"
}

// Server to Client  
{
  "type": "output",
  "content": "Enter discussion topic:",
  "style": "system-message"
}
```

#### Message Types

- `output` - General text output with optional styling
- `message` - Formatted discussion messages from participants
- `header` - Discussion header with topic and round info
- `thinking` - Thinking indicator for AI participants
- `menu` - Display main menu
- `clear` - Clear terminal screen
- `final_consensus` - Show final discussion consensus

## Development

### Dependencies

The web interface adds one new dependency:
- `websockets>=11.0.0` - For WebSocket server functionality

### File Structure

```
web/
├── README.md          # This file
├── index.html         # Main terminal interface
├── terminal.css       # Terminal styling
├── terminal.js        # Client-side JavaScript
├── server.py          # WebSocket server
└── web_ui.py          # Web UI class

web_main.py            # Combined server launcher
```

### Testing

Basic structure test:
```bash
python test_web_structure.py
```

Integration with existing tests:
```bash
make test
```

## Browser Support

- **Modern Browsers**: Chrome, Firefox, Safari, Edge (recent versions)
- **WebSocket Support**: Required (available in all modern browsers)  
- **JavaScript**: ES6+ features used
- **CSS**: Modern flexbox and animations

## Troubleshooting

### Common Issues

1. **Connection Failed**: Ensure both HTTP and WebSocket servers are running
2. **Port Conflicts**: Servers use ports 8080 and 8000 - ensure they're available
3. **API Keys**: Web interface requires the same API keys as CLI version
4. **CORS Issues**: Development server includes CORS headers for local access

### Logs

Server logs are printed to console when running `web_main.py`:
- Connection events
- Error messages  
- Client registration/disconnection

### Browser Console

Check browser developer console for client-side errors:
- WebSocket connection issues
- JavaScript errors
- Message parsing problems