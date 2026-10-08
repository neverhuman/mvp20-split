/** Compile locally pinned public scientific schemas; never compile schemas in a browser. */
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {standaloneValidators} from './standalone-validators.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),target=resolve(root,'src/page_models/scientific_output');
process.chdir(root);
const schemas={},profiles={};
for(const name of ['hansen-solvency','arrhenius-viscosity']) {
 const raw=await readFile(resolve(target,'schemas',name+'.json')),schema=JSON.parse(raw);
 profiles['materials.'+name+'.output']={sha256:createHash('sha256').update(raw).digest('hex'),schema};
 schemas[name.replaceAll('-','_')]={...schema,$id:'urn:amphora:scientific:'+name};
}
const outputs={'schemas.ts':'// Generated from exact public schema snapshots.\nexport const scientificSchemas = '+JSON.stringify(profiles,null,2)+' as const;\n','validators.ts':await standaloneValidators(schemas,root)};
for(const [name,body] of Object.entries(outputs)) {
 const path=resolve(target,name);
 if(process.argv.includes('--check')) {if(await readFile(path,'utf8')!==body)throw Error('Scientific generated contract is stale: '+name);}
 else await writeFile(path,body);
}
