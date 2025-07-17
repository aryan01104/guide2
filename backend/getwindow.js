import { execSync } from "child_process";

export function getActiveWindowTitle() {
  const script = `
    tell application "System Events"
      set frontApp to first application process whose frontmost is true
      tell frontApp
        try
          set winTitle to value of attribute "AXTitle" of front window
        on error
          set winTitle to "Unknown"
        end try
      end tell
    end tell
    return winTitle
  `;

  try {
    const result = execSync(`osascript -e '${script}'`).toString().trim();
    return result;
  } catch {
    return "Unknown";
  }
}
