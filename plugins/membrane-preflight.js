import { appendFile, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const HOME = process.env.HOME || process.env.USERPROFILE || ".";
// Where the membrane/ toolkit lives. Override with MEMBRANE_HOME if you keep
// it somewhere other than ~/.config/opencode/membrane.
const MEM = process.env.MEMBRANE_HOME || path.join(HOME, ".config/opencode/membrane");
const STATE = path.join(
  process.env.XDG_STATE_HOME || path.join(HOME, ".local/state"),
  "opencode-membrane",
);
const FLAG = path.join(STATE, "preflight.flag");

const PREFLIGHT = [
  "[MEMBRANE PRE-FLIGHT] Activate the semipermeable membrane for this session?",
  "If YES: before reading/quoting any workspace file run",
  `  python3 ${MEM}/bin/membrane_check.py --workspace . <path> (exit 1 = do not open),`,
  "quote only output piped through membrane_filter.py, and use membrane_tail.py for logs.",
  "If NO: reply 'membrane off' and proceed normally.",
].join(" ");

function toast(client, msg, kind = "info") {
  client.tui.appendPrompt({ body: { text: msg } }).catch(() => {
    client.tui.showToast?.({ body: { message: msg, variant: kind } }).catch(() => {});
  });
}

export const MembranePreflight = async ({ client, directory }) => {
  let asked = false;
  let armed = false;

  const alreadyAsked = async (sessionID) => {
    try {
      const f = path.join(STATE, `asked-${sessionID}`);
      await readFile(f);
      return true;
    } catch {
      return false;
    }
  };
  const markAsked = async (sessionID) => {
    await mkdir(STATE, { recursive: true });
    await writeFile(path.join(STATE, `asked-${sessionID}`), new Date().toISOString());
  };

  return {
    event: async ({ event }) => {
      if (event.type === "session.idle") {
        const props = event.properties || {};
        const sessionID = props.sessionID;
        if (!sessionID || asked || armed) return;
        if (await alreadyAsked(sessionID)) return;
        asked = true;
        await markAsked(sessionID);
        toast(client, PREFLIGHT);
      }
      if (event.type === "session.deleted") {
        const props = event.properties || {};
        if (props.sessionID) {
          appendFile(path.join(STATE, "reset.log"), `reset ${props.sessionID} ${new Date().toISOString()}\n`).catch(() => {});
        }
      }
    },
    "chat.message": async (input, output) => {
      const text = (output.parts || [])
        .filter((p) => p.type === "text")
        .map((p) => p.text || "")
        .join(" ")
        .toLowerCase();
      if (!armed && /\bmembrane\b/.test(text) && /\b(on|activate|enable|yes|arm|start)\b/.test(text)) {
        armed = true;
        await mkdir(STATE, { recursive: true });
        await writeFile(FLAG, `armed ${new Date().toISOString()} dir=${directory}\n`);
        output.parts.unshift({
          type: "text",
          text:
            "[membrane ARMED - enforce for the whole session] Gate every file read with " +
            `python3 ${MEM}/bin/membrane_check.py --workspace . <path>; quote only output piped through ` +
            `${MEM}/bin/membrane_filter.py; logs only via membrane_tail.py. Hard denials: tuple/**, *.root, ` +
            "*.dst, *.ndst, *.p12, *.pem, *.key, .env*, .deid/**.",
        });
      }
    },
  };
};
