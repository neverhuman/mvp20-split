/** Module-owned verification; E2E remains a separate acceptance tier. */
import {spawnSync} from 'node:child_process';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
for(const args of [['scripts/generate-contracts.mjs','--check'],['node_modules/typescript/bin/tsc','-p','tsconfig.json'],['--test','dist/tests/page_models/generation_comparison/checkpoint.test.js','dist/tests/page_models/generation_comparison/model.test.js']]){
 const result=spawnSync(process.execPath,args,{cwd:root,stdio:'inherit',windowsHide:true});if(result.status!==0)process.exit(result.status??1);
}
