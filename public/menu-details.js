/* Compact menu cards for the crew, recipes, and service hazards. */
window.KitchenMenuDetails=(()=>{
  const el=id=>document.getElementById(id),section=document.createElement('section');section.className='menu-details';
  section.innerHTML='<div class="menu-card"><h3><span>👩‍🍳</span> The crew <b id="menu-crew-count"></b></h3><div id="menu-crew" class="mini-card-grid"></div><div id="menu-service-stats" class="menu-metric-grid"></div></div><div class="menu-card"><h3><span>🍽️</span> Meals & drinks</h3><div id="menu-recipes" class="mini-card-grid recipe-mini-grid"></div></div><div class="menu-card rules-card"><h3><span>🔥</span> Keep the kitchen open</h3><div id="menu-loss-rules" class="menu-rule-grid"></div><p id="menu-loss-tip" class="menu-rule-tip"></p></div>';
  el('host-controls').after(section);
  const emergency=document.createElement('div');emergency.id='fire-emergency';emergency.hidden=true;emergency.setAttribute('role','status');
  emergency.innerHTML='<span class="fire-alert-icon" aria-hidden="true">🔥</span><span class="fire-alert-label">STOVE SHUTDOWN</span><strong id="fire-alert-time"></strong><span class="fire-alert-action">Extinguish the stove</span>';
  el('arena').append(emergency);
  const recipePanel=document.createElement('div');recipePanel.id='sidebar-drink';recipePanel.className='recipe';recipePanel.innerHTML='<span>🥤</span> <b>Lemonade</b><p>Mix at Drinks for 3 seconds → serve the cup</p>';document.querySelector('aside').append(recipePanel);
  const icons={Salad:'🥗',Burger:'🍔','Fish & rice':'🍱',Lemonade:'🥤'};
  let crewSignature='';
  function card(className){const node=document.createElement('article');node.className='mini-card '+className;return node;}
  function metric(icon,label,value){const node=document.createElement('div');node.className='menu-metric';node.innerHTML='<span>'+icon+' '+label+'</span><strong>'+value+'</strong>';return node;}
  function crewCards(s,session,onKick){
    return Object.entries(s.players).map(([id,p],index)=>{
      const node=card('crew-mini-card');node.style.setProperty('--chef-color',window.KitchenArt.colors[index%8]);
      const heading=document.createElement('div');heading.className='mini-card-heading';
      const name=document.createElement('strong');name.textContent=p.name;
      const role=document.createElement('span');role.className='mini-role';role.textContent=id===s.host?'HOST':p.bot?'BOT':id===session.token?'YOU':'CHEF';heading.append(name,role);
      const served=document.createElement('div');served.className='mini-number';served.innerHTML='<strong>'+p.served+'</strong><span>orders served</span>';node.append(heading,served);
      if(p.bot){const job=document.createElement('small');job.className='mini-job';job.textContent='🤖 '+p.bot_status;node.append(job);}
      if(s.host===session.token&&id!==session.token){node.classList.add('kickable');const kick=document.createElement('button');kick.type='button';kick.className='kick-button';kick.textContent='×';kick.setAttribute('aria-label','Remove '+p.name+(p.bot?' bot':'')+' from this kitchen');kick.title='Remove '+p.name+(p.bot?' bot':'')+' from this kitchen';kick.onclick=()=>onKick(id,p.name,p.bot);node.append(kick);}
      node.dataset.playerId=id;
      return node;
    });
  }
  function recipeCards(recipes){
    return Object.entries(recipes).map(([name,parts],index)=>{
      const node=card('recipe-mini-card'),heading=document.createElement('div');heading.className='mini-card-heading';
      const icon=document.createElement('span');icon.className='recipe-icon';icon.textContent=icons[name]||'🍽️';
      const title=document.createElement('strong');title.textContent=name;
      const number=document.createElement('span');number.className='recipe-index';number.textContent=String(index+1).padStart(2,'0');heading.append(icon,title,number);
      const details=document.createElement('small');details.textContent=name==='Lemonade'?'Mix 3s · serve the cup':parts.join(' + ');node.append(heading,details);return node;
    });
  }
  function rules(s){
    if(s.demo)return [metric('🧑‍🍳','Practice','SAFE'),metric('🧯','Shutdown','OFF')];
    return [metric('⛔','Score floor',s.score_floor),metric('🔥','Fire limit',s.fire_limit+'s')];
  }
  function update(s,session,onKick=()=>{}){
    const ids=Object.keys(s.players);
    el('menu-crew-count').textContent=ids.length+'/4';
    const membership=JSON.stringify(Object.entries(s.players).map(([id,p])=>[id,p.name,p.bot,id===s.host]));
    if(membership!==crewSignature){crewSignature=membership;el('menu-crew').replaceChildren(...crewCards(s,session,onKick));}
    for(const [id,p] of Object.entries(s.players)){
      const node=el('menu-crew').querySelector('[data-player-id="'+id+'"]');
      node.querySelector('.mini-number strong').textContent=p.served;
      const job=node.querySelector('.mini-job');if(job)job.textContent='🤖 '+p.bot_status;
    }
    el('menu-recipes').replaceChildren(...recipeCards(s.recipes));
    const customerLimit=s.difficulties[s.demo?'easy':s.difficulty].max_customers;
    el('menu-service-stats').replaceChildren(
      metric('⭐','Score',s.score),metric('🎯','Target',s.target||'—'),
      metric('🎟️','Customers',s.orders.length+s.diners.length+'/'+customerLimit),metric('🪑','Seated',s.diners.length+'/4'));
    el('menu-loss-rules').replaceChildren(...rules(s));
    el('menu-loss-tip').textContent=s.demo?'🧑‍🍳 Practice mode: enjoy the shift with no shutdown penalties.':'🧯 Extinguish each stove before its fire timer runs out.';
    recipePanel.hidden=!('Lemonade' in s.recipes);
    emergency.hidden=!s.fire_deadline||s.finished||s.paused||s.demo;
    if(!emergency.hidden)el('fire-alert-time').textContent=Math.max(0,Math.ceil(s.fire_deadline-s.now))+'s';
  }
  return {update,reset:()=>{emergency.hidden=true;crewSignature='';}};
})();
