/* Shared dialog lifecycle: pointer-safe handbook, leave guard, and round results. */
window.GameDialogs = (() => {
  const el = id => document.getElementById(id);
  const guide = el('rules'), exit = el('exit-dialog'), results = el('results-dialog');
  let callbacks, latest = null, shownRound = null, pending = false;
  function blocked() { return !!document.querySelector('dialog[open]'); }
  function open(dialog) {
    callbacks.resetInput();
    if (!dialog.open) dialog.showModal();
  }
  function requestExit() {
    if (!callbacks.isInGame()) return;
    el('exit-error').textContent = '';
    open(exit);
  }
  async function roundAction(action) {
    if (pending) return;
    pending = true;
    el('results-error').textContent = '';
    try {
      const success = await callbacks.act(action);
      if (!success) el('results-error').textContent = 'Could not start the round. Check the connection and try again.';
    } finally { pending = false; }
  }
  function init(options) {
    callbacks = options;
    el('help').onclick = () => open(guide);
    el('home-link').addEventListener('click', event => {
      if (callbacks.isInGame()) {event.preventDefault(); requestExit();}
    });
    guide.addEventListener('click', event => {
      const bounds = guide.getBoundingClientRect();
      if (event.target === guide && (event.clientX < bounds.left || event.clientX > bounds.right ||
          event.clientY < bounds.top || event.clientY > bounds.bottom)) guide.close();
    });
    el('exit-cancel').onclick = () => exit.close();
    el('exit-confirm').onclick = async () => {
      if (pending) return;
      pending = true;
      el('exit-confirm').disabled = el('exit-cancel').disabled = true;
      try { await callbacks.leave(); }
      catch(error) { el('exit-error').textContent = error.message; }
      finally {pending = false; el('exit-confirm').disabled = el('exit-cancel').disabled = false;}
    };
    exit.addEventListener('cancel', event => {if(pending) event.preventDefault();});
    el('results-close').onclick = () => results.close();
    el('results-home').onclick = requestExit;
    el('results-rematch').onclick = () => {
      if(latest.state.demo)roundAction('start');else{results.close();RoundEffects.setupRestart();}
    };
    el('results-next').onclick = () => {
      if (latest.state.lesson.round === latest.state.lesson.total) requestExit();
      else roundAction('next_demo');
    };
    el('view-results').onclick = () => {if (latest?.state.finished) open(results);};
    window.addEventListener('beforeunload', event => {
      if (callbacks.isInGame()) {event.preventDefault(); event.returnValue = '';}
    });
  }
  function renderResults(state, session) {
    const summary = state.results;
    const host = state.host === session.token;
    el('results-level').textContent = summary.demo ? 'DEMO ROUND '+state.lesson.round+' OF '+state.lesson.total : summary.difficulty+' · COOPERATIVE ROUND';
    el('results-title').textContent = summary.demo ? (summary.won ? 'Practice dish complete!' : 'Practice time is up') :
      (summary.won ? 'Kitchen crew wins!' : summary.reason?'Kitchen shut down!':'Target missed. Next shift?');
    el('results-outcome-copy').textContent = summary.demo ? (summary.won ? 'Lesson complete. Keep practicing or move on to the next recipe.' : 'You can retry this recipe or continue to the next lesson.') :
      (summary.won ? 'Winning team: Kitchen crew — every chef shares the victory.' : summary.reason||'No winning team this round — your crew finished below the target.');
    el('results-outcome-icon').textContent = summary.demo ? (summary.won?'🥗':'⏱️') : summary.won ? '🏆' : /fire|stove/i.test(summary.reason||'') ? '🔥' : '🎯';
    el('results-score').textContent = summary.score;
    el('results-target').textContent = summary.demo ? '1 correct dish' : summary.target;
    const metrics = [['🍽️','Orders served',summary.stats.served], ['🥴','Wrong dishes',summary.stats.incorrect],
      ['⌛','Expired tickets',summary.stats.expired], ['🔥','Food burned',summary.stats.burned], ['✨','Best streak','×'+summary.stats.best_combo],
      ['👑','VIPs served',summary.stats.vip_served],['🧐','VIPs missed',summary.stats.vip_missed],['🥤','Drinks served',summary.stats.drinks]];
    el('results-stats').replaceChildren(...metrics.map(([icon,label,value]) => {
      const group=document.createElement('div'),term=document.createElement('dt'),definition=document.createElement('dd');
      term.textContent=icon+' '+label; definition.textContent=value; group.append(term,definition);return group;
    }));
    el('results-chefs').replaceChildren(...summary.chefs.map(chef => {
      const item=document.createElement('li'),icon=document.createElement('span'),name=document.createElement('strong'),orders=document.createElement('small'),count=document.createElement('b');
      item.className='chef-result-card';icon.className='chef-result-icon';icon.textContent='👨‍🍳';name.textContent=chef.name;orders.textContent='Orders served';count.textContent=chef.served;item.append(icon,name,orders,count);return item;
    }));
    el('results-rematch').textContent = summary.demo ? 'Retry sample round' : 'Rematch setup';
    el('results-rematch').disabled = !host || pending;
    el('rematch-hint').textContent = host ? (summary.demo ? 'Practice at your own pace.' : 'You’re the host. Review difficulty and crew in Rematch setup, then start the next shift.') : 'Waiting for the host to start a rematch.';
    el('results-next').hidden = !summary.demo;
    if(summary.demo) el('results-next').textContent=state.lesson.round===state.lesson.total?'Finish demo →':'Next demo round →';
    el('results-next').disabled=pending;
  }
  function update(state, session) {
    latest = {state, session};
    el('view-results').hidden = !state.finished;
    if (!state.finished) {
      if(results.open) results.close();
      shownRound = null;
      return;
    }
    renderResults(state, session);
    const id=session.room+':'+state.round_id;
    if (shownRound!==id && !exit.open && !guide.open) {open(results); shownRound=id;}
  }
  function reset() {
    for(const dialog of [guide,exit,results]) if(dialog.open) dialog.close();
    latest=null; shownRound=null;
  }
  return {init,update,blocked,requestExit,reset};
})();
