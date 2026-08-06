/**
 * LoreWeaver - Hollow Knight Knowledge AI
 * Vanilla JavaScript implementation - API Connected
 */

document.addEventListener('DOMContentLoaded', () => {
    const music = document.getElementById('bg-music');
    const musicBtn = document.getElementById('music-toggle');

    // Set volume to 20% so it's a pleasant background ambiance
    music.volume = 0.2;

    musicBtn.addEventListener('click', () => {
        if (music.paused) {
            music.play();
            musicBtn.innerText = '🔇';
        } else {
            music.pause();
            musicBtn.innerText = '🔊';
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    
    // ─── State Management ──────────────────────────────────────────────────────────
    let messages = [];
    let isLoading = false;
    let hasMessages = false;

    // ─── DOM Elements ─────────────────────────────────────────────────────────────
    const ui = {
        welcomeState: document.getElementById('welcome-state'),
        chatHistory: document.getElementById('chat-history'),
        chatAnchor: document.getElementById('chat-anchor'),
        typingIndicator: document.getElementById('typing-indicator'),
        chatInput: document.getElementById('chat-input'),
        sendBtn: document.getElementById('send-btn'),
        sendIcon: document.getElementById('send-icon'),
        welcomeSuggestions: document.getElementById('welcome-suggestions'),
        inlineSuggestions: document.getElementById('inline-suggestions'),
    };

    const SUGGESTIONS = [
        'Me diga todos os itens que podem ser vendidos?',
        'Me diga todos os bosses e suas localizações.',
        'Quais são todas as areas do jogo?',
        'Me conte mais sobre a Hornet.',
        'Quais são os lugares que o Quirrel aparece?',
        'Me conte mais sobre o cavaleiro.',
    ];

    // ─── SVG Avatar Template ──────────────────────────────────────────────────────
    const oracleAvatarSVG = `
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="16" r="15" stroke="#2A3440" stroke-width="1" fill="#11151B" />
            <circle cx="16" cy="16" r="12" stroke="#8EC5FF" stroke-width="0.5" stroke-opacity="0.3" fill="none" stroke-dasharray="3 2" />
            <circle cx="16" cy="16" r="6" stroke="#8EC5FF" stroke-width="0.8" stroke-opacity="0.5" fill="none" />
            <line x1="16" y1="4" x2="16" y2="10" stroke="#8EC5FF" stroke-width="0.8" stroke-opacity="0.6" />
            <line x1="16" y1="22" x2="16" y2="28" stroke="#8EC5FF" stroke-width="0.8" stroke-opacity="0.6" />
            <line x1="4" y1="16" x2="10" y2="16" stroke="#8EC5FF" stroke-width="0.8" stroke-opacity="0.6" />
            <line x1="22" y1="16" x2="28" y2="16" stroke="#8EC5FF" stroke-width="0.8" stroke-opacity="0.6" />
            <circle cx="16" cy="16" r="2" fill="#8EC5FF" fill-opacity="0.7" />
            <circle cx="16" cy="4" r="1" fill="#8EC5FF" fill-opacity="0.4" />
            <circle cx="16" cy="28" r="1" fill="#8EC5FF" fill-opacity="0.4" />
            <circle cx="4" cy="16" r="1" fill="#8EC5FF" fill-opacity="0.4" />
            <circle cx="28" cy="16" r="1" fill="#8EC5FF" fill-opacity="0.4" />
        </svg>
    `;

    // ─── Initialization ───────────────────────────────────────────────────────────
    
    function init() {
        renderSuggestions();
        initParticles();
        setupEventListeners();
    }

    function renderSuggestions() {
        // Welcome State Chips
        SUGGESTIONS.forEach(text => {
            const btn = document.createElement('button');
            btn.className = 'suggestion-chip';
            btn.textContent = text;
            btn.addEventListener('click', () => handleSend(text));
            ui.welcomeSuggestions.appendChild(btn);
        });

        // Inline Chips (only first 4)
        SUGGESTIONS.slice(0, 4).forEach(text => {
            const btn = document.createElement('button');
            btn.className = 'suggestion-chip';
            btn.textContent = text;
            btn.addEventListener('click', () => handleSend(text));
            ui.inlineSuggestions.appendChild(btn);
        });
    }

    // ─── Chat Logic ───────────────────────────────────────────────────────────────

    async function handleSend(textOverride) {
        const text = textOverride || ui.chatInput.value.trim();
        if (!text || isLoading) return;

        // Transition from Welcome to Chat if first message
        if (!hasMessages) {
            hasMessages = true;
            ui.welcomeState.style.display = 'none';
            ui.chatHistory.style.display = 'block';
            ui.inlineSuggestions.style.display = 'flex';
        }

        // Add User Message
        appendMessage('user', text);
        
        // Reset Input
        ui.chatInput.value = '';
        updateInputLayout();
        
        // Set Loading State
        isLoading = true;
        updateSendButtonState();
        ui.inlineSuggestions.style.display = 'none'; // Hide inline chips while loading
        ui.typingIndicator.style.display = 'flex';
        scrollToBottom();

        // API Call to Python Backend
        try {
            const response = await fetch('http://127.0.0.1:5000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Clear loading state
            isLoading = false;
            ui.typingIndicator.style.display = 'none';
            ui.inlineSuggestions.style.display = 'flex'; // Show chips again
            
            // Render backend response
            appendMessage('assistant', data.response);
            updateSendButtonState();

        } catch (error) {
            console.error("API Connection Error:", error);
            
            // Clear loading state and show error message
            isLoading = false;
            ui.typingIndicator.style.display = 'none';
            ui.inlineSuggestions.style.display = 'flex';
            
            appendMessage('assistant', "Error: Could not connect to the LoreWeaver backend. Make sure 05_api.py is running.");
            updateSendButtonState();
        }
    }

    function appendMessage(role, content) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `msg-enter ${role === 'user' ? 'user-message' : 'assistant-message'}`;

        if (role === 'user') {
            msgDiv.innerHTML = `
                <div class="user-bubble">
                    <p>${escapeHTML(content)}</p>
                </div>
            `;
        } else {
            // We remove the wrapping <p> tag from the template because marked.parse() 
            // automatically generates <p>, <h1>, <ul>, etc., based on the content.
            msgDiv.innerHTML = `
                <div class="avatar-glow avatar-wrapper">
                    ${oracleAvatarSVG}
                </div>
                <div class="assistant-bubble markdown-rendered">
                    ${marked.parse(content)}
                </div>
            `;
        }

        ui.chatHistory.insertBefore(msgDiv, ui.typingIndicator);
        scrollToBottom();
    }

    // ─── UI Interactions ──────────────────────────────────────────────────────────

    function setupEventListeners() {
        // Auto-resize textarea
        ui.chatInput.addEventListener('input', updateInputLayout);

        // Handle Enter key
        ui.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        });

        // Send Button
        ui.sendBtn.addEventListener('click', () => handleSend());
    }

    function updateInputLayout() {
        // Auto resize height
        ui.chatInput.style.height = 'auto';
        ui.chatInput.style.height = Math.min(ui.chatInput.scrollHeight, 140) + 'px';
        
        updateSendButtonState();
    }

    function updateSendButtonState() {
        const hasText = ui.chatInput.value.trim().length > 0;
        
        if (hasText && !isLoading) {
            ui.sendBtn.disabled = false;
            ui.sendBtn.classList.add('active');
            ui.sendIcon.setAttribute('opacity', '1');
        } else {
            ui.sendBtn.disabled = true;
            ui.sendBtn.classList.remove('active');
            ui.sendIcon.setAttribute('opacity', '0.3');
        }
    }

    function scrollToBottom() {
        ui.chatAnchor.scrollIntoView({ behavior: 'smooth' });
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }

    // ─── Particle System ──────────────────────────────────────────────────────────
    
    function initParticles() {
        const canvas = document.getElementById('particles');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let raf;
        const particles = [];

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        resize();
        window.addEventListener('resize', resize);

        const spawn = () => {
            if (particles.length < 60 && Math.random() < 0.25) {
                particles.push({
                    x: Math.random() * canvas.width,
                    y: canvas.height + 4,
                    vx: (Math.random() - 0.5) * 0.3,
                    vy: -(Math.random() * 0.4 + 0.15),
                    alpha: Math.random() * 0.4 + 0.1,
                    size: Math.random() * 1.5 + 0.5,
                    decay: Math.random() * 0.0008 + 0.0003,
                });
            }
        };

        const draw = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            spawn();

            for (let i = particles.length - 1; i >= 0; i--) {
                const p = particles[i];
                p.x += p.vx;
                p.y += p.vy;
                p.alpha -= p.decay;

                if (p.alpha <= 0 || p.y < -10) {
                    particles.splice(i, 1);
                    continue;
                }

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(142, 197, 255, ${p.alpha})`;
                ctx.fill();
            }

            raf = requestAnimationFrame(draw);
        };

        draw();
    }

    // Run application
    init();
});