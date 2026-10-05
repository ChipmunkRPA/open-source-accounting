import {el} from './ui.js';

export const ANNOTATION_BRAND = 'Ray Sang Annotation';

// Call only around first-party explanation. Never wrap source text or notices.
export function annotationNotice(context = 'Original educational explanation') {
  return el('section', {class:'annotation-notice', 'aria-label':'Original annotation'},
    el('p', {}, el('strong', {}, ANNOTATION_BRAND), ' · '+context),
    el('p', {class:'muted'}, 'Educational draft. The brand does not mean Ray Sang personally wrote or professionally reviewed this text. Existing creator credits, licenses and source notices remain in force.'),
    el('a', {href:'/content-terms.txt'}, 'Content rights and automated-access terms'));
}
