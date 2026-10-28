const $ = id => document.getElementById(id);
let session = null;
let state, busy = false, joining = false, leaving = false, keys = new Set(), touch = [0, 0];
async function post(path, data) {
  const response = await fetch('/api/'+path, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) {const error=Error(result.error);error.status=response.status;throw error;}
  return result;
}
function error(e) { $('error').textContent = e.message; if(session) KitchenUX.showError(e.message); else $('lobby-error').textContent=e.message; }
async function enter(mode) {
  if(joining || mode!=='demo'&&!$('join').reportValidity()) return;
  joining=true; $('lobby-error').textContent='';
  KitchenAudio.unlock().catch(error);
  KitchenLobby.pending(true);
  try {
    activate(await post(mode,mode==='demo'?{}:KitchenLobby.payload()));
  } catch(e) { error(e); }
  finally {joining=false;KitchenLobby.pending(false);}
}
function showGame() { $('error').textContent=''; $('lobby').hidden = true; $('game').hidden = false; $('room').textContent = session.room; window.scrollTo(0,0); $('canvas').focus({preventScroll:true}); }
function activate(next){session={room:next.room,token:next.token};state=null;resetInput();KitchenUX.reset();GameDialogs.reset();RoundEffects.reset();LaunchCountdown.reset();RejoinFlow.remember(session);history.replaceState(null,'','/?room='+encodeURIComponent(session.room));showGame();}
async function resume(record){KitchenAudio.unlock().catch(error);activate(await post('rejoin',{room:record.room,token:record.token}));}
function resetInput() {keys.clear(); touch=[0,0]; KitchenRenderer.setMovement(0,0);}
function movementInput() {
  return {
    dx:touch[0]+Number(keys.has('d')||keys.has('arrowright'))-Number(keys.has('a')||keys.has('arrowleft')),
    dy:touch[1]+Number(keys.has('s')||keys.has('arrowdown'))-Number(keys.has('w')||keys.has('arrowup'))
  };
}
function updateMovementPreview(){const {dx,dy}=movementInput();KitchenRenderer.setMovement(dx,dy);}
function home({forget=true}={}) {const departing=session;session=null;state=null;if(forget){RejoinFlow.forget(departing);history.replaceState(null,'','/');}else RejoinFlow.idle();resetInput();KitchenRenderer.clearAim();KitchenUX.reset();GameDialogs.reset();KitchenAudio.reset();KitchenLobby.reset();RoundEffects.reset();LaunchCountdown.reset();$('lobby').hidden=false;$('game').hidden=true;window.scrollTo(0,0);}
async function leave() {
  leaving=true;
  try {
    await post('leave',session);
    if(document.fullscreenElement) await document.exitFullscreen();
    home();
  } finally {leaving=false;}
}
async function act(action, extra={}) {
  if (!session||RejoinFlow.blocked()) return false;
  if(['move','interact','throw','discard'].includes(action)&&(RoundEffects.blocked()||LaunchCountdown.blocked()))return false;
  if(action==='throw')extra={...KitchenRenderer.aimVector(),...extra};
  try { await post('action', {...session, action, ...extra}); if(action !== 'move') { $('error').textContent=''; if(!GameDialogs.blocked()) $('canvas').focus({preventScroll:true}); } return true; }
  catch(e) { error(e); if(!GameDialogs.blocked()) $('canvas').focus({preventScroll:true}); return false; }
}
$('start').onclick = () => act('start');
GameDialogs.init({act,leave,resetInput,isInGame:()=>!!session});
KitchenUX.init({act,leave:GameDialogs.requestExit,onError:error});
KitchenLobby.init({enter});
RoundEffects.init({act,resetInput,leave:GameDialogs.requestExit});
LaunchCountdown.init({resetInput});
RejoinFlow.init({resume,home,resetInput,getSession:()=>session,onError:error});
$('invite').onclick = async () => { try { await navigator.clipboard.writeText(location.origin+'/?room='+session.room); $('invite').textContent='Copied!'; } catch(e) { error(e); } };
document.querySelectorAll('[data-action]').forEach(b => b.onclick = () => act(b.dataset.action));
document.querySelectorAll('[data-move]').forEach(b => {
  b.onpointerdown = e => { e.preventDefault(); b.setPointerCapture(e.pointerId); touch=b.dataset.move.split(',').map(Number); updateMovementPreview(); };
  b.onpointerup = b.onpointercancel = () => {touch=[0,0];updateMovementPreview();};
});
window.addEventListener('keydown',e => {
  if(!session || GameDialogs.blocked() || /INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;
  const key=e.key.toLowerCase();
  if((key==='p'||key==='escape')&&!e.repeat){e.preventDefault();RoundEffects.toggle();return;}
  if(key==='f'&&e.shiftKey&&!e.repeat){e.preventDefault();$('window-fullscreen').click();return;}
  if(state?.paused||RoundEffects.blocked()||LaunchCountdown.blocked()||RejoinFlow.blocked())return;
  if(['arrowup','arrowdown','arrowleft','arrowright',' '].includes(key)) e.preventDefault();
  keys.add(key);
  updateMovementPreview();
  if(['w','a','s','d','arrowup','arrowdown','arrowleft','arrowright'].includes(key))KitchenRenderer.clearAim();
  if(!e.repeat && {e:1,f:1,x:1}[key]) act({e:'interact',f:'throw',x:'discard'}[key]);
});
window.addEventListener('keyup',e => {keys.delete(e.key.toLowerCase());updateMovementPreview();});
window.addEventListener('blur',() => {keys.clear();touch=[0,0];updateMovementPreview();});
async function pollState() {
  if(!session || busy || leaving || RejoinFlow.blocked()) return;
  busy=true;
  try {
    const current=session;
    let response,data;
    try{response=await fetch('/api/state?'+new URLSearchParams(current));data=await response.json();}
    catch(networkError){if(current===session&&!leaving)RejoinFlow.failed(networkError);return;}
    if(current!==session || leaving) return;
    if(!response.ok) {if(response.status===410){home();error(Error(data.error));}else{home({forget:false});RejoinFlow.expired(data.error);}return;}
    RejoinFlow.good();state=data; render();
  } catch(e) {error(e);} finally {busy=false;}
}
setInterval(pollState,100);
document.addEventListener('visibilitychange',()=>{
  if(document.visibilityState==='visible')pollState();
});
let moving=false;
setInterval(async () => {
  if(document.visibilityState!=='visible' || moving || !session || state?.paused || GameDialogs.blocked() || RoundEffects.blocked() || LaunchCountdown.blocked() || RejoinFlow.blocked()) return;
  const {dx,dy}=movementInput();
  KitchenRenderer.setMovement(dx,dy);
  if(dx||dy) {moving=true;await act('move',{dx,dy});moving=false;}
},50);
function render() {
  const s=state, remaining=Math.max(0,Math.ceil(s.end-s.now));
  $('score').textContent=s.score; $('target').textContent=s.target || '—';
  $('timer').textContent=s.started ? Math.floor(remaining/60)+':'+String(remaining%60).padStart(2,'0') : '2:30';
  $('start').disabled=s.started&&remaining>0 || s.host!==s.you;
  $('start').hidden=s.host!==s.you||s.started&&!s.finished;
  $('start').textContent=s.started&&remaining===0?'Play again':'Start service';
  const me=s.players[s.you],near=s.stations.reduce((a,b)=>Math.hypot(a.x-me.x,a.y-me.y)<=Math.hypot(b.x-me.x,b.y-me.y)?a:b);
  const floor=s.floor.some(item=>Math.hypot(item.x-me.x,item.y-me.y)<.85)&&me.held===null;
  const held=me.held===null?'hands empty':Array.isArray(me.held)?'plate: '+(me.held.join(' + ')||'empty'):me.held;
  const closeToStation=Math.hypot(near.x-me.x,near.y-me.y)<1.55;
  $('announcement').hidden=!s.started||s.finished||s.paused||s.wall_now<s.launch_at||!(floor||closeToStation||me.held!==null||me.task||me.stunned_until>s.now);
  $('announcement').textContent=(floor?'Fallen ingredient':closeToStation?near.name:'Carrying')+' · '+held+(me.stunned_until>s.now?' · STUNNED':'');
  $('tickets').replaceChildren();
  for(const [i,o] of s.orders.filter(order=>order.expires>s.now).entries()) {
    const card=document.createElement('div');card.className='ticket'+(o.guest?' special '+(o.guest==='Critic'?'critic':''):'');
    const title=document.createElement('b');title.textContent=(i===0?'★ ':'')+(o.guest?o.guest+' · ':'')+o.recipe;
    const sub=document.createElement('small');sub.textContent=Math.max(0,Math.ceil(o.expires-s.now))+'s left · '+(i===0?'×'+s.combo+' next':'100 base');
    const meter=document.createElement('div');meter.className='meter';const fill=document.createElement('i');
    const percent=Math.max(0,(o.expires-s.now)/o.patience*100);fill.style.width=percent+'%';fill.style.background=percent<25?'#ce6046':percent<55?'#d4aa46':'#65985f';
    meter.append(fill);card.append(title,sub,meter);$('tickets').append(card);
    if(o.guest){const stakes=document.createElement('small');stakes.className='guest-stakes';stakes.textContent='Bonus +'+o.bonus+' · Miss / wrong −'+o.penalty;card.append(stakes);}
  }
  $('crew').replaceChildren();
  Object.entries(s.players).forEach(([id,p],i) => {const row=document.createElement('div');row.style.color=KitchenArt.colors[i%8];row.textContent='● '+p.name+(p.bot?' · BOT':id===s.you?' (you)':'');if(p.bot){const status=document.createElement('small');status.textContent=p.bot_status;row.append(document.createElement('br'),status);}$('crew').append(row);});
  $('supply').textContent='Plates: '+s.plates+' clean · '+s.dirty+' dirty';
  const publicSession={room:session.room,token:s.you};
  KitchenUX.update(s,publicSession);
  GameDialogs.update(s,publicSession);
  RoundEffects.update(s,publicSession);
  LaunchCountdown.update(s);
  RejoinFlow.metadata(s,session);
  document.querySelectorAll('.controls [data-action],#touch button').forEach(button=>button.disabled=s.paused||LaunchCountdown.blocked()||RoundEffects.blocked());
  KitchenRenderer.update(s,publicSession);
  KitchenAudio.update(s,session);
}
