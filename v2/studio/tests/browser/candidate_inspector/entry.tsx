import {createRoot} from 'react-dom/client';
import {CandidateResults} from '../../../src/presentation/candidate_inspector/results.js';
import '../../../src/presentation/style.css';
const context=await fetch('/probe-context').then(response=>response.json());
createRoot(document.getElementById('root')!).render(<main><h1>Campaign results</h1><CandidateResults context={context}/></main>);
