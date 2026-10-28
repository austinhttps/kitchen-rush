/* Numeric HUD clock and the final ten-second, pointer-free last-call overlay. */
window.KitchenTimer=(()=>{
  const arena=document.getElementById('arena'),clock=document.getElementById('timer');
  const overlay=document.createElement('div');overlay.id='last-call';overlay.hidden=true;
  overlay.innerHTML='<div class="last-call-label">LAST CALL</div><strong id="last-call-time" role="timer" aria-label="Time remaining"></strong>';
  arena.append(overlay);
  function phase(state){
    const remaining=state.started?Math.max(0,Math.ceil(state.end-state.now)):150;
    const active=state.started&&!state.finished&&state.wall_now>=state.launch_at&&remaining>0;
    return {remaining,urgent:active&&remaining<=30,final:active&&!state.paused&&remaining<=10};
  }
  function update(state){
    const {remaining,urgent,final}=phase(state);
    const text=Math.floor(remaining/60)+':'+String(remaining%60).padStart(2,'0');
    clock.textContent=text;clock.setAttribute('aria-label',remaining+' seconds remaining');
    clock.classList.toggle('clock-urgent',urgent);clock.classList.toggle('clock-in-center',final);
    arena.classList.toggle('clock-paused',state.paused);
    overlay.hidden=!final;document.getElementById('last-call-time').textContent=text;
  }
  function reset(){clock.classList.remove('clock-urgent','clock-in-center');overlay.hidden=true;arena.classList.remove('clock-paused');}
  return {phase,update,reset};
})();
