import { startSpike } from './server.mjs';
const { server, url } = await startSpike();
console.log(`Synthetic interaction prototype: ${url}`);
process.on('SIGINT', () => server.close(() => process.exit(0)));
