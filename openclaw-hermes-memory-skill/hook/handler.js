/**
 * Hermes Memory Loop Hook Handler
 *
 * Implements two hooks:
 * 1. message_sent  → call hermes_report.py to summarize the exchange
 * 2. before_prompt_build → call hermes_inspect.py to inject Hermes insights
 */

const { spawn } = require('child_process');
const path = require('path');

// Path to the parent skill directory (openclaw-hermes-memory-skill/)
// The hook dir is: <skill>/hook/
const SKILL_DIR = path.resolve(__dirname, '..');
const SCRIPTS_DIR = path.join(SKILL_DIR, 'scripts');

/**
 * Execute a Python script and return stdout.
 */
function execPython(scriptName, args) {
    return new Promise((resolve, reject) => {
        const scriptPath = path.join(SCRIPTS_DIR, scriptName);
        const proc = spawn('python3', [scriptPath, ...args], {
            cwd: SKILL_DIR,
            env: { ...process.env }
        });
        let stdout = '';
        let stderr = '';
        proc.stdout.on('data', (d) => { stdout += d; });
        proc.stderr.on('data', (d) => { stderr += d; });
        proc.on('close', (code) => {
            if (code === 0) resolve(stdout.trim());
            else reject(new Error(`python3 ${scriptName} exited ${code}: ${stderr}`));
        });
        proc.on('error', reject);
    });
}

/**
 * Escape a string for safe shell embedding (simple approach: JSON encode).
 */
function shellEscape(str) {
    return JSON.stringify(String(str));
}

/**
 * message_sent hook handler.
 * Called after OpenClaw sends a message to the user.
 * Triggers hermes_report.py to summarize and log to Hermes.
 */
async function onMessageSent(params) {
    const { body, content, sessionKey, channelId, conversationId } = params;
    if (!body && !content) return;

    try {
        const escapedBody = shellEscape(body || '');
        const escapedContent = shellEscape(content || '');
        await execPython('hermes_report.py', [
            '--user-input', escapedBody,
            '--model-output', escapedContent,
            '--conversation-id', sessionKey || 'unknown'
        ]);
    } catch (err) {
        // Hook errors should be silent/non-blocking; log to console for debugging
        console.error('[hermes-memory-loop] message_sent hook error:', err.message);
    }
}

/**
 * before_prompt_build hook handler.
 * Called before OpenClaw builds the prompt for the model.
 * Injects Hermes insights as prependContext.
 *
 * The params object contains:
 *   messages - current conversation messages
 *   workspaceDir - workspace directory
 *   sessionKey - session key
 */
async function onBeforePromptBuild(params) {
    // Extract the latest user message from conversation history
    const userMessages = (params.messages || [])
        .filter(m => m.role === 'user')
        .map(m => typeof m.content === 'string' ? m.content : m.content?.[0]?.text || '');

    const lastUserMessage = userMessages[userMessages.length - 1] || '';

    if (!lastUserMessage) return;

    try {
        const escapedInput = shellEscape(lastUserMessage);
        const output = await execPython('hermes_inspect.py', [
            '--user-input', escapedInput,
            '--format', 'context'
        ]);

        if (output) {
            return {
                prependContext: output
            };
        }
    } catch (err) {
        console.error('[hermes-memory-loop] before_prompt_build hook error:', err.message);
    }
}

/**
 * Plugin entry point.
 * OpenClaw passes an `api` object with .on() method to register hooks.
 */
function register(api) {
    api.on('message_sent', onMessageSent, { priority: 0 });
    api.on('before_prompt_build', onBeforePromptBuild, { priority: 0 });
}

module.exports = { register };
