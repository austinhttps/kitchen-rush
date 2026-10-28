/* Separate service and menu soundtracks, plus kitchen sound effects. */
window.KitchenAudio = (() => {
  let context=null,master=null,enabled=localStorage.getItem('kitchen-sound')!=='off',state=null;
  let lastSecond=-1,lastWash=0,lastFire=0,lastEvent=0,room=null,round=null,observed=0,playPending=false,musicBlocked=false,musicFailure=null,menuPlayPending=false,menuOverride=false;
  const music=document.createElement('audio');music.id='kitchen-music';music.src='cyborg-ninja-kevin-macleod-main-version-7993-03-00.mp3';
  music.loop=true;music.preload='metadata';music.volume=.28;document.body.append(music);
  const menuTrack=document.createElement('audio');menuTrack.id='menu-music';menuTrack.src='Local%20Forecast%20-%20Elevator.mp3';
  menuTrack.loop=true;menuTrack.preload='metadata';menuTrack.volume=.22;document.body.append(menuTrack);
  function live(){return state?.started&&!state.finished&&!state.paused&&!menuOverride&&state.wall_now>=state.launch_at&&enabled&&!document.hidden;}
  function playbackError(error){
    // Pausing at countdown/menu boundaries can cancel an in-flight play request.
    if(error.name==='AbortError'&&!live())return;
    musicBlocked=true;buttons();
    if(error.name!=='NotAllowedError')musicFailure='Background music failed: '+error.message;
  }
  function syncMusic(){
    if(!live()){music.pause();return;}
    if(music.paused&&!playPending&&!musicBlocked){playPending=true;music.play().catch(playbackError).finally(()=>playPending=false);}
  }
  function menuMusicWanted(){return !!state&&enabled&&!document.hidden&&(menuOverride||!state.started||state.paused||state.finished);}
  function syncMenuMusic(){
    if(!menuMusicWanted()){
      menuTrack.pause();
      return;
    }
    if(menuTrack.paused&&!menuPlayPending){menuPlayPending=true;menuTrack.play().catch(error=>{if(error.name!=='NotAllowedError')musicFailure='Menu music failed: '+error.message;}).finally(()=>menuPlayPending=false);}
  }
  function menu(open){menuOverride=open;syncMusic();syncMenuMusic();}
  function countdown(beat){
    if(beat>0){tone(beat===1?659:beat===2?784:beat===3?880:1046,.24,.075,'sine');return;}
    tone(523,.22,.075,'sine');tone(659,.22,.075,'sine',.12);tone(784,.3,.085,'sine',.24);tone(1046,.42,.09,'sine',.4);
  }
  function roundEnd(){tone(784,.28,.075,'sine');tone(659,.36,.075,'sine',.2);tone(523,.55,.085,'sine',.44);}
  music.addEventListener('error',()=>playbackError(Error('Unable to load the service soundtrack (media error '+music.error.code+').')));
  menuTrack.addEventListener('error',()=>{musicFailure='Unable to load the uploaded menu soundtrack (media error '+menuTrack.error.code+').';});
  function tone(frequency,duration=.12,volume=.06,type='sine',delay=0){
    if(!context||!enabled||context.state!=='running')return;
    const oscillator=context.createOscillator(),gain=context.createGain(),at=context.currentTime+delay;
    oscillator.type=type;oscillator.frequency.value=frequency;
    gain.gain.setValueAtTime(0,at);gain.gain.linearRampToValueAtTime(volume,at+.012);gain.gain.exponentialRampToValueAtTime(.0001,at+duration);
    oscillator.connect(gain);gain.connect(master);oscillator.start(at);oscillator.stop(at+duration+.02);
  }
  function noise(duration,volume,frequency){
    if(!context||!enabled||context.state!=='running')return;
    const buffer=context.createBuffer(1,Math.ceil(context.sampleRate*duration),context.sampleRate),samples=buffer.getChannelData(0);
    for(let i=0;i<samples.length;i++)samples[i]=(Math.random()*2-1)*(1-i/samples.length);
    const source=context.createBufferSource(),filter=context.createBiquadFilter(),gain=context.createGain();
    source.buffer=buffer;filter.type='bandpass';filter.frequency.value=frequency;gain.gain.value=volume;
    source.connect(filter);filter.connect(gain);gain.connect(master);source.start();source.stop(context.currentTime+duration);
  }
  function effect(name){
    if(name==='serve'||name==='ready'||name==='washed'){tone(660,.15,.06);tone(880,.2,.045,'sine',.13);}
    if(name==='wrong'||name==='bonk'){tone(140,.2,.09,'triangle');tone(90,.25,.06,'triangle',.12);}
    if(name==='throw'){noise(.15,.12,1200);tone(400,.1,.025,'triangle');}
    if(name==='fire'){noise(.5,.19,850);tone(520,.15,.07,'square');tone(390,.16,.05,'square',.2);}
  }
  function buttons(){
    for(const id of ['sound','arena-sound']){const button=document.getElementById(id);if(button){button.textContent=enabled?(context?.state==='running'&&!musicBlocked?'♫ Sound on':'♫ Enable sound'):'♫ Sound off';button.setAttribute('aria-pressed',String(enabled&&context?.state==='running'&&!musicBlocked));}}
  }
  async function unlock(){
    if(!enabled){buttons();return;}
    if(!context){context=new AudioContext();master=context.createGain();master.gain.value=.4;master.connect(context.destination);}
    await context.resume();musicBlocked=false;
    try{await music.play();if(!live())music.pause();}catch(error){playbackError(error);}
    buttons();
  }
  async function toggle(){
    if(enabled&&(!context||context.state!=='running'||musicBlocked)){await unlock();return;}
    enabled=!enabled;localStorage.setItem('kitchen-sound',enabled?'on':'off');
    if(master)master.gain.value=enabled&&!document.hidden ? .4 : 0;
    if(!enabled){music.pause();menuTrack.pause();}await unlock();buttons();
  }
  function update(s,session){
    if(musicFailure){KitchenUX.showError(musicFailure);musicFailure=null;}
    const endedThisUpdate=room===session.room&&!!state&&state.round_id===s.round_id&&!state.finished&&s.finished;
    state=s;observed=performance.now();if(master)master.gain.value=enabled&&!document.hidden ? .4 : 0;
    if(room!==session.room||round!==s.round_id){room=session.room;round=s.round_id;music.currentTime=0;lastSecond=-1;lastEvent=s.event_id-1;}
    syncMusic();syncMenuMusic();if(endedThisUpdate)roundEnd();
    for(const event of s.events)if(event.id>lastEvent){if(event.sound)effect(event.sound);lastEvent=event.id;}
  }
  function reset(){state=null;room=null;round=null;menuOverride=false;music.pause();menuTrack.pause();music.currentTime=0;menuTrack.currentTime=0;}
  setInterval(()=>{
    syncMusic();syncMenuMusic();
    if(!live()||!context)return;
    const now=state.now+(performance.now()-observed)/1000,remaining=Math.max(0,Math.ceil(state.end-now));
    if(remaining===0)return;
    if(remaining>0&&remaining!==lastSecond){lastSecond=remaining;tone(remaining%2?1100:850,.04,remaining<=30 ? .08 : .018,remaining<=30?'square':'sine');}
    if(Object.values(state.players).some(p=>p.task?.kind==='wash')&&now-lastWash>.35){lastWash=now;noise(.28,.12,2200);}
    if(state.stations.some(s=>s.item==='fire')&&now-lastFire>.7){lastFire=now;noise(.45,.18,700);tone(420,.13,.04,'square');}
  },70);
  document.addEventListener('visibilitychange',()=>{if(master)master.gain.value=enabled&&!document.hidden ? .4 : 0;syncMusic();syncMenuMusic();});
  return {unlock,toggle,update,reset,buttons,countdown,menu};
})();
