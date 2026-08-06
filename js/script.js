document.addEventListener('DOMContentLoaded', () => {
    const music = document.getElementById('bg-music');
    const musicBtn = document.getElementById('music-toggle');

    music.volume = 0.2;

    musicBtn.addEventListener('click', () => {
        if (music.paused) {
            music.play();
            musicBtn.innerText = '🔊';
        } else {
            music.pause();
            musicBtn.innerText = '🔇';
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    
    // ─── gerenciador de estado ──────────────────────────────────────────────────────────
    let messages = [];
    let isLoading = false;
    let hasMessages = false;

    // ─── elementos da interface ─────────────────────────────────────────────────────────────
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
        'Me diga todos os itens que podem ser vendidos.',
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

    // ─── Inicialização ───────────────────────────────────────────────────────────
    
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

    // ─── Lógica do Chat ───────────────────────────────────────────────────────────────

    async function handleSend(textOverride) {
        const text = textOverride || ui.chatInput.value.trim();
        if (!text || isLoading) return;

        // Trasição do estado de boas-vindas para o histórico de chat
        if (!hasMessages) {
            hasMessages = true;
            ui.welcomeState.style.display = 'none';
            ui.chatHistory.style.display = 'block';
            ui.inlineSuggestions.style.display = 'flex';
        }

        // Adicionar mensagem do usuário
        appendMessage('user', text);
        
        // Resetar input e atualizar layout
        ui.chatInput.value = '';
        updateInputLayout();
        
        // Mostrar indicador de digitação e desabilitar botão de envio
        isLoading = true;
        updateSendButtonState();
        ui.inlineSuggestions.style.display = 'none'; // esconder chips durante a resposta
        ui.typingIndicator.style.display = 'flex';
        scrollToBottom();

        // Chamada da API para obter a resposta do backend
        try {
            const response = await fetch('http://127.0.0.1:5000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });

            if (!response.ok) {
                throw new Error(`Erro http! status: ${response.status}`);
            }

            const data = await response.json();

            // limpar estado de carregamento e mostrar chips novamente
            isLoading = false;
            ui.typingIndicator.style.display = 'none';
            ui.inlineSuggestions.style.display = 'flex'; // Show chips again
            
            // Adicionar resposta do assistente
            appendMessage('assistant', data.response);
            updateSendButtonState();

        } catch (error) {
            console.error("Erro na Conexão com a API:", error);
            
            // limpar estado de carregamento e mostrar chips novamente
            isLoading = false;
            ui.typingIndicator.style.display = 'none';
            ui.inlineSuggestions.style.display = 'flex';
            
            appendMessage('assistant', "Error: Não conseguimos conectar ao backend. Certifique-se de que 05_api.py está em execução.");
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

    // ─── Interações com a UI ──────────────────────────────────────────────────────────

    function setupEventListeners() {
        // Auto resize
        ui.chatInput.addEventListener('input', updateInputLayout);

        // Entrada de teclado (Enter para enviar, Shift+Enter para nova linha)
        ui.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        });

        // Botão de enviar
        ui.sendBtn.addEventListener('click', () => handleSend());
    }

    function updateInputLayout() {
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

    // ─── Sistema de Partículas ──────────────────────────────────────────────────────────
    
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

    // Rodar a aplicação
    init();
});