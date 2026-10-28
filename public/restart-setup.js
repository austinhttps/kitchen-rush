/* Review next-round difficulty and chef removals before one atomic restart. */
window.RestartSetup=(()=>{
  const fieldset=document.createElement('fieldset');fieldset.id='restart-options';fieldset.hidden=true;
  fieldset.innerHTML='<legend>Set up the next shift</legend><label>Level difficulty<select id="restart-difficulty"></select></label><p>Keep checked chefs. Uncheck players or bots to remove them when the new shift starts.</p><div id="restart-crew"></div>';
  document.getElementById('host-confirm-copy').after(fieldset);
  function open(state,session){
    fieldset.hidden=false;
    const select=document.getElementById('restart-difficulty');select.replaceChildren();select.disabled=state.demo;
    for(const [id,config] of Object.entries(state.difficulties)){const option=document.createElement('option');option.value=id;option.textContent=config.label;select.append(option);}
    select.value=state.difficulty;
    const crew=document.getElementById('restart-crew');crew.replaceChildren();
    for(const [id,player] of Object.entries(state.players)){
      const label=document.createElement('label'),check=document.createElement('input');
      check.type='checkbox';check.checked=true;check.dataset.keepChef=id;check.disabled=id===session.token||state.demo;
      label.append(check,document.createTextNode(player.name+(id===session.token?' · Host':player.bot?' · Bot':' · Player')));crew.append(label);
    }
  }
  function payload(){return {difficulty:document.getElementById('restart-difficulty').value,
    remove:[...fieldset.querySelectorAll('[data-keep-chef]')].filter(input=>!input.checked).map(input=>input.dataset.keepChef)};}
  return {open,payload,hide:()=>fieldset.hidden=true};
})();
