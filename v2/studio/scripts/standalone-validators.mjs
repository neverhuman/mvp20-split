/** Compile reviewed schemas before deployment; emitted browser code never invokes Ajv's compiler. */
import { Ajv2020 } from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import standaloneCode from 'ajv/dist/standalone/index.js';
import { build } from 'esbuild';

const references = {
  SourceRevisionRef:'source', MaterialStateRevisionRef:'material', ExperimentRevisionRef:'experiment',
  ObservationRevisionRef:'observation', ResearchQuestionRef:'question', EvidenceNeedRef:'need',
  AcceptedChangeRef:'change', DomainGraphRef:'proposal',
};
export async function standaloneValidators(schemas, root) {
  const ajv = new Ajv2020({ strict:true, allErrors:false, coerceTypes:false, useDefaults:false,
    removeAdditional:false, code:{source:true} });
  ajv.addKeyword({keyword:'discriminator',schemaType:'object',valid:true});
  addFormats(ajv);
  const names = {};
  for (const [key,schema] of Object.entries(schemas)) {
    ajv.addSchema(schema);names[key]=schema.$id;
  }
  for (const [definition,key] of Object.entries(references)) {
    if (!schemas[key]?.$defs?.[definition]) continue;
    const name=key+'__'+definition, id='urn:amphora:studio-reference:'+name;
    ajv.addSchema({$id:id,$ref:schemas[key].$id+'#/$defs/'+definition});names[name]=id;
  }
  const source=standaloneCode(ajv,names);
  const result=await build({stdin:{contents:source,resolveDir:root,sourcefile:'reviewed-validators.cjs'},
    bundle:true,platform:'browser',format:'esm',write:false,minify:false,legalComments:'none'});
  return '// @ts-nocheck\n// Generated standalone validators; change published schemas or the generator, never this file.\n'+result.outputFiles[0].text;
}
