/**
 * Hermes Memory Loop Hook - Plugin Entry Point
 *
 * This is the OpenClaw plugin entry point.
 * Exports a register(api) function that registers the hooks.
 */

const { register } = require('./handler');
module.exports = { register };
