// Project Lisa - Interactive Visual Model Web Logic

const avatarContainer = document.getElementById("avatarContainer");
const bubbleText = document.getElementById("bubbleText");
const statusText = document.getElementById("statusText");
const chatContainer = document.getElementById("chatContainer");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
const voicePlayer = document.getElementById("voicePlayer");

let isSpeaking = false;
let isRecording = false;
let recognition = null;

// Initialize Speech Recognition if browser supports it
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'bn-BD, en-US';

  recognition.onstart = () => {
    isRecording = true;
    micBtn.classList.add('recording');
    statusText.innerText = "Listening...";
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    userInput.value = transcript;
    sendMessage(transcript);
  };

  recognition.onerror = (e) => {
    console.error("Speech recognition error:", e);
    stopRecording();
  };

  recognition.onend = () => {
    stopRecording();
  };
}

function stopRecording() {
  isRecording = false;
  micBtn.classList.remove('recording');
  if (!isSpeaking) {
    statusText.innerText = "Standing by";
  }
}

if (micBtn) {
  micBtn.addEventListener("click", () => {
    if (!recognition) {
      alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
      return;
    }
    if (isRecording) {
      recognition.stop();
    } else {
      recognition.start();
    }
  });
}

// Append Chat Message
function appendMessage(text, sender) {
  const div = document.createElement("div");
  div.className = `msg ${sender}`;
  div.innerText = text;
  chatContainer.appendChild(div);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Set Lisa's Speaking State
function setLisaSpeaking(text, audioUrl = null) {
  isSpeaking = true;
  avatarContainer.classList.add("speaking");
  statusText.innerText = "Lisa Speaking...";
  bubbleText.innerText = "";

  // Smooth typing effect for speech bubble
  let i = 0;
  const speed = 25; // ms per char
  const timer = setInterval(() => {
    if (i < text.length) {
      bubbleText.innerText += text.charAt(i);
      i++;
    } else {
      clearInterval(timer);
    }
  }, speed);

  // If audio is provided, play it and sync avatar animation
  if (audioUrl) {
    voicePlayer.src = audioUrl;
    voicePlayer.play().catch(e => console.warn("Audio playback error:", e));
    voicePlayer.onended = () => {
      setLisaIdle();
    };
  } else {
    // If no audio, reset to idle after reasonable duration
    const readDuration = Math.max(3000, text.length * 50);
    setTimeout(() => {
      setLisaIdle();
    }, readDuration);
  }
}

// Set Lisa to Idle / Standing by
function setLisaIdle() {
  isSpeaking = false;
  avatarContainer.classList.remove("speaking");
  statusText.innerText = "Standing by";
}

// Send Message to Lisa Backend
async function sendMessage(text) {
  const message = text || userInput.value.trim();
  if (!message) return;

  appendMessage(message, "user");
  userInput.value = "";
  statusText.innerText = "Thinking...";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message }),
    });

    const data = await res.json();
    const reply = data.reply || "I processed your request, Boss.";
    appendMessage(reply, "lisa");

    // Activate visual avatar speech with audio if returned
    setLisaSpeaking(reply, data.audio_url || null);
  } catch (err) {
    console.error("Error communicating with Lisa:", err);
    appendMessage("Sorry Boss, an error occurred while connecting to my core.", "lisa");
    statusText.innerText = "Standing by";
  }
}

sendBtn.addEventListener("click", () => sendMessage());
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});

function sendQuickAction(actionText) {
  sendMessage(actionText);
}
