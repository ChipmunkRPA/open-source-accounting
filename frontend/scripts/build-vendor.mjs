import {build} from 'esbuild';
await build({entryPoints:['vendor/identity.mjs'],outfile:'dist/vendor/identity.js',bundle:true,
  format:'esm',platform:'browser',target:'es2022',minify:true,sourcemap:false,legalComments:'external'});
console.log('Built local Identity Platform MFA bundle; no remote QR or analytics services.');
