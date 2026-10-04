// Read-only inventory: literal internal links must resolve to a real Next route.
import fs from "node:fs";
import path from "node:path";
import ts from "typescript";
const distDir=fs.readFileSync("next.config.ts","utf8").match(/distDir:\s*"([^"]+)"/)?.[1]??".next";
const manifest=JSON.parse(fs.readFileSync(path.join(distDir,"server/app-paths-manifest.json"),"utf8"));
const routes=Object.keys(manifest).filter(p=>p.endsWith("/page")).map(p=>p.slice(0,-5)||"/");
const matches=(href)=>routes.some(r=>new RegExp("^"+r.split("/").map(s=>s.startsWith("[")?"[^/]+":s.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")).join("/")+"$").test(href));
const links=new Set();
function walk(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,entry.name);if(entry.isDirectory())walk(p);else if(/\.tsx?$/.test(p)){const sf=ts.createSourceFile(p,fs.readFileSync(p,"utf8"),ts.ScriptTarget.Latest,true);function visit(n){let value;
if(ts.isJsxAttribute(n)&&n.name.getText(sf)==="href"&&n.initializer&&ts.isStringLiteral(n.initializer))value=n.initializer.text;
if(ts.isPropertyAssignment(n)&&n.name.getText(sf)==="href"&&ts.isStringLiteral(n.initializer))value=n.initializer.text;
if(value?.startsWith("/")&&!value.startsWith("//")){const clean=value.split(/[?#]/)[0];if(!/\.(png|svg|woff2?|ttf)$/.test(clean))links.add(clean);}
ts.forEachChild(n,visit);}visit(sf);}}}
for(const dir of ["app","components","lib"])walk(dir);
const missing=[...links].filter(h=>!matches(h));
console.log(JSON.stringify({routes:routes.sort(),literalInternalLinks:[...links].sort(),missing},null,2));
if(missing.length)process.exitCode=1;
if(process.argv.includes("--http")){
  const prerender=JSON.parse(fs.readFileSync(path.join(distDir,"prerender-manifest.json"),"utf8"));
  const pages=[...new Set([...links,...Object.keys(prerender.routes).filter(r=>!r.startsWith("/_")&&!r.startsWith("/api/")),"/ruta-no-encontrada","/knowledge/no-existe","/sources/no-existe"])];
  const results=[];
  for(const route of pages){const response=await fetch("http://127.0.0.1:3810"+route);results.push({route,status:response.status});await response.text();}
  fs.mkdirSync("qa/recovery",{recursive:true});
  fs.writeFileSync("qa/recovery/route-status.json",JSON.stringify(results,null,2)+"\n");
  console.log(JSON.stringify({protocolChecks:results.length,failures:results.filter(r=>r.status>=500)},null,2));
  if(results.some(r=>r.status>=500))process.exitCode=1;
}
