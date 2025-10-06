"""Reusable client-side scripts for the FastHTML UI."""

from __future__ import annotations

from fasthtml.common import Script

recording_script = Script(
    """
(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;
    let isRecording = false;
    const defaultSelector = 'input[name="message"]';

    const setButtonState = (button, active) => {
        if (!button) return;
        if (active) {
            button.textContent = '⏹ Stop Recording';
            button.classList.remove('bg-green-500', 'hover:bg-green-600');
            button.classList.add('bg-red-500', 'hover:bg-red-600');
        } else {
            button.textContent = '🎤 Voice Input';
            button.classList.remove('bg-red-500', 'hover:bg-red-600');
            button.classList.add('bg-green-500', 'hover:bg-green-600');
        }
    };

    const resolveTarget = (button) => {
        if (!button) return defaultSelector;
        const selector = button.dataset.target;
        return selector && selector.trim() ? selector : defaultSelector;
    };

    window.startRecording = (button) => {
        if (!SpeechRecognition) {
            alert('Speech recognition not supported in this browser.');
            return;
        }

        if (isRecording && recognition) {
            recognition.stop();
            return;
        }

        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        const selector = resolveTarget(button);
        const messageField = document.querySelector(selector);

        recognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                transcript += event.results[i][0].transcript;
            }
            const cleaned = transcript.trim();
            if (messageField) {
                messageField.value = cleaned;
                messageField.focus();
            }
        };

        recognition.onerror = () => {
            setButtonState(button, false);
            isRecording = false;
        };

        recognition.onend = () => {
            setButtonState(button, false);
            isRecording = false;
        };

        recognition.start();
        setButtonState(button, true);
        isRecording = true;
    };
})();
    """
)

__all__ = ["recording_script"]
