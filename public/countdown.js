/* Shared launch time produces the same playful pre-service countdown on each device. */
window.LaunchCountdown=(()=>{
  const overlay=document.createElement('section');overlay.id='launch-overlay';overlay.hidden=true;overlay.setAttribute('role','status');
  overlay.innerHTML='<div class="launch-card"><div class="launch-pan">🍳</div><div class="eyebrow">THE DINNER BELL IS ABOUT TO RING</div><strong id="launch-number"></strong><h2 id="launch-caption"></h2><p>One crew. One kitchen. Make it delicious.</p></div>';
  document.getElementById('arena').append(overlay);
  let counting=false,lastRound=null,lastBeat=null,callbacks,closing=null;
  function init(options){callbacks=options;}
  function update(s){
    const remaining=s.launch_at-s.wall_now,current=s.started&&!s.finished&&remaining>0;
    if(lastRound!==s.round_id){if(closing)clearTimeout(closing);closing=null;overlay.hidden=true;counting=false;lastBeat=null;lastRound=s.round_id;}
    if(current){
      if(!counting)callbacks.resetInput();counting=true;overlay.hidden=false;overlay.classList.remove('launch-go');
      const beat=Math.ceil(remaining);
      if(beat!==lastBeat){KitchenAudio.countdown(beat);lastBeat=beat;}
      document.getElementById('launch-number').textContent=beat>3?'🥄':beat;
      document.getElementById('launch-caption').textContent=beat>3?'Aprons on!':beat===3?'Knives ready!':beat===2?'Plates up!':'Yes, chef!';
    }else if(counting){
      KitchenAudio.countdown(0);lastBeat=0;
      counting=false;overlay.classList.add('launch-go');document.getElementById('launch-number').textContent='GO!';document.getElementById('launch-caption').textContent='Service is open!';
      closing=setTimeout(()=>{overlay.hidden=true;closing=null;},550);
    }
    if(s.finished)overlay.hidden=true;
  }
  function reset(){counting=false;lastRound=null;lastBeat=null;overlay.hidden=true;if(closing)clearTimeout(closing);closing=null;}
  return {init,update,reset,blocked:()=>counting};
})();
