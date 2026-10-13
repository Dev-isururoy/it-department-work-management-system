const fs=require('node:fs');
for(const file of fs.readdirSync('web').filter(f=>f.endsWith('.js'))){
 const source=fs.readFileSync('web/'+file,'utf8').replace(/^import .*?;$/gm,'').replace(/^export /gm,'');
 new Function(source);
 console.log('Parsed',file);
}
