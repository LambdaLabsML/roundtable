class WebTerminal {
    constructor() {
        this.socket = null;
        this.output = document.getElementById('output');
        this.input = document.getElementById('command-input');
        this.cursor = document.getElementById('cursor');
        this.promptSpan = document.getElementById('prompt');
        
        this.isConnected = false;
        this.commandHistory = [];
        this.historyIndex = -1;
        this.currentInput = '';
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.connect();
        this.showWelcome();
    }
    
    setupEventListeners() {
        this.input.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.input.addEventListener('input', (e) => this.handleInput(e));
        
        // Focus input when clicking anywhere in terminal
        document.addEventListener('click', () => {
            this.input.focus();
        });
        
        // Keep input focused
        this.input.addEventListener('blur', () => {
            setTimeout(() => this.input.focus(), 10);
        });
        
        // Initial focus
        this.input.focus();
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/ws`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            this.isConnected = true;
            this.appendOutput('Connected to Roundtable server', 'system-message');
        };
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleServerMessage(data);
        };
        
        this.socket.onclose = () => {
            this.isConnected = false;
            this.appendOutput('Disconnected from server', 'error-message');
        };
        
        this.socket.onerror = (error) => {
            this.appendOutput('Connection error: ' + error, 'error-message');
        };
    }
    
    showWelcome() {
        const asciiArt = `
 ██████╗  ██████╗ ██╗   ██╗███╗   ██╗██████╗ ████████╗ █████╗ ██████╗ ██╗     ███████╗
 ██╔══██╗██╔═══██╗██║   ██║████╗  ██║██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██║     ██╔════╝
 ██████╔╝██║   ██║██║   ██║██╔██╗ ██║██║  ██║   ██║   ███████║██████╔╝██║     █████╗  
 ██╔══██╗██║   ██║██║   ██║██║╚██╗██║██║  ██║   ██║   ██╔══██║██╔══██╗██║     ██╔══╝  
 ██║  ██║╚██████╔╝╚██████╔╝██║ ╚████║██████╔╝   ██║   ██║  ██║██████╔╝███████╗███████╗
 ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═════╝ ╚══════╝╚══════╝
        `;
        
        this.appendOutput(asciiArt, 'ascii-art');
        this.appendOutput('A Socratic discussion platform for LLMs', 'system-message');
        this.appendOutput('', '');
        this.appendOutput('Available commands:', 'menu');
        this.appendOutput('  1 - Start New Discussion', 'menu-option');
        this.appendOutput('  2 - Load Previous Discussion', 'menu-option'); 
        this.appendOutput('  3 - Exit', 'menu-option');
        this.appendOutput('  help - Show this help message', 'menu-option');
        this.appendOutput('', '');
        this.appendOutput('Enter your choice:', 'system-message');
    }
    
    handleKeyDown(e) {
        switch(e.key) {
            case 'Enter':
                e.preventDefault();
                this.executeCommand();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.navigateHistory(-1);
                break;
            case 'ArrowDown':
                e.preventDefault();
                this.navigateHistory(1);
                break;
            case 'Tab':
                e.preventDefault();
                // Could implement tab completion here
                break;
        }
    }
    
    handleInput(e) {
        this.currentInput = this.input.value;
    }
    
    navigateHistory(direction) {
        if (this.commandHistory.length === 0) return;
        
        if (direction === -1) {
            // Up arrow
            if (this.historyIndex === -1) {
                this.historyIndex = this.commandHistory.length - 1;
            } else if (this.historyIndex > 0) {
                this.historyIndex--;
            }
        } else {
            // Down arrow
            if (this.historyIndex < this.commandHistory.length - 1) {
                this.historyIndex++;
            } else {
                this.historyIndex = -1;
                this.input.value = '';
                return;
            }
        }
        
        if (this.historyIndex >= 0) {
            this.input.value = this.commandHistory[this.historyIndex];
        }
    }
    
    executeCommand() {
        const command = this.input.value.trim();
        if (!command) return;
        
        // Add to history
        this.commandHistory.push(command);
        this.historyIndex = -1;
        
        // Display command
        this.appendOutput(`$ ${command}`, '');
        
        // Clear input
        this.input.value = '';
        
        // Send to server
        if (this.isConnected) {
            this.socket.send(JSON.stringify({
                type: 'command',
                command: command
            }));
        } else {
            this.appendOutput('Not connected to server', 'error-message');
        }
    }
    
    handleServerMessage(data) {
        switch(data.type) {
            case 'output':
                this.appendOutput(data.content, data.style || '');
                break;
            case 'clear':
                this.clearOutput();
                break;
            case 'message':
                this.displayMessage(data);
                break;
            case 'header':
                this.displayHeader(data.topic, data.round);
                break;
            case 'thinking':
                this.appendOutput(`${data.participant} is formulating response...`, 'thinking');
                break;
            case 'round_transition':
                this.displayRoundTransition(data.from_round, data.to_round);
                break;
            case 'final_consensus':
                this.displayFinalConsensus(data.content);
                break;
            case 'menu':
                this.displayMenu();
                break;
            case 'prompt':
                this.setPrompt(data.prompt || '$ ');
                break;
        }
        
        // Auto-scroll to bottom
        this.scrollToBottom();
    }
    
    appendOutput(content, className = '') {
        const div = document.createElement('div');
        div.textContent = content;
        if (className) {
            div.className = className;
        }
        this.output.appendChild(div);
    }
    
    clearOutput() {
        this.output.innerHTML = '';
    }
    
    displayMessage(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        
        const roleBadge = data.is_moderator ? '🎯 MOD' : '💭';
        const header = document.createElement('div');
        header.className = 'message-header';
        header.textContent = `${roleBadge} ${data.participant_model}`;
        
        const content = document.createElement('div');
        content.className = `message-content panel ${data.participant_id}`;
        content.textContent = data.content;
        
        messageDiv.appendChild(header);
        messageDiv.appendChild(content);
        this.output.appendChild(messageDiv);
    }
    
    displayHeader(topic, round) {
        this.appendOutput('', '');
        this.appendOutput('═══ ROUNDTABLE ═══', 'round-header');
        this.appendOutput(`Topic: ${topic}`, 'system-message');
        this.appendOutput(`Round: ${round}`, 'system-message');
        this.appendOutput('─'.repeat(80), 'separator');
    }
    
    displayRoundTransition(fromRound, toRound) {
        this.appendOutput('='.repeat(80), 'separator');
        this.appendOutput(`✓ Completed: ${fromRound}`, 'system-message');
        this.appendOutput(`→ Starting: ${toRound}`, 'system-message');
        this.appendOutput('='.repeat(80), 'separator');
    }
    
    displayFinalConsensus(content) {
        this.appendOutput('='.repeat(80), 'separator');
        this.appendOutput('═══ FINAL CONSENSUS ═══', 'round-header');
        this.appendOutput('='.repeat(80), 'separator');
        
        const consensusDiv = document.createElement('div');
        consensusDiv.className = 'final-consensus';
        consensusDiv.textContent = content;
        this.output.appendChild(consensusDiv);
    }
    
    displayMenu() {
        this.showWelcome();
    }
    
    setPrompt(prompt) {
        this.promptSpan.textContent = prompt;
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.output.scrollTop = this.output.scrollHeight;
        }, 10);
    }
}

// Initialize terminal when page loads
document.addEventListener('DOMContentLoaded', () => {
    new WebTerminal();
});