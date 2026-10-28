/* Brief, pointer-free kitchen distractions; critical HUD remains in the DOM above. */
window.KitchenChaos=(()=>{
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  function draw(ctx,s,now){
    const event=s.chaos;
    if(!event||s.finished||s.paused)return;
    const art=KitchenArt,t=now-event.start,intensity=event.intensity;
    ctx.save();ctx.beginPath();ctx.rect(42,176,1040,800);ctx.clip();
    if(event.phase==='warning'){
      for(const [index,station] of s.stations.entries()){
        if(event.stations.includes(index)){
          ctx.strokeStyle='#edb948';ctx.lineWidth=5;ctx.setLineDash([8,7]);ctx.strokeRect(42+station.x*80-41,176+station.y*80-41,82,82);ctx.setLineDash([]);
        }
      }
    }else if(event.kind==='steam'||event.kind==='rush'){
      for(let i=0;i<Math.min(11,3+intensity);i++){
        const speed=reduced.matches?0:t*72,x=42+(i*173+speed)%1040,y=320+(i%3)*190;
        for(let j=0;j<4;j++){ctx.fillStyle='#fff7df70';ctx.beginPath();ctx.ellipse(x+j*33,y+Math.sin(i+j)*24,67,48,0,0,7);ctx.fill();}
      }
    }else if(event.kind==='carousel'){
      ctx.strokeStyle='#e7b85388';ctx.lineWidth=8;ctx.setLineDash([22,18]);
      ctx.beginPath();ctx.ellipse(562,576,430,315,reduced.matches?0:Math.sin(t)*.04,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);
      art.text(ctx,'↻ KITCHEN CAROUSEL',562,230,22,'#76592a');
    }else if(event.kind==='confetti'){
      for(let i=0;i<24+intensity*5;i++){
        const x=60+(i*89)%990,y=190+((i*41+(reduced.matches?0:t*90))%750);
        ctx.save();ctx.translate(x,y);ctx.rotate(reduced.matches ? .1 : Math.sin(t+i)*.5);
        art.box(ctx,-9,-17,18,34,i%3?'#fff9e6dd':'#edc168cc',2);
        ctx.strokeStyle='#a7895c';ctx.beginPath();ctx.moveTo(-5,-6);ctx.lineTo(5,-6);ctx.stroke();ctx.restore();
      }
    }
    ctx.restore();
  }
  return {draw,reducedMotion:()=>reduced.matches};
})();
