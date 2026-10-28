/* Exercise real timer rendering at server-time boundaries, without a browser clock. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function element(){
  const classes=new Set();
  return {hidden:false,textContent:'',innerHTML:'',attributes:{},append(){},
    setAttribute(key,value){this.attributes[key]=value;},
    classList:{toggle(key,on){if(on)classes.add(key);else classes.delete(key);},remove(...keys){for(const key of keys)classes.delete(key);},contains(key){return classes.has(key);}}};
}
const ids=new Map(['arena','timer','last-call-time'].map(id=>[id,element()]));
const overlay=element();
const context={window:{},document:{getElementById:id=>ids.get(id),createElement:()=>overlay}};
vm.runInNewContext(fs.readFileSync('public/game-timer.js','utf8'),context);
const timer=context.window.KitchenTimer,clock=ids.get('timer');
const state={started:true,finished:false,paused:false,end:1240,now:1209,wall_now:1209,launch_at:1000};
timer.update(state);
assert.equal(clock.textContent,'0:31');assert.equal(clock.classList.contains('clock-urgent'),false);assert.equal(overlay.hidden,true);
timer.update({...state,now:1210});
assert.equal(clock.textContent,'0:30');assert.equal(clock.classList.contains('clock-urgent'),true);assert.equal(overlay.hidden,true);
timer.update({...state,now:1229});assert.equal(overlay.hidden,true);
timer.update({...state,now:1230});
assert.equal(overlay.hidden,false);assert.equal(clock.classList.contains('clock-in-center'),true);assert.equal(ids.get('last-call-time').textContent,'0:10');
timer.update({...state,now:1235,paused:true});
assert.equal(overlay.hidden,true);assert.equal(ids.get('arena').classList.contains('clock-paused'),true);assert.equal(clock.textContent,'0:05');
timer.update({...state,now:1239});assert.equal(overlay.hidden,false);assert.equal(ids.get('last-call-time').textContent,'0:01');
for(const snapshot of [{...state,now:1240},{...state,now:1235,finished:true},{...state,started:false},{...state,now:1235,launch_at:1300}]){
  timer.update(snapshot);assert.equal(overlay.hidden,true);assert.equal(clock.classList.contains('clock-urgent'),false);
}
timer.reset();assert.equal(overlay.hidden,true);assert.equal(clock.classList.contains('clock-in-center'),false);
console.log('PASS: 31/30/11/10/1/0-second timer rendering, pause, finish, launch and reset.');
