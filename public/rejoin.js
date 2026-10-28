/* Persistent own-chef credentials stay in browser storage; URLs contain only room codes. */
window.RejoinFlow=(()=>{
  const KEY='kitchen-rejoin',el=id=>document.getElementById(id);
  let saved=null,callbacks,interrupted=false,failures=0,unavailable=false;
  const dialog=document.createElement('dialog');dialog.id='rejoin-dialog';dialog.setAttribute('aria-labelledby','rejoin-title');
  dialog.innerHTML='<div class="modal-header"><strong id="rejoin-title">Your kitchen is waiting</strong></div><div class="modal-body"><p id="rejoin-copy"></p><p id="rejoin-error" class="dialog-error" role="alert"></p><div class="dialog-actions"><button id="rejoin-confirm" class="primary">Rejoin game</button><button id="rejoin-later">Not now</button><button id="rejoin-forget">Forget this kitchen</button></div></div>';
  document.body.append(dialog);
  const offer=document.createElement('div');offer.id='saved-kitchen';offer.hidden=true;
  offer.innerHTML='<span id="saved-kitchen-copy"></span><button id="saved-kitchen-open">Rejoin</button>';
  el('lobby-feedback').append(offer);
  function load(){
    const raw=sessionStorage.getItem('kitchen')||localStorage.getItem(KEY);
    if(!raw)return null;
    let record;
    try{record=JSON.parse(raw);}catch(error){sessionStorage.removeItem('kitchen');localStorage.removeItem(KEY);callbacks.onError(Error('The saved kitchen record could not be read. Please create or join a room.'));return null;}
    if(typeof record.room!=='string'||typeof record.token!=='string')throw Error('Invalid saved kitchen record.');
    return record;
  }
  function refreshOffer(){offer.hidden=!saved;if(saved)el('saved-kitchen-copy').textContent='Saved kitchen '+saved.room+(saved.name?' · '+saved.name:'');}
  function remember(session,details={}){
    unavailable=false;
    saved={room:session.room,token:session.token,name:details.name??null,demo:details.demo===true,savedAt:Date.now()};
    const text=JSON.stringify(saved);sessionStorage.setItem('kitchen',text);localStorage.setItem(KEY,text);refreshOffer();
  }
  function metadata(s,session){const name=s.players[s.you].name;if(saved?.token!==session.token||saved.name!==name||saved.demo!==s.demo)remember(session,{name,demo:s.demo});}
  function ask(lost=false){
    if(!saved)return;
    interrupted=true;callbacks.resetInput();
    el('rejoin-title').textContent=lost?'Connection interrupted':'Your kitchen is waiting';
    el('rejoin-copy').textContent=(saved.name?saved.name+', rejoin ':'Rejoin ')+'kitchen '+saved.room+'? Your chef, inventory, and place in the crew will be restored.';
    el('rejoin-error').textContent='';el('rejoin-confirm').disabled=unavailable;
    if(!dialog.open)dialog.showModal();
  }
  function idle(){interrupted=false;failures=0;if(dialog.open)dialog.close();refreshOffer();}
  function forget(session){
    const identity=session||saved;
    const local=localStorage.getItem(KEY);
    if(local){const record=JSON.parse(local);if(identity&&record.token===identity.token)localStorage.removeItem(KEY);}
    sessionStorage.removeItem('kitchen');saved=null;unavailable=false;idle();
  }
  function decline(){idle();if(callbacks.getSession())callbacks.home({forget:false});}
  function expired(message){unavailable=true;ask();el('rejoin-error').textContent=message;}
  function init(options){
    callbacks=options;saved=load();refreshOffer();
    el('saved-kitchen-open').onclick=()=>ask();
    el('rejoin-later').onclick=decline;
    el('rejoin-forget').onclick=()=>{forget(callbacks.getSession());callbacks.home();};
    dialog.addEventListener('cancel',event=>{event.preventDefault();decline();});
    el('rejoin-confirm').onclick=async()=>{
      el('rejoin-confirm').disabled=true;el('rejoin-error').textContent='';
      try{await callbacks.resume(saved);unavailable=false;idle();}
      catch(error){if(error.status===400||error.status===404)unavailable=true;el('rejoin-error').textContent=error.message;}
      finally{el('rejoin-confirm').disabled=unavailable;}
    };
    window.addEventListener('offline',()=>{if(callbacks.getSession())ask(true);});
    const invite=new URLSearchParams(location.search).get('room');
    if(saved&&(!invite||invite.toUpperCase().replace('-','')===saved.room.replace('-','')))ask();
  }
  function failed(error){failures++;if(failures>=2){ask(true);el('rejoin-error').textContent='Could not reach the kitchen. Check your connection, then choose Rejoin game.';}}
  return {init,remember,metadata,forget,idle,expired,failed,good:()=>{failures=0;},blocked:()=>interrupted};
})();
