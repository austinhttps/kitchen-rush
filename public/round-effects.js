/* A compact in-game menu; host commands and shortcut instructions live here. */
window.RoundEffects=(()=>{
  const el=id=>document.getElementById(id);
  let localOpen=false,latest=null,callbacks,lastRound=null,lastFinished=false;
  const pause=document.createElement('button');pause.id='pause';pause.textContent='Pause';el('fullscreen').before(pause);
  const hostMenu=document.createElement('button');hostMenu.id='host-menu';hostMenu.textContent='Host controls';el('pause').before(hostMenu);
  const overlay=document.createElement('section');overlay.id='pause-overlay';overlay.hidden=true;overlay.setAttribute('aria-label','Kitchen menu');
  overlay.innerHTML='<div class="pause-card"><div class="eyebrow" id="menu-role"></div><h2 id="menu-title">The pass is yours</h2><p id="pause-host-note"></p><button id="resume-game" class="primary">Back to the line</button><section id="host-controls"><h3>🧑‍🍳 Host controls</h3><p class="host-controls-note">You’re in charge of who cooks and when.</p><div class="menu-buttons"><button id="host-start" class="primary">Start service</button><button id="host-restart">Set up a fresh shift</button><button id="host-end" class="danger-button">Close the kitchen</button></div></section><section class="key-guide"><h3>🎮 Kitchen controls</h3><div class="control-card-grid"><article class="control-mini-card"><span>🏃</span><kbd>WASD<br>Arrows</kbd><strong>Move</strong></article><article class="control-mini-card"><span>🍳</span><kbd>E</kbd><strong>Work / pick up</strong></article><article class="control-mini-card"><span>🥏</span><kbd>F</kbd><strong>Throw food</strong></article><article class="control-mini-card"><span>🧹</span><kbd>X</kbd><strong>Discard</strong></article><article class="control-mini-card"><span>📋</span><kbd>P / Esc</kbd><strong>Open menu</strong></article><article class="control-mini-card"><span>⛶</span><kbd>Shift + F</kbd><strong>Toggle fullscreen</strong></article><article class="control-mini-card"><span>🎯</span><kbd>Click / tap</kbd><strong>Aim a throw</strong></article></div></section><div class="menu-buttons"><button id="arena-sound" aria-pressed="true">♫ Sound on</button><button id="menu-fullscreen">⛶ Fullscreen</button><button id="arena-home">Leave kitchen</button></div><p id="menu-error" class="dialog-error" role="alert"></p></div>';
  el('arena').append(overlay);
  const confirm=document.createElement('dialog');confirm.id='host-confirm';confirm.setAttribute('aria-labelledby','host-confirm-title');
  confirm.innerHTML='<div class="modal-header"><strong id="host-confirm-title"></strong></div><div class="modal-body"><p id="host-confirm-copy"></p><div class="dialog-actions"><button id="host-cancel">Keep cooking</button><button id="host-confirm-action" class="danger-button">Confirm</button></div><p id="host-confirm-error" class="dialog-error" role="alert"></p></div>';
  document.body.append(confirm);
  const banner=document.createElement('div');banner.id='chaos-banner';banner.hidden=true;banner.setAttribute('role','status');el('arena').append(banner);
  let pendingAction=null,pendingData={};
  function blocked(){return localOpen||!!latest?.state.paused;}
  function show(){
    if(!latest)return;
    localOpen=true;callbacks.resetInput();paint();
    const {state:s,session}=latest;
    if(s.host===session.token&&s.started&&!s.finished&&!s.paused&&s.wall_now>=s.launch_at)callbacks.act('pause',{paused:true});
  }
  async function close(){
    if(latest?.state.paused){
      if(latest.state.host!==latest.session.token)return;
      if(!await callbacks.act('pause',{paused:false}))return;
    }
    localOpen=false;overlay.hidden=true;el('canvas').focus({preventScroll:true});
  }
  function ask(action,data={}){
    pendingAction=action;pendingData=data;
    el('host-confirm-title').textContent=action==='restart'?'Restart this round?':action==='kick'?'Remove this teammate?':'End service now?';
    el('host-confirm-copy').textContent=action==='restart'?'The team score and current orders will reset. Everyone gets a new countdown.':action==='kick'?data.bot?'Remove '+data.name+' from this kitchen? The bot will stop working immediately.':'Remove '+data.name+' from this kitchen and send them to the lobby? They can rejoin with a new invite.':'Service will end for every chef and the final results will appear.';
    if(action==='restart')RestartSetup.open(latest.state,latest.session);else RestartSetup.hide();
    el('host-confirm-action').textContent=action==='restart'?'Apply setup & restart':action==='kick'?data.bot?'Remove bot':'Remove player':'End round';el('host-confirm-error').textContent='';confirm.showModal();
  }
  const resultsButton=document.createElement('button');resultsButton.id='menu-results';resultsButton.textContent='View results';resultsButton.hidden=true;el('resume-game').after(resultsButton);
  function init(options){
    callbacks=options;
    el('arena-menu').onclick=el('host-menu').onclick=show;
    el('pause').onclick=()=>{if(latest?.state.paused)close();else show();};
    el('resume-game').onclick=close;
    el('arena-home').onclick=options.leave;
    el('menu-results').onclick=()=>el('view-results').click();
    el('menu-fullscreen').onclick=()=>el('window-fullscreen').click();
    el('host-start').onclick=()=>callbacks.act('start');
    el('host-restart').onclick=()=>ask('restart');el('host-end').onclick=()=>ask('end');
    el('host-cancel').onclick=()=>confirm.close();
    el('host-confirm-action').onclick=async()=>{
      el('host-confirm-action').disabled=true;
      try{if(await callbacks.act(pendingAction,pendingAction==='restart'?RestartSetup.payload():pendingData)){confirm.close();if(pendingAction!=='kick')localOpen=false;}else el('host-confirm-error').textContent='The host action failed. Check the connection and try again.';}
      finally{el('host-confirm-action').disabled=false;}
    };
  }
  function paint(){
    if(!latest)return;
    const {state:s,session}=latest,host=s.host===session.token,live=s.started&&!s.finished,counting=s.wall_now<s.launch_at;
    overlay.hidden=!localOpen&&!s.paused;
    KitchenAudio.menu(!overlay.hidden);
    el('host-menu').hidden=!host;el('host-controls').hidden=!host;
    for(const id of ['room-difficulty','room-bots'])el(id).closest('label').hidden=!host;
    el('hud-difficulty-readout').hidden=host;el('hud-bots-readout').hidden=host;
    el('pause').hidden=!host;el('pause').disabled=!live||counting;
    el('pause').textContent=s.paused?'Resume':'Pause';el('pause').setAttribute('aria-pressed',String(s.paused));
    el('menu-role').textContent=!s.started?(host?'TONIGHT, YOU’RE THE CHEF':'YOUR TABLE IS READY'):host?'HEAD CHEF ON THE PASS':'YOUR KITCHEN CREW';
    el('menu-title').textContent=!s.started?(host?'Aprons on. Ready when you are.':'Waiting for the head chef'):s.paused?'A little breather':'Kitchen menu';
    el('pause-host-note').textContent=!s.started?(host?'Gather your crew, then call “Service!” to start the 2½-minute rush.':'The head chef will call service when the kitchen is ready.'):s.paused?'Orders, burners, and the clock are taking a breather.':host?'You’re steering the whole kitchen. Pause here whenever the crew needs a reset.':'Service keeps moving until the host calls a pause.';
    el('resume-game').hidden=!s.started;el('resume-game').textContent=s.paused?(host?'Back to the burners':'Waiting for the host'):'Back to the line';el('resume-game').disabled=s.paused&&!host;
    el('host-start').hidden=live;el('host-start').textContent=s.finished?'Call the crew back':'Start service · 2:30';
    el('menu-results').hidden=!s.finished;
    el('host-restart').disabled=!s.started;el('host-end').disabled=!live;
  }
  function update(s,session){
    if(lastRound!==s.round_id||s.finished&&!lastFinished){localOpen=false;if(confirm.open)confirm.close();}
    lastRound=s.round_id;lastFinished=s.finished;latest={state:s,session};
    if(!s.started&&!s.finished)localOpen=true;
    if(s.paused)callbacks.resetInput();paint();
    KitchenMenuDetails.update(s,session,(id,name,bot)=>ask('kick',{player:id,name,bot}));
    const event=s.chaos;banner.hidden=!event||s.paused||s.finished;
    if(event){const text=event.phase==='warning'?event.label+' · in '+Math.max(1,Math.ceil(event.start-s.now))+'s':event.label;if(banner.textContent!==text)banner.textContent=text;banner.className=event.phase;}
  }
  function reset(){localOpen=false;latest=null;lastRound=null;lastFinished=false;overlay.hidden=true;banner.hidden=true;KitchenAudio.menu(false);KitchenMenuDetails.reset();if(confirm.open)confirm.close();}
  function toggle(){if(blocked())close();else show();}
  return {init,update,reset,blocked,toggle,setupRestart:()=>ask('restart')};
})();
