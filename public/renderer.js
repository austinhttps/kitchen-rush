window.KitchenRenderer = (() => {
  const canvas=document.getElementById('canvas'),ctx=canvas.getContext('2d'),art=KitchenArt;
  canvas.width=1440;canvas.height=1040;
  let snapshot=null,session=null,received=0,aim=null,movement={dx:0,dy:0},movementChangedAt=0,localCorrection={x:0,y:0,started:0,duration:120};
  const motion=new Map();
  const origin={x:42,y:176},scale=80;
  function food(item){
    if(Array.isArray(item))return '🍽️'+item.map(food).join('');
    const kind=item.replace('chopped ','').replace('cooked ','');
    if(!(kind in KitchenArt.icons))throw Error('Unknown inventory item: '+item);
    return KitchenArt.icons[kind];
  }
  function timerTag(x,y,label,remaining,total){
    const width=78,left=x-width/2,top=y-72,ratio=Math.max(0,Math.min(1,remaining/total));
    art.box(ctx,left,top,width,28,'#173c31ed',7);art.text(ctx,label+' '+remaining.toFixed(1)+'s',x,top+10,11,'#fff4d3');
    ctx.fillStyle='#f0c568';ctx.fillRect(left+7,top+21,(width-14)*ratio,3);
  }
  function displayPosition(id,p,at){
    const track=motion.get(id);
    let x=p.x,y=p.y;
    if(track&&id!==session?.token){
      const t=Math.min(1,Math.max(0,(at-track.started)/track.duration));
      x=track.x+(track.toX-track.x)*t;
      y=track.y+(track.toY-track.y)*t;
    }
    if(id===session?.token&&!snapshot.paused&&!snapshot.finished&&p.stunned_until<=snapshot.now&&(movement.dx||movement.dy)){
      const length=Math.max(1,Math.hypot(movement.dx,movement.dy));
      const predictionStart=Math.max(received,movementChangedAt);
      let distance=Math.min(.22,Math.max(0,(at-predictionStart)/1000))*4;
      const steps=Math.max(1,Math.ceil(distance/.08));
      for(let step=0;step<steps;step++){
        const nx=x+movement.dx/length*distance/steps;
        const ny=y+movement.dy/length*distance/steps;
        if(nx<.3||nx>12.7||ny<.3||ny>9.4)break;
        if(snapshot.stations.some(station=>(station.x-nx)**2+(station.y-ny)**2<=.5))break;
        x=nx;y=ny;
      }
    }
    if(id===session?.token){
      const remaining=Math.max(0,1-(at-localCorrection.started)/localCorrection.duration);
      const ease=remaining*remaining;
      x+=localCorrection.x*ease;
      y+=localCorrection.y*ease;
    }
    return{x,y};
  }
  function update(s,who){
    const at=performance.now();
    if(snapshot&&session?.token===who.token){
      const duration=Math.min(220,Math.max(35,at-received));
      for(const[id,p]of Object.entries(s.players)){
        const previous=snapshot.players[id];
        if(!previous)continue;
        if(id===who.token){
          motion.delete(id);
          const from=displayPosition(id,previous,at),dx=from.x-p.x,dy=from.y-p.y,distance=Math.hypot(dx,dy);
          if(distance<=.9)localCorrection={x:dx,y:dy,started:at,duration:Math.min(180,Math.max(80,duration))};
          else localCorrection={x:0,y:0,started:at,duration:120};
          continue;
        }
        const from=displayPosition(id,previous,at),distance=Math.hypot(p.x-from.x,p.y-from.y);
        if(at-received>450||distance>1.4)motion.delete(id);
        else if(distance>.005)motion.set(id,{...from,toX:p.x,toY:p.y,started:at,duration});
        else motion.delete(id);
      }
      for(const id of motion.keys())if(!s.players[id])motion.delete(id);
    }else{motion.clear();localCorrection={x:0,y:0,started:at,duration:120};}
    snapshot=s;session=who;received=at;
  }
  function setMovement(dx,dy){
    if(dx!==movement.dx||dy!==movement.dy){movement={dx,dy};movementChangedAt=performance.now();}
  }
  function setAim(event){
    const r=canvas.getBoundingClientRect(),ratio=Math.min(r.width/canvas.width,r.height/canvas.height);
    const left=r.left+(r.width-canvas.width*ratio)/2,top=r.top+(r.height-canvas.height*ratio)/2;
    aim={x:((event.clientX-left)/ratio-origin.x)/scale,y:((event.clientY-top)/ratio-origin.y)/scale};
    canvas.focus({preventScroll:true});
  }
  canvas.addEventListener('pointerdown',setAim);
  function aimVector(){if(!aim||!snapshot)return{};const p=snapshot.players[session.token];return{dx:aim.x-p.x,dy:aim.y-p.y};}
  function clearAim(){aim=null;}
  function draw(){
    requestAnimationFrame(draw);
    if(!snapshot||document.getElementById('game').hidden)return;
    const s=snapshot,now=s.finished||s.paused?s.now:s.now+Math.min(.15,(performance.now()-received)/1000),me=s.players[session.token];
    art.room(ctx,s,now);
    const nearest=s.stations.reduce((a,b)=>Math.hypot(a.x-me.x,a.y-me.y)<=Math.hypot(b.x-me.x,b.y-me.y)?a:b);
    for(const station of s.stations){
      const motion=station.motion,progress=motion&&!KitchenChaos.reducedMotion()?Math.min(1,Math.max(0,(now-motion.start)/(motion.end-motion.start))):0;
      const x=origin.x+(motion?motion.from_x+(motion.to_x-motion.from_x)*progress:station.x)*scale,y=origin.y+(motion?motion.from_y+(motion.to_y-motion.from_y)*progress:station.y)*scale,near=station===nearest&&!motion&&Math.hypot(station.x-me.x,station.y-me.y)<1.55;
      art.station(ctx,station,x,y,near,now);
      if(station.kind==='stove'&&station.item&&station.item!=='fire'&&station.ready>now)timerTag(x,y,'COOK',station.ready-now,7);
      if(station.item!==null&&station.kind!=='stove'){
        art.text(ctx,food(station.item),x,y-4,26);
        if(Array.isArray(station.item)&&station.item.length)art.text(ctx,station.item.length+' ingredient'+(station.item.length===1?'':'s'),x,y+52,12);
      }
    }
    for(const item of s.floor){
      const x=origin.x+item.x*scale,y=origin.y+item.y*scale;
      art.circle(ctx,x,y+7,15,'#45624525');art.text(ctx,food(item.item),x,y+8,27);
    }
    for(const shot of s.projectiles){
      const advance=Math.min(5-shot.travelled,Math.max(0,now-shot.updated)*9),x=origin.x+(shot.x+shot.dx*advance)*scale,y=origin.y+(shot.y+shot.dy*advance)*scale;
      ctx.strokeStyle='#e6a85a';ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(x-shot.dx*28,y-shot.dy*28);ctx.lineTo(x,y);ctx.stroke();art.text(ctx,food(shot.item),x,y-12,30);
    }
    Object.entries(s.players).forEach(([id,p],index)=>{
      const position=displayPosition(id,p,performance.now()),x=origin.x+position.x*scale,y=origin.y+position.y*scale;
      if(id===session.token){ctx.strokeStyle='#f9e9a9';ctx.lineWidth=5;ctx.beginPath();ctx.ellipse(x,y+15,29,17,0,0,7);ctx.stroke();}
      art.person(ctx,x,y,art.colors[index%8],true);
      if(p.task&&p.task.end>now)timerTag(x,y-40,p.task.kind==='chop'?'CHOP':p.task.kind==='wash'?'CLEAN':'MIX',p.task.end-now,3);
      if(p.stunned_until>now)timerTag(x,y-40,'STUN',p.stunned_until-now,1.25);
      art.box(ctx,x-72,y-68,144,22,p.bot?'#e6e9d9':'#fff8e8',5);art.text(ctx,p.name+(p.bot?' · BOT':''),x,y-52,13);
      if(p.held!==null)art.text(ctx,food(p.held),x+28,y+12,26);
      if(p.stunned_until>now){for(let i=0;i<3;i++)art.text(ctx,'★',x+Math.cos(now*5+i*2)*32,y-25+Math.sin(now*5+i*2)*13,20,'#eab642');}
    });
    KitchenChaos.draw(ctx,s,now);
    if(aim&&!s.paused&&typeof me.held==='string'&&me.held!=='extinguisher'){
      const x=origin.x+aim.x*scale,y=origin.y+aim.y*scale;
      ctx.strokeStyle='#b77d3d';ctx.setLineDash([5,6]);ctx.beginPath();ctx.moveTo(origin.x+me.x*scale,origin.y+me.y*scale);ctx.lineTo(x,y);ctx.stroke();ctx.setLineDash([]);art.text(ctx,'⊕',x,y+8,28,'#ac6c30');
    }
  }
  requestAnimationFrame(draw);
  return {update,setMovement,aimVector,clearAim};
})();
