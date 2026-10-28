/* Three explicit entry flows; setup inputs never leak into joining or demo. */
window.KitchenLobby = (() => {
  const el=id=>document.getElementById(id);
  let mode='create';
  function formatCode(value){const raw=value.toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,6);return raw.slice(0,3)+(raw.length>3?'-'+raw.slice(3):'');}
  function show(next){
    mode=next;el('lobby-panel').hidden=false;
    el('join-fields').hidden=next!=='join';el('create-fields').hidden=next!=='create';
    el('code').disabled=next!=='join';el('code').required=next==='join';
    el('difficulty').disabled=el('bots').disabled=next!=='create';
    el('entry-title').textContent=next==='join'?'Join your crew':'Set up your kitchen';
    el('submit-entry').textContent=next==='join'?'Join kitchen →':'Create kitchen →';
    el('show-join').setAttribute('aria-expanded',String(next==='join'));
    el('show-create').setAttribute('aria-expanded',String(next==='create'));
    el('lobby-error').textContent='';
    el(next==='join'&&!el('code').value?'code':'name').focus({preventScroll:true});
    el('lobby-panel').scrollIntoView({behavior:'instant',block:'nearest'});
  }
  function reset(){
    el('lobby-panel').hidden=true;
    for(const id of ['show-join','show-create'])el(id).setAttribute('aria-expanded','false');
    el('lobby-error').textContent='';
  }
  function init({enter}){
    el('demo').onclick=()=>enter('demo');
    el('show-join').onclick=()=>show('join');el('show-create').onclick=()=>show('create');
    el('entry-back').onclick=reset;
    el('join').onsubmit=event=>{event.preventDefault();enter(mode);};
    el('code').addEventListener('input',()=>{el('code').value=formatCode(el('code').value);});
    const invite=new URLSearchParams(location.search).get('room');
    if(invite){el('code').value=formatCode(invite);show('join');}
  }
  function payload(){return mode==='join'?{name:el('name').value,room:el('code').value}:{name:el('name').value,difficulty:el('difficulty').value,bots:Number(el('bots').value)};}
  function pending(value){for(const id of ['demo','show-join','show-create','submit-entry'])el(id).disabled=value;}
  return {init,reset,payload,pending};
})();
