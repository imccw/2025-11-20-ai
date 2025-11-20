const translateBtn = document.getElementById("translate-btn");
const inputText = document.getElementById("input-text");
const outputText = document.getElementById("output-text");
const statusText = document.getElementById("status-text");
const styleSelect = document.getElementById("style-select");
const TRANSLATOR_API_URL = window.TRANSLATOR_API_URL || "http://localhost:8000";
const TRANSLATE_ENDPOINT = new URL("/translate", TRANSLATOR_API_URL).href;

const STYLE_INSTRUCTIONS = {
  default: "Translate the sentence accurately with a neutral, helpful tone.",
  "hk-mafia-90s":
    "Translate like a Hong Kong mafia member in the 1990s: a little bit rude, confident, but never insulting beyond playful toughness.",
};

async function translate() {
  const selectedStyle = styleSelect.value;
  const payload = {
    inputLanguage: document.getElementById("input-lang").value,
    outputLanguage: document.getElementById("output-lang").value,
    text: inputText.value.trim(),
    style: selectedStyle,
    instruction: STYLE_INSTRUCTIONS[selectedStyle],
  };

  if (!payload.text) {
    statusText.textContent = "Please enter text to translate.";
    return;
  }

  translateBtn.disabled = true;
  statusText.textContent = "Translating…";

  try {
    const response = await fetch(TRANSLATE_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("Translation API not available");
    }

    const { translation } = await response.json();
    outputText.value = translation || "No translation received.";
    statusText.textContent = "Translation complete.";
  } catch (err) {
    outputText.value = selectedStyle === "hk-mafia-90s"
      ? "我鍾意寫程式，唔好搞我喺度。"
      : "Ich programmiere gerne.";
    statusText.textContent =
      "Running without backend; showing a style-aware placeholder translation.";
    console.error(err);
  } finally {
    translateBtn.disabled = false;
  }
}

translateBtn.addEventListener("click", translate);
