import {renderDashboard,renderTasks,openTask,taskForm} from './tasks.js';
import {renderRegister,renderSchedules,renderTeam,renderSettings} from './management.js';
import {renderReports,renderAI} from './reports.js';
import {renderManage,renderKnowledge} from './organize.js';
export const state={user:null,users:[],tasks:[],equipment:[],settings:{},catalog:{},page:'dashboard',view:'list',filters:{},connected:false};
export const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const manager=()=>state.user?.role==='manager';
export const userName=id=>state.users.find(u=>u.id===Number(id))?.name||'Unknown';
export const fmt=value=>value?new Intl.DateTimeFormat('en-GB',{dateStyle:'medium',timeStyle:'short',timeZone:state.settings.timezone||'Asia/Colombo'}).format(new Date(value)):'No deadline';
export const dateKey=d=>new Intl.DateTimeFormat('en-CA',{timeZone:state.settings.timezone||'Asia/Colombo',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(d));
export const overdue=t=>!!t.due&&new Date(t.due)<new Date()&&!['Completed','Cancelled'].includes(t.status);
export const badge=x=>`<span class="badge ${['Critical','Overdue'].includes(x)?'red':['High','Waiting','Submitted for Review'].includes(x)?'amber':x==='Completed'?'green':x==='In Progress'?'blue':''}">${esc(x)}</span>`;
export function toast(message){const e=document.querySelector('#toast');e.textContent=message;e.className='show';clearTimeout(window.toastTimer);window.toastTimer=setTimeout(()=>e.className='',7000)}
const pendingRequests=new Map();
export async function api(path,options={}){
 const mutation=options.method&&!['GET','HEAD'].includes(options.method),fingerprint=options.method+path+String(options.body);
 if(mutation&&!pendingRequests.has(fingerprint))pendingRequests.set(fingerprint,crypto.randomUUID());
 const headers={'X-Kelun-Client':'web',...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),...(mutation?{'Idempotency-Key':pendingRequests.get(fingerprint)}:{}),...options.headers};
 const response=await fetch('/api'+path,{...options,headers,credentials:'same-origin'});
 if(response.status<500)pendingRequests.delete(fingerprint);
 if(!response.ok){let body=await response.json().catch(()=>({detail:response.statusText}));const detail=body.detail;throw new Error(typeof detail==='string'?detail:detail?.message||JSON.stringify(detail))}return response.json();
}
export function on(id,event,fn){const el=document.getElementById(id);if(el)el.addEventListener(event,async e=>{if(el.dataset.busy==='true'){e.preventDefault();return}el.dataset.busy='true';const button=el.tagName==='BUTTON'?el:event==='submit'?el.querySelector('button[type=submit],button.primary'):null;if(button)button.disabled=true;try{await fn(e)}catch(err){toast(err.message)}finally{el.dataset.busy='false';if(button)button.disabled=false}})}
export function modal(title,html){const d=document.querySelector('#dialog');d.innerHTML=`<div class="dialog-head"><h2>${esc(title)}</h2><button id="close-dialog" aria-label="Close dialog">✕</button></div><div class="dialog-body">${html}</div>`;if(!d.open)d.showModal();on('close-dialog','click',()=>d.close());return d}
export function closeModal(){document.querySelector('#dialog').close()}
export function formData(form){return Object.fromEntries(new FormData(form))}
export function input(label,name,value='',type='text',required=false){return `<label>${esc(label)}<input name="${esc(name)}" type="${type}" value="${esc(value)}" ${required?'required':''}></label>`}
export function area(label,name,value='',required=false){return `<label>${esc(label)}<textarea name="${name}" ${required?'required':''}>${esc(value)}</textarea></label>`}
export function select(label,name,values,value='',multiple=false){return `<label>${esc(label)}<select name="${name}" ${multiple?'multiple':''}>${values.map(x=>{const v=typeof x==='object'?x.value:x,l=typeof x==='object'?x.label:x;return `<option value="${esc(v)}" ${multiple?(value||[]).map(String).includes(String(v))?'selected':'':String(value)===String(v)?'selected':''}>${esc(l)}</option>`}).join('')}</select></label>`}
export const userOptions=()=>state.users.filter(u=>u.active).map(u=>({value:u.id,label:u.name}));
export function heading(title,subtitle,buttons=''){return `<div class="heading"><div><div class="eyebrow">Kelun Life Sciences · IT Department</div><h1>${esc(title)}</h1><p>${esc(subtitle)}</p></div><div class="actions">${buttons}</div></div>`}
export function empty(message){return `<div class="empty">${esc(message)}</div>`}
let events;
async function authentication(){
 let setup=await api('/setup-status');
 document.querySelector('#app').innerHTML=`<div class="auth"><div class="brand">Kelun <small>IT WORK MANAGER</small></div><h1>${setup.required?'Set up your workspace':'Welcome back'}</h1><p class="muted">${setup.required?'Create Isuru’s manager account. Read the setup key on the server computer.':'Sign in to your department workspace.'}</p><form id="auth-form">${setup.required?input('Server setup key','setup_key','', 'password',true):''}${input('Username','username','isuru','text',true)}${input('Password','password','','password',true)}<p class="legend">${setup.required?'Use a unique password with at least 12 characters.':'Contact your manager if your account is not yet active.'}</p><button class="primary" type="submit">${setup.required?'Create manager account':'Sign in'}</button></form><p class="legend" id="auth-error" role="alert"></p></div>`;
 on('auth-form','submit',async e=>{e.preventDefault();const b=e.target.querySelector('button');b.disabled=true;try{const data=formData(e.target);if(setup.required){await api('/setup',{method:'POST',body:JSON.stringify(data)});toast('Manager account created. Sign in to activate your team.');await authentication()}else{await api('/login',{method:'POST',body:JSON.stringify(data)});await boot()}}catch(err){document.querySelector('#auth-error').textContent=err.message}finally{b.disabled=false}});
}
function shell(){
 const nav=[['dashboard','Overview'],['tasks','Work'],['reports','Reports'],['manage',manager()?'Manage':'More']];
 document.querySelector('#app').innerHTML=`<div class="shell"><aside class="sidebar" id="sidebar"><div class="brand">Kelun <small>IT WORK MANAGER</small></div><button id="sidebar-record" class="sidebar-record">＋ Record work</button><div class="nav-label">Workspace</div>${nav.filter(([id])=>manager()||id!=='reports').map(([id,label])=>`<button data-nav="${id}">${label}</button>`).join('')}<footer>Describe the work.<br>Keep the team informed.</footer></aside><div class="workspace"><header class="topbar"><button id="menu" class="mobile-nav" aria-label="Toggle menu">☰</button><span class="company">Kelun Life Sciences (Pvt) Ltd.</span><span id="connection" class="connection">Connecting…</span><div class="account"><button id="notifications" aria-label="Notifications">Inbox</button><span class="avatar">${esc(state.user.name[0])}</span><span class="name">${esc(state.user.name)}<br><small>${manager()?'Manager':'Team member'}</small></span><button id="logout">Sign out</button></div></header><main class="content" id="content"></main></div></div>`;
 document.querySelectorAll('[data-nav]').forEach(e=>e.addEventListener('click',()=>navigate(e.dataset.nav)));
 on('menu','click',()=>document.querySelector('#sidebar').classList.toggle('open'));
 on('sidebar-record','click',()=>taskForm());
 on('logout','click',async()=>{await api('/logout',{method:'POST'});events?.close();state.user=null;await authentication()});
 on('notifications','click',async()=>{const notices=await api('/notifications');modal('Your inbox',notices.map(n=>`<article class="task-row"><div><p>${esc(n.message)}</p><small>${fmt(n.at)}</small></div>${n.task_id?`<button data-task="${n.task_id}">Open</button>`:''}</article>`).join('')||empty('No notifications yet.'));bindTasks();await api('/notifications/read',{method:'POST'})});
}
export function bindTasks(){document.querySelectorAll('[data-task]').forEach(b=>b.addEventListener('click',()=>openTask(b.dataset.task).catch(e=>toast(e.message))))}
export async function refresh(){state.tasks=await api('/tasks');if(!document.querySelector('#dialog').open&&['dashboard','tasks'].includes(state.page))await render();await inboxCount()}
async function inboxCount(){const n=await api('/notifications');const b=document.querySelector('#notifications');if(b)b.textContent=`Inbox${n.filter(v=>!v.seen).length?' · '+n.filter(v=>!v.seen).length:''}`}
export async function navigate(page){state.page=page;location.hash=page;document.querySelector('#sidebar')?.classList.remove('open');await render()}
async function render(){
 document.querySelectorAll('[data-nav]').forEach(e=>e.classList.toggle('active',e.dataset.nav===state.page));
 const target=document.querySelector('#content');
 try{if(state.page==='dashboard')await renderDashboard(target);else if(state.page==='tasks')renderTasks(target);else if(state.page==='manage')await renderManage(target);else if(state.page==='knowledge')await renderKnowledge(target);else if(state.page.startsWith('register:'))await renderRegister(target,state.page.split(':')[1]);else if(state.page==='schedules')await renderSchedules(target);else if(state.page==='team')await renderTeam(target);else if(state.page==='settings')await renderSettings(target);else if(state.page==='reports')await renderReports(target);else if(state.page==='ai')await renderAI(target);else {state.page='dashboard';await renderDashboard(target)}}catch(e){target.innerHTML=heading('Could not load this view',e.message)+'<button id="retry-page">Try again</button>';on('retry-page','click',render)}
}
async function boot(){
 try{state.user=await api('/me')}catch{await authentication();return}
 [state.users,state.settings,state.catalog,state.tasks,state.equipment]=await Promise.all(['/users','/settings','/catalog','/tasks','/registers/equipment'].map(p=>api(p)));shell();
 const hash=location.hash.slice(1);state.page=hash.startsWith('task/')?'tasks':hash||'dashboard';await render();if(hash.startsWith('task/'))await openTask(hash.slice(5));
 events?.close();events=new EventSource('/api/events');
 events.addEventListener('change',()=>{connection(true);refresh().catch(()=>connection(false))});events.onopen=()=>connection(true);events.onerror=()=>connection(false);
 await inboxCount();
}
function connection(ok){state.connected=ok;const e=document.querySelector('#connection');if(e){e.textContent=ok?'● Live connection':'● Offline · reconnecting';e.className='connection'+(ok?'':' offline')}}
window.addEventListener('online',()=>refresh().catch(()=>{}));
document.querySelector('#dialog').addEventListener('close',()=>{if(state.user)refresh().catch(e=>toast(e.message))});
window.addEventListener('hashchange',()=>{const h=location.hash.slice(1);if(h.startsWith('task/'))openTask(h.slice(5)).catch(e=>toast(e.message));else if(h&&h!==state.page)navigate(h).catch(e=>toast(e.message))});
boot().catch(e=>{document.querySelector('#app').innerHTML=`<main class="auth"><h1>Server unavailable</h1><p>${esc(e.message)}</p><p>Start the local server, then reload this page.</p></main>`});
