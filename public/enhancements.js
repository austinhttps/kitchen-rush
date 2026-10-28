/* Lobby handbook, practice lessons, notifications, and fullscreen controls. */
window.KitchenUX = (() => {
  const el = id => document.getElementById(id);
  let lastEvent = 0, lastRoom = null, lastError = '', errorAt = 0;
  for (const id of ['homepage-guide', 'modal-guide']) {
    el(id).append(el('guide-template').content.cloneNode(true));
  }
  const lobbyError = document.createElement('p');
  lobbyError.id = 'lobby-error'; lobbyError.className = 'dialog-error'; lobbyError.setAttribute('role','alert');
  el('lobby-feedback').append(lobbyError);
  const botsLabel=document.createElement('label');botsLabel.textContent='Bot teammates';
  const botsSelect=document.createElement('select');botsSelect.id='bots';
  for(let i=0;i<=3;i++){const option=document.createElement('option');option.value=i;option.textContent=i===0?'No bots — humans only':i+' bot teammate'+(i===1?'':'s');botsSelect.append(option);}
  botsLabel.append(botsSelect);el('difficulty-hint').before(botsLabel);
  const toolbar = document.createElement('div');
  toolbar.id='game-toolbar';toolbar.className = 'game-toolbar';
  toolbar.innerHTML = '<label>Level difficulty<select id="room-difficulty"></select></label><label>Bots<select id="room-bots"></select></label><span id="level-summary"></span><button id="view-results" hidden>View results</button><button id="sound" aria-pressed="true">♫ Sound on</button><button id="fullscreen">⛶ Fullscreen</button><button id="leave">Back to homepage</button>';
  el('game').prepend(toolbar);
  el('room-difficulty').append(...Array.from(el('difficulty').options, option => option.cloneNode(true)));
  el('room-bots').append(...Array.from(botsSelect.options,option=>option.cloneNode(true)));
  const board=el('canvas').parentElement;board.id='board';
  const arena=document.createElement('div');arena.id='arena';
  for(const child of [...el('game').children])arena.append(child);
  el('game').append(arena);
  const hud=document.createElement('div');hud.className='arena-hud';
  hud.innerHTML='<div class="hud-brand">🍳 <strong>The Little Bistro</strong></div><div class="hud-cell hud-room"><small>ROOM</small></div><div class="hud-cell hud-clock"><small>TIME</small></div><div id="arena-score"><span class="hud-score-item">Score </span><span class="hud-target-item">Target </span></div><span id="hud-combo" title="Serve the oldest ticket to build the score multiplier">✨ Combo ×1</span><div id="hud-difficulty-readout" class="hud-cell"><small>LEVEL</small><strong id="hud-difficulty-value"></strong></div><div id="hud-bots-readout" class="hud-cell"><small>BOTS</small><strong id="hud-bots-value"></strong></div><div id="hud-host-controls"></div><div id="arena-players" aria-label="Active players"></div><div class="arena-tools"><button id="window-fullscreen">⛶ Fullscreen</button><button id="arena-menu">☰ Menu</button></div>';
  const status=el('room').closest('.status');
  hud.querySelector('.hud-room').append(el('room'));
  hud.querySelector('.hud-clock').append(el('timer'));
  hud.querySelector('.hud-score-item').append(el('score'));
  hud.querySelector('.hud-target-item').append(el('target'));
  hud.querySelector('#hud-host-controls').append(el('room-difficulty').closest('label'),el('room-bots').closest('label'));
  hud.querySelector('.arena-tools').prepend(el('start'),el('invite'));
  status.hidden=true;
  el('level-summary').hidden=true;
  el('game-toolbar').hidden=true;
  arena.append(hud);
  const supply=document.createElement('div');supply.id='supply';supply.className='sr-only';supply.setAttribute('aria-label','Plate supply');arena.append(supply);
  function placeOverlays(){
    const canvas=el('canvas'),r=canvas.getBoundingClientRect(),a=arena.getBoundingClientRect();
    const scale=Math.min(r.width/canvas.width,r.height/canvas.height);
    arena.style.setProperty('--map-content-top',(r.top-a.top+(r.height-canvas.height*scale)/2+156*scale)+'px');
    arena.style.setProperty('--map-content-left',(r.left-a.left+(r.width-canvas.width*scale)/2)+'px');
  }
  const layoutObserver=new ResizeObserver(placeOverlays);
  for(const target of [hud,arena,el('canvas')])layoutObserver.observe(target);
  const practice = document.createElement('section');
  practice.id = 'practice'; practice.hidden = true;
  practice.innerHTML = '<div><div class="eyebrow" id="lesson-number"></div><h2 id="lesson-title"></h2><ol id="lesson-steps"></ol></div><div class="practice-actions"><p id="lesson-result" role="status"></p><button id="next-demo" class="primary" hidden>Next sample round →</button></div>';
  toolbar.after(practice);
  const alerts = document.createElement('div');
  alerts.id = 'game-alerts'; alerts.setAttribute('role', 'status'); alerts.setAttribute('aria-live', 'polite');
  el('tickets').after(alerts);
  function toast(message, tone='info') {
    const card = document.createElement('div'); card.className = 'game-alert '+tone;
    const text = document.createElement('span'); text.textContent = message;
    const close = document.createElement('button'); close.textContent = '×'; close.setAttribute('aria-label', 'Dismiss alert');
    close.onclick = () => card.remove(); card.append(text, close); alerts.append(card);
    while (alerts.children.length > 4) alerts.firstElementChild.remove();
    setTimeout(() => card.remove(), 6500);
  }
  function showError(message) {
    if (message !== lastError || Date.now()-errorAt > 3000) {
      toast(message, 'danger'); lastError=message; errorAt=Date.now();
    }
  }
  let currentState=null;
  function init({act, leave, onError}) {
    el('leave').onclick = leave;
    el('arena-home').onclick=leave;
    for(const id of ['sound','arena-sound'])el(id).onclick=()=>KitchenAudio.toggle().then(()=>el('canvas').focus({preventScroll:true})).catch(onError);
    KitchenAudio.buttons();
    el('room-bots').onchange=async()=>{
      const select=el('room-bots');select.dataset.pending='true';
      await act('bots',{count:Number(select.value)});delete select.dataset.pending;
    };
    el('room-difficulty').onchange = async () => {
      const select = el('room-difficulty'); select.dataset.pending = 'true';
      await act('difficulty', {difficulty: select.value}); delete select.dataset.pending;
    };
    el('difficulty').onchange = () => {
      const descriptions = {easy:'100s patience · 15s burn · 3 active customers · 600 base target', medium:'60s patience · 10s burn · 4 active customers · 1,200 base target',hard:'50s patience · 8s burn · 5 active customers · 1,600 base target',expert:'45s patience · 6s burn · 6 active customers · 2,000 base target',chef:'40s patience · 5s burn · 7 active customers · 2,400 base target','chef-de-cuisine':'35s patience · 4s burn · 8 active customers · 2,800 base target'};
      el('difficulty-hint').textContent=descriptions[el('difficulty').value]+'. The host chooses the room difficulty.';
    };
  const fullscreen = async () => {
      try {
        if (document.fullscreenElement) await document.exitFullscreen();
        else if (arena.requestFullscreen) await arena.requestFullscreen();
        else throw Error('Fullscreen is unavailable in this browser. Open the game in a browser that supports fullscreen.');
      } catch (e) { onError(e); }
    };
  el('fullscreen').onclick=el('window-fullscreen').onclick=fullscreen;
    document.addEventListener('fullscreenchange', () => {
      const label=document.fullscreenElement?'⛶ Exit fullscreen':'⛶ Fullscreen';
      for(const id of ['fullscreen','window-fullscreen','menu-fullscreen'])el(id).textContent=label;
      el('canvas').focus({preventScroll:true});
    });
    el('next-demo').onclick = () => {
      if(el('next-demo').dataset.finish==='true') leave(); else act('next_demo');
    };
  }
  function update(s, session) {
    currentState=s;
    if(lastRoom !== session.room) {lastRoom=session.room;lastEvent=0;alerts.replaceChildren();}
    if(s.paused){alerts.replaceChildren();lastEvent=Math.max(lastEvent,...s.events.map(event=>event.id));}
    else for (const event of s.events) if(event.id>lastEvent) {toast(event.message,event.tone);lastEvent=event.id;}
    const active=s.started && s.end>s.now, config=s.difficulties[s.demo?'easy':s.difficulty];
    const selector=el('room-difficulty');
    if(!selector.dataset.pending) selector.value=s.demo?'easy':s.difficulty;
    selector.disabled=s.demo || active || s.host!==session.token;
    const botSelector=el('room-bots');
    if(!botSelector.dataset.pending)botSelector.value=s.bot_count;
    botSelector.disabled=s.demo||active||s.host!==session.token;
    el('hud-combo').textContent='✨ Combo ×'+s.combo;
    el('hud-difficulty-value').textContent=config.label;
    el('hud-bots-value').textContent=s.bot_count;
    el('arena-players').replaceChildren(...Object.entries(s.players).map(([id,p],index)=>{const avatar=document.createElement('span');avatar.className='player-avatar'+(p.bot?' bot':'');avatar.style.setProperty('--chef-color',window.KitchenArt.colors[index%8]);avatar.textContent=p.bot?'🤖':'👩‍🍳';avatar.title=p.name+(p.bot?' · bot':'');avatar.setAttribute('role','img');avatar.setAttribute('aria-label',avatar.title);return avatar;}));
    KitchenTimer.update(s);
    el('invite').hidden=s.demo;
    el('practice').hidden=!s.demo;
    if(s.demo) {
      const lesson=s.lesson;
      el('lesson-number').textContent='DEMO ROUND '+lesson.round+' OF '+lesson.total+' · '+lesson.recipe;
      el('lesson-title').textContent=lesson.title;
      if(el('lesson-steps').dataset.round!==String(lesson.round)) {
        el('lesson-steps').replaceChildren(...lesson.steps.map(step => {const li=document.createElement('li');li.textContent=step;return li;}));
        el('lesson-steps').dataset.round=lesson.round;
      }
      el('next-demo').hidden=active;
      el('next-demo').dataset.finish=String(lesson.round===lesson.total);
      el('next-demo').textContent=lesson.round===lesson.total?'Finish demo → Join a real kitchen':'Next sample round →';
      el('lesson-result').textContent=active?'Goal: serve one '+lesson.recipe+'.':s.demo_served?'Dish complete! Continue or retry to practice again.':'Time is up. Retry this lesson or continue when you’re ready.';
      el('start').textContent='Retry sample round';
      el('target').textContent='1 dish';
      el('room').textContent='DEMO '+lesson.round+'/3';
    } else el('room').textContent=session.room;
  }
  function reset() {lastRoom=null;lastEvent=0;currentState=null;alerts.replaceChildren();KitchenTimer.reset();}
  return {init, update, showError, reset};
})();
