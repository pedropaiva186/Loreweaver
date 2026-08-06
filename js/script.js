/**
 * LoreWeaver - Hollow Knight Knowledge AI
 * Vanilla JavaScript implementation
 */

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

    // ─── Mock Data & Responses ────────────────────────────────────────────────────
    const MOCK_RESPONSES = {
        default: `The knowledge graph contains deep connections across Hallownest's history. Could you ask me about a specific character, location, or event? I'll draw from the wiki's full structure to give you a precise answer.`,
        'pale king': `The Pale King is the ruler of Hallownest and one of the five great Pale Beings. He arrived in the ancient world as a Wyrm — an immense creature of light — and shed that form to assume a kingly shape. He built Hallownest from a crossroads of ancient fungal paths, bringing civilisation to the bugs who inhabited it by giving them minds and language.\n\nHis greatest act — and arguably his greatest sin — was the creation of the Hollow Knight: a Vessel born from his own essence and the Void, designed to contain the Radiance's Infection within a perfect, mindless shell. That plan ultimately failed.`,
        void: `The Void is a formless, lightless substance that exists beneath Hallownest in a place called the Abyss. It predates the kingdom itself. The Pale King harvested it to create Vessels: empty vessels of pure Void encased in shells, intended to contain and seal the Radiance.\n\nThe Void is antithetical to light and, by extension, to the Radiance. The protagonist — the Knight — is themselves a Vessel composed of Void, which gives them unique resistance to the Infection and the ability to wield the Dream Nail.`,
        hallownest: `Hallownest was an ancient kingdom built by the Pale King in a vast cavern system deep underground. At its height it was a marvel of civilisation: insects with cognition, language, and culture, served by a vast infrastructure of roads, lifts, and city districts.\n\nThe kingdom fell to the Radiance's Infection — a plague of golden light that consumed the minds of all life connected to the Pale King's soul. Most of Hallownest now lies silent and ruined, frozen in time by a barrier the Pale King constructed to contain the outbreak.`,
        hornet: `Hornet is the daughter of the Pale King and Herrah the Beast, one of the Dreamers who sealed the Hollow Knight's temple. She serves as a guardian of Hallownest's secrets and as a recurring foil to the Knight throughout their journey.\n\nShe wields a needle and thread with lethal precision, using Silk as both weapon and binding. Her motivations are complex: she tests the Knight's worth before allowing them deeper into the kingdom, but ultimately aids them in confronting the Infection.`,
        infection: `The Infection originates from the Radiance, a moth-god and the first source of light and consciousness in the ancient world. When the Pale King brought his own light to the kingdom and the moths forsook the Radiance — letting her fade from memory — she turned to a plague as a means of reclaiming what she lost.\n\nThe Infection manifests as golden, glowing spores that invade the minds of any creature with a soul. It does not destroy — it overwhelms, filling minds with light and obsession until the host loses independent will.`,
        dream: `The Dream Realm is a plane of memory and consciousness accessible through the Dream Nail, an artefact that can read thoughts and pierce the veil between the waking world and the psychic residue left by the dead.\n\nWithin it exist Dream Warriors — powerful fighters whose spirits have not moved on — and the memories of those who lived and died in Hallownest. The Radiance herself inhabits a deep layer of the Dream Realm, which is why the Dream Nail is ultimately necessary to confront her.`,
    };

    const SUGGESTIONS = [
        'Who is the Pale King?',
        'Explain the Void.',
        'What happened to Hallownest?',
        'Tell me about Hornet.',
        'Who created the Infection?',
        'Explain the Dream Realm.',
    ];

    function getMockResponse(input) {
        const lower = input.toLowerCase();
        if (lower.includes('pale king') || lower.includes('king')) return MOCK_RESPONSES['pale king'];
        if (lower.includes('void') || lower.includes('abyss')) return MOCK_RESPONSES['void'];
        if (lower.includes('hallownest') || lower.includes('happened')) return MOCK_RESPONSES['hallownest'];
        if (lower.includes('hornet')) return MOCK_RESPONSES['hornet'];
        if (lower.includes('infection') || lower.includes('radiance') || lower.includes('created')) return MOCK_RESPONSES['infection'];
        if (lower.includes('dream')) return MOCK_RESPONSES['dream'];
        return MOCK_RESPONSES['default'];
    }

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

    function handleSend(textOverride) {
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

        // Simulate Network Latency
        const delay = 800 + Math.random() * 700;
        setTimeout(() => {
            isLoading = false;
            ui.typingIndicator.style.display = 'none';
            ui.inlineSuggestions.style.display = 'flex'; // Show chips again
            
            appendMessage('assistant', getMockResponse(text));
            updateSendButtonState();
        }, delay);
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
                <div class="assistant-bubble">
                    <p>${escapeHTML(content)}</p>
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