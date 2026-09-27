import {copyFile, mkdir} from 'node:fs/promises';
await mkdir('dist', {recursive:true});
for (const name of ['index.html','styles.css']) await copyFile(`public/${name}`,`dist/${name}`);
console.log('Built frontend/dist. Start the API to serve the working UI.');
