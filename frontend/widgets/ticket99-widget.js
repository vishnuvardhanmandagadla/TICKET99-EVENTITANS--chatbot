(function () {
  "use strict";

  const CONFIG = {
    apiUrl: "/api/ticket99/chat",
    leadsUrl: "/api/leads",
    clearUrl: "/api/clear",
    brandName: "Tickets99",
    prefix: "t99",
    primaryColor: "#f97316",
    secondaryColor: "#ef4444",
    gradient: "linear-gradient(135deg, #f97316, #ef4444)",
    position: "right",
    quickReplies: [
      { text: "Organize an event", icon: "\uD83C\uDFAD" },
      { text: "Find events", icon: "\uD83D\uDD0D" },
      { text: "Partnership", icon: "\uD83E\uDD1D" },
      { text: "Pricing", icon: "\uD83D\uDCB0" },
    ],
  };

  let sessionId = null;
  let isOpen = false;
  let isTyping = false;

  function injectStyles() {
    const style = document.createElement("style");
    style.textContent = `
      #${CONFIG.prefix}-toggle {
        position: fixed;
        bottom: 24px;
        ${CONFIG.position}: 24px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: ${CONFIG.gradient};
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 24px rgba(249,115,22,0.4);
        z-index: 99999;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.3s, box-shadow 0.3s;
      }
      #${CONFIG.prefix}-toggle:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 32px rgba(249,115,22,0.5);
      }
      #${CONFIG.prefix}-toggle svg {
        width: 28px;
        height: 28px;
        fill: white;
      }
      #${CONFIG.prefix}-window {
        position: fixed;
        bottom: 96px;
        ${CONFIG.position}: 24px;
        width: 380px;
        max-width: calc(100vw - 48px);
        height: 560px;
        max-height: calc(100vh - 120px);
        border-radius: 20px;
        overflow: hidden;
        z-index: 99998;
        display: none;
        flex-direction: column;
        background: rgba(255,255,255,0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.3);
        box-shadow: 0 8px 32px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      #${CONFIG.prefix}-window.open {
        display: flex;
        animation: ${CONFIG.prefix}-slideUp 0.3s ease-out;
      }
      @keyframes ${CONFIG.prefix}-slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
      }
      #${CONFIG.prefix}-header {
        background: ${CONFIG.gradient};
        color: white;
        padding: 16px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-shrink: 0;
      }
      #${CONFIG.prefix}-header-info {
        display: flex;
        align-items: center;
        gap: 12px;
      }
      #${CONFIG.prefix}-header-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: rgba(255,255,255,0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
      }
      #${CONFIG.prefix}-header h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }
      #${CONFIG.prefix}-header p {
        margin: 2px 0 0;
        font-size: 12px;
        opacity: 0.9;
      }
      #${CONFIG.prefix}-close {
        background: none;
        border: none;
        color: white;
        font-size: 24px;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 8px;
        line-height: 1;
      }
      #${CONFIG.prefix}-close:hover {
        background: rgba(255,255,255,0.15);
      }
      #${CONFIG.prefix}-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .${CONFIG.prefix}-msg {
        max-width: 85%;
        padding: 10px 14px;
        border-radius: 16px;
        font-size: 14px;
        line-height: 1.5;
        word-wrap: break-word;
      }
      .${CONFIG.prefix}-msg.bot {
        align-self: flex-start;
        background: rgba(255,255,255,0.9);
        border: 1px solid rgba(0,0,0,0.06);
        color: #1f2937;
        border-bottom-left-radius: 4px;
      }
      .${CONFIG.prefix}-msg.user {
        align-self: flex-end;
        background: ${CONFIG.gradient};
        color: white;
        border-bottom-right-radius: 4px;
      }
      .${CONFIG.prefix}-quick-replies {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding: 0 16px 8px;
      }
      .${CONFIG.prefix}-quick-btn {
        background: rgba(249,115,22,0.08);
        border: 1px solid rgba(249,115,22,0.2);
        color: ${CONFIG.primaryColor};
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s;
        white-space: nowrap;
      }
      .${CONFIG.prefix}-quick-btn:hover {
        background: ${CONFIG.primaryColor};
        color: white;
      }
      .${CONFIG.prefix}-typing {
        align-self: flex-start;
        padding: 12px 16px;
        background: rgba(255,255,255,0.9);
        border: 1px solid rgba(0,0,0,0.06);
        border-radius: 16px;
        border-bottom-left-radius: 4px;
        display: flex;
        gap: 4px;
      }
      .${CONFIG.prefix}-typing span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #9ca3af;
        animation: ${CONFIG.prefix}-bounce 1.4s infinite;
      }
      .${CONFIG.prefix}-typing span:nth-child(2) { animation-delay: 0.2s; }
      .${CONFIG.prefix}-typing span:nth-child(3) { animation-delay: 0.4s; }
      @keyframes ${CONFIG.prefix}-bounce {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-8px); }
      }
      #${CONFIG.prefix}-input-area {
        display: flex;
        padding: 12px 16px;
        gap: 8px;
        border-top: 1px solid rgba(0,0,0,0.06);
        background: rgba(255,255,255,0.7);
        flex-shrink: 0;
      }
      #${CONFIG.prefix}-input {
        flex: 1;
        border: 1px solid rgba(0,0,0,0.1);
        border-radius: 24px;
        padding: 10px 16px;
        font-size: 14px;
        outline: none;
        background: white;
        transition: border-color 0.2s;
      }
      #${CONFIG.prefix}-input:focus {
        border-color: ${CONFIG.primaryColor};
      }
      #${CONFIG.prefix}-send {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        background: ${CONFIG.gradient};
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        transition: transform 0.2s;
      }
      #${CONFIG.prefix}-send:hover { transform: scale(1.05); }
      #${CONFIG.prefix}-send:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
      #${CONFIG.prefix}-send svg {
        width: 18px;
        height: 18px;
        fill: white;
      }
      .${CONFIG.prefix}-lead-form {
        padding: 16px;
        background: rgba(249,115,22,0.04);
        border: 1px solid rgba(249,115,22,0.15);
        border-radius: 12px;
        margin: 0 16px 8px;
      }
      .${CONFIG.prefix}-lead-form h4 {
        margin: 0 0 12px;
        font-size: 14px;
        color: #1f2937;
      }
      .${CONFIG.prefix}-lead-form input,
      .${CONFIG.prefix}-lead-form select {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid rgba(0,0,0,0.1);
        border-radius: 8px;
        font-size: 13px;
        margin-bottom: 8px;
        box-sizing: border-box;
        outline: none;
      }
      .${CONFIG.prefix}-lead-form input:focus,
      .${CONFIG.prefix}-lead-form select:focus {
        border-color: ${CONFIG.primaryColor};
      }
      .${CONFIG.prefix}-lead-submit {
        width: 100%;
        padding: 10px;
        background: ${CONFIG.gradient};
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        margin-top: 4px;
      }
      .${CONFIG.prefix}-lead-submit:hover { opacity: 0.9; }
      #${CONFIG.prefix}-powered {
        text-align: center;
        padding: 6px;
        font-size: 11px;
        color: #9ca3af;
        flex-shrink: 0;
      }
    `;
    document.head.appendChild(style);
  }

  function createWidget() {
    // Toggle button
    const toggle = document.createElement("button");
    toggle.id = `${CONFIG.prefix}-toggle`;
    toggle.innerHTML = `<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>`;
    toggle.onclick = toggleChat;
    document.body.appendChild(toggle);

    // Chat window
    const win = document.createElement("div");
    win.id = `${CONFIG.prefix}-window`;
    win.innerHTML = `
      <div id="${CONFIG.prefix}-header">
        <div id="${CONFIG.prefix}-header-info">
          <div id="${CONFIG.prefix}-header-avatar">\uD83C\uDFAB</div>
          <div>
            <h3>${CONFIG.brandName}</h3>
            <p>AI Assistant</p>
          </div>
        </div>
        <button id="${CONFIG.prefix}-close" onclick="document.getElementById('${CONFIG.prefix}-toggle').click()">&times;</button>
      </div>
      <div id="${CONFIG.prefix}-messages"></div>
      <div id="${CONFIG.prefix}-quick-container"></div>
      <div id="${CONFIG.prefix}-input-area">
        <input id="${CONFIG.prefix}-input" type="text" placeholder="Type a message..." autocomplete="off" />
        <button id="${CONFIG.prefix}-send">
          <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
      <div id="${CONFIG.prefix}-powered">Powered by AI</div>
    `;
    document.body.appendChild(win);

    // Event listeners
    document.getElementById(`${CONFIG.prefix}-input`).addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    document.getElementById(`${CONFIG.prefix}-send`).addEventListener("click", sendMessage);
  }

  function toggleChat() {
    isOpen = !isOpen;
    const win = document.getElementById(`${CONFIG.prefix}-window`);
    if (isOpen) {
      win.classList.add("open");
      const msgs = document.getElementById(`${CONFIG.prefix}-messages`);
      if (msgs.children.length === 0) {
        addBotMessage(`Hey there! Welcome to ${CONFIG.brandName} \uD83D\uDC4B How can I help you today?`);
        showQuickReplies(CONFIG.quickReplies);
      }
      document.getElementById(`${CONFIG.prefix}-input`).focus();
    } else {
      win.classList.remove("open");
    }
  }

  function addBotMessage(text) {
    const msgs = document.getElementById(`${CONFIG.prefix}-messages`);
    const div = document.createElement("div");
    div.className = `${CONFIG.prefix}-msg bot`;
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function addUserMessage(text) {
    const msgs = document.getElementById(`${CONFIG.prefix}-messages`);
    const div = document.createElement("div");
    div.className = `${CONFIG.prefix}-msg user`;
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function showTyping() {
    if (isTyping) return;
    isTyping = true;
    const msgs = document.getElementById(`${CONFIG.prefix}-messages`);
    const div = document.createElement("div");
    div.className = `${CONFIG.prefix}-typing`;
    div.id = `${CONFIG.prefix}-typing-indicator`;
    div.innerHTML = "<span></span><span></span><span></span>";
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function hideTyping() {
    isTyping = false;
    const el = document.getElementById(`${CONFIG.prefix}-typing-indicator`);
    if (el) el.remove();
  }

  function showQuickReplies(replies) {
    const container = document.getElementById(`${CONFIG.prefix}-quick-container`);
    container.innerHTML = "";
    const wrap = document.createElement("div");
    wrap.className = `${CONFIG.prefix}-quick-replies`;
    replies.forEach((r) => {
      const btn = document.createElement("button");
      btn.className = `${CONFIG.prefix}-quick-btn`;
      btn.textContent = `${r.icon} ${r.text}`;
      btn.onclick = () => {
        container.innerHTML = "";
        sendMessage(r.text);
      };
      wrap.appendChild(btn);
    });
    container.appendChild(wrap);
  }

  function showLeadForm(type) {
    const container = document.getElementById(`${CONFIG.prefix}-quick-container`);
    const isPartner = type === "partner";
    container.innerHTML = `
      <div class="${CONFIG.prefix}-lead-form">
        <h4>${isPartner ? "Partnership Inquiry" : "Get Started"}</h4>
        <input type="text" id="${CONFIG.prefix}-lead-name" placeholder="Your Name" />
        <input type="email" id="${CONFIG.prefix}-lead-email" placeholder="Email Address" />
        <input type="tel" id="${CONFIG.prefix}-lead-phone" placeholder="Phone Number" />
        ${isPartner
          ? `<select id="${CONFIG.prefix}-lead-type">
              <option value="">Partnership Type</option>
              <option value="sponsor">Sponsor</option>
              <option value="venue">Venue Partner</option>
              <option value="corporate">Corporate</option>
              <option value="reseller">Reseller</option>
            </select>`
          : `<input type="text" id="${CONFIG.prefix}-lead-event" placeholder="Event Type (optional)" />`
        }
        <button class="${CONFIG.prefix}-lead-submit" onclick="window._${CONFIG.prefix}SubmitLead('${type}')">Submit</button>
      </div>
    `;
  }

  window[`_${CONFIG.prefix}SubmitLead`] = async function (type) {
    const name = document.getElementById(`${CONFIG.prefix}-lead-name`)?.value?.trim();
    const email = document.getElementById(`${CONFIG.prefix}-lead-email`)?.value?.trim();
    const phone = document.getElementById(`${CONFIG.prefix}-lead-phone`)?.value?.trim();

    if (!name || !email) {
      alert("Please enter your name and email.");
      return;
    }

    const leadData = { name, email, phone, type, brand: "ticket99" };

    if (type === "partner") {
      leadData.partnerType = document.getElementById(`${CONFIG.prefix}-lead-type`)?.value;
    } else {
      leadData.eventType = document.getElementById(`${CONFIG.prefix}-lead-event`)?.value;
    }

    try {
      await fetch(CONFIG.leadsUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(leadData),
      });
      document.getElementById(`${CONFIG.prefix}-quick-container`).innerHTML = "";
      addBotMessage("Thanks! Our team will reach out within 24 hours. Is there anything else I can help with?");
    } catch (e) {
      addBotMessage("Sorry, couldn't submit your details. Please try emailing support@tickets99.com.");
    }
  };

  async function sendMessage(text) {
    const input = document.getElementById(`${CONFIG.prefix}-input`);
    const message = text || input.value.trim();
    if (!message || isTyping) return;

    input.value = "";
    addUserMessage(message);

    // Clear quick replies
    document.getElementById(`${CONFIG.prefix}-quick-container`).innerHTML = "";

    showTyping();

    try {
      const resp = await fetch(CONFIG.apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, sessionId: sessionId }),
      });

      const data = await resp.json();
      hideTyping();

      if (data.success) {
        sessionId = data.sessionId;
        addBotMessage(data.message);

        if (data.showForm) {
          showLeadForm(data.showForm);
        }
      } else {
        addBotMessage("Sorry, something went wrong. Please try again!");
      }
    } catch (e) {
      hideTyping();
      addBotMessage("Connection error. Please check your internet and try again.");
    }
  }

  // Initialize
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      injectStyles();
      createWidget();
    });
  } else {
    injectStyles();
    createWidget();
  }
})();
