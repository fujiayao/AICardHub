import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import vm from 'node:vm';
import ts from 'typescript';
const BS=String.fromCharCode(92);
const nodeRequire=createRequire(import.meta.url);
const VueRouter=nodeRequire('vue-router');
const Vue=nodeRequire('vue');
const {parse,compileScript}=nodeRequire('vue/compiler-sfc');
const transpile=src=>ts.transpileModule(src,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
function run(code,file,require,extra={}){const module={exports:{}};vm.runInNewContext(code,{module,exports:module.exports,require,URL,decodeURIComponent,console,...extra},{filename:file});return module.exports;}
const loadTs=(file,require)=>run(transpile(readFileSync(new URL('../src/'+file,import.meta.url),'utf8')),file,require);
// Real SFC <script setup> compiled non-inline so setup() returns the actual handlers (submit/save).
function loadSfc(file,require){const filename=new URL('../src/'+file,import.meta.url).pathname;const {descriptor}=parse(readFileSync(new URL('../src/'+file,import.meta.url),'utf8'),{filename});const out=compileScript(descriptor,{id:'t',inlineTemplate:false});return run(transpile(out.content),file,require).default;}
const redirect=loadTs('router/redirect.ts',()=>({}));
const guard=loadTs('router/guard.ts',n=>n==='./redirect'?redirect:VueRouter);

// Real vue-router (memory history) + real guard + real LoginForm/ChangePassword handlers.
// Stubbed: auth store, api, element-plus, form validation, window events (EventTarget).
async function harness(){
  const auth={signedIn:false,mustChangePassword:false};const events=new EventTarget();const c={template:'<div/>'};
  const router=VueRouter.createRouter({history:VueRouter.createMemoryHistory(),routes:[{path:'/login',component:c},{path:'/change-password',component:c},{path:'/activity',redirect:to=>({path:'/activities',query:to.query,hash:to.hash})},{path:'/dashboard',component:c},{path:'/activities',component:c},{path:'/reports',component:c},{path:'/:p(.*)*',redirect:'/dashboard'}]});
  guard.installAuthNavigation(router,{auth:()=>auth,requirePassword:()=>{auth.mustChangePassword=true;},events});
  const errors=[];
  // Mirrors src/api/session.ts: clearing the session dispatches admin-session-ended.
  const store={get session(){return auth.signedIn?{must_change_pwd:auth.mustChangePassword}:null;},async login(){auth.signedIn=true;},logout(){auth.signedIn=false;auth.mustChangePassword=false;events.dispatchEvent(new Event('admin-session-ended'));}};
  const sfcRequire=n=>{switch(n){
    case 'vue':return {...Vue,useTemplateRef:()=>({value:{validate:async()=>true}})};
    case 'vue-router':return {useRouter:()=>router,useRoute:()=>router.currentRoute.value};
    case 'element-plus':return {ElMessage:{success(){},warning(){}}};
    case '@/store/modules/auth':return {useAuthStore:()=>store};
    case '@/api/adapters':return {api:{async changePassword(){}}};
    case '@/composables/useTask':return {useTask:()=>({busy:{value:false},error:{value:''},run:async t=>{try{return await t();}catch(e){errors.push(e);}}})};
    case '@/router/redirect':return redirect;
    default:throw new Error('unexpected import '+n);}};
  const LoginForm=loadSfc('components/auth/LoginForm.vue',sfcRequire);
  const ChangePassword=loadSfc('views/ChangePassword.vue',sfcRequire);
  // setup() is called directly (no DOM mount); useRoute() snapshot is taken at that moment, like a freshly mounted view.
  const setup=C=>C.setup({}, {expose(){},emit(){},attrs:{},slots:{}});
  const settle=()=>new Promise(r=>setTimeout(r,0));
  const login=async(mustChange=false)=>{const s=setup(LoginForm);s.model.phone='13800000000';s.model.password='pw';const orig=store.login;store.login=async()=>{auth.signedIn=true;auth.mustChangePassword=mustChange;};await s.submit();store.login=orig;await settle();assert.deepEqual(errors,[]);};
  const passwordChanged=async()=>{const s=setup(ChangePassword);Object.assign(s.model,{old_password:'a',new_password:'b',confirm:'b'});await s.save();await settle();assert.deepEqual(errors,[]);};
  const logout=async()=>{store.logout();await settle();};
  return {auth,events,router,login,logout,passwordChanged,settle,cur:()=>router.currentRoute.value.fullPath};}

test('unauthenticated deep link keeps query+hash through login (and /activity alias)',async()=>{const h=await harness();await h.router.push('/reports?campaign=7&tab=a%20b#leads');assert.equal(h.router.currentRoute.value.path,'/login');assert.equal(h.router.currentRoute.value.query.redirect,'/reports?campaign=7&tab=a%20b#leads');await h.login();{const r=h.router.currentRoute.value;assert.equal(r.path,'/reports');assert.deepEqual({...r.query},{campaign:'7',tab:'a b'});assert.equal(r.hash,'#leads');}await h.logout();await h.router.push('/activity?id=3#x');assert.equal(h.router.currentRoute.value.query.redirect,'/activities?id=3#x');await h.login();assert.equal(h.cur(),'/activities?id=3#x');});

test('forced password change re-authenticates and still lands on original target',async()=>{const h=await harness();await h.router.push('/activities?status=live#top');await h.login(true);assert.equal(h.router.currentRoute.value.path,'/change-password');assert.equal(h.router.currentRoute.value.query.redirect,'/activities?status=live#top');await h.passwordChanged();assert.equal(h.auth.signedIn,false,'invalidated session must not be reused');assert.equal(h.router.currentRoute.value.path,'/login');assert.equal(h.router.currentRoute.value.query.redirect,'/activities?status=live#top');await h.login();assert.equal(h.cur(),'/activities?status=live#top');
  // server-side PASSWORD_CHANGE_REQUIRED mid-session also preserves the current page
  h.events.dispatchEvent(new Event('admin-password-required'));await h.settle();assert.equal(h.router.currentRoute.value.path,'/change-password');assert.equal(h.router.currentRoute.value.query.redirect,'/activities?status=live#top');});

test('explicit logout and expiry go to bare /login without a stale target',async()=>{const h=await harness();await h.router.push('/reports?x=1');await h.login();assert.equal(h.cur(),'/reports?x=1');await h.logout();assert.equal(h.cur(),'/login');await h.login();assert.equal(h.cur(),'/dashboard');});

test('unsafe redirect values fall back to /dashboard; valid encoded targets are kept',async()=>{const bad=['https://evil.test','//evil.test','/'+BS+'evil.test',BS+BS+'evil.test','/%5Cevil.test','/%5cevil.test','/reports?q=%5C','/%2F%2Fevil.test','/%2fevil.test','%2F%2Fevil.test','/%252F%252Fevil.test','/x/..//evil.test','/.//evil.test','/%2e%2e//evil.test','/a/%2E%2E/%2E%2E//evil.test','javascript:alert(1)','/javascript:alert(1)','JaVaScRiPt%3Aalert(1)','/%6Aavascript:alert(1)','/%00x','/a%0Ab','/a'+String.fromCharCode(10)+'b','/%E0%A4%A','/reports?q=%E0%A4%A','/100%','/login','/LOGIN/','/%6Cogin','/%6cOGIN/','/reports/../login','/change-password?redirect=/x','/change%2Dpassword','reports',['/reports','/x'],'',undefined];for(const v of bad)assert.equal(redirect.resolveTarget(v),'/dashboard',JSON.stringify(v));
  const good={'/reports?a=1&b=2#h':'/reports?a=1&b=2#h','/reports?q=100%25':'/reports?q=100%25','/reports?next=https://evil.test#//x':'/reports?next=https://evil.test#//x','/reports?next=%2F%2Fevil.test':'/reports?next=%2F%2Fevil.test','/activities?name=%E6%B4%BB%E5%8A%A8':'/activities?name=%E6%B4%BB%E5%8A%A8'};for(const [v,want] of Object.entries(good))assert.equal(redirect.resolveTarget(v),want,JSON.stringify(v));
  const h=await harness();h.auth.signedIn=true;await h.router.push('/login?redirect='+encodeURIComponent('//evil.test'));assert.equal(h.cur(),'/dashboard');await h.router.push('/login?redirect='+encodeURIComponent('/x/..//evil.test'));assert.equal(h.cur(),'/dashboard');await h.router.push({path:'/login',query:{redirect:['/reports','/activities']}});assert.equal(h.cur(),'/dashboard');
  // literal percent in a query survives the full unauthenticated → login round trip
  h.auth.signedIn=false;await h.router.push('/reports?q=100%25');await h.login();assert.equal(h.router.currentRoute.value.path,'/reports');assert.equal(h.router.currentRoute.value.query.q,'100%');});
