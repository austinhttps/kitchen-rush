/* Original canvas artwork for the bistro, stations, and chefs. */
window.KitchenArt = (() => {
  const colors=['#ef8a5c','#70a6d4','#be91c7','#e5ba50','#64b69f','#e48da6','#99ae5d','#b29b7c'];
  const icons={tomato:'🍅',lettuce:'🥬',meat:'🥩',fish:'🐟',rice:'🍚',bun:'🍞',chop:'🔪',stove:'🍳',plates:'🍽️',sink:'🫧',serve:'🛎️',counter:'',extinguisher:'🧯',fire:'🔥',drinks:'🍋',lemonade:'🥤','empty cup':'🥤'};
  function box(ctx,x,y,w,h,color,r=8){ctx.fillStyle=color;ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill();}
  function text(ctx,value,x,y,size=16,color='#365345',align='center'){
    ctx.fillStyle=color;ctx.font='600 '+size+'px "DM Sans",sans-serif';ctx.textAlign=align;ctx.fillText(value,x,y);
  }
  function circle(ctx,x,y,r,color){ctx.fillStyle=color;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();}
  function plant(ctx,x,y){box(ctx,x-13,y,26,24,'#bd7650',4);for(let i=0;i<5;i++)circle(ctx,x+Math.sin(i*2)*14,y-10+Math.cos(i*2)*12,12,i%2?'#62895d':'#436e4d');}
  function person(ctx,x,y,color,chef=false){
    ctx.fillStyle='#102e2525';ctx.beginPath();ctx.ellipse(x,y+25,24,9,0,0,7);ctx.fill();
    box(ctx,x-18,y+2,36,32,color,12);circle(ctx,x,y-6,17,'#f1c5a0');
    circle(ctx,x-6,y-7,2,'#3d4239');circle(ctx,x+6,y-7,2,'#3d4239');
    box(ctx,x-5,y+1,10,3,'#a16a50',1);
    if(chef){box(ctx,x-16,y-28,32,14,'#fffdf5',3);for(let i=-1;i<2;i++)circle(ctx,x+i*12,y-32,11,'#fffdf5');box(ctx,x-9,y+9,18,25,'#fff6e3',4);}
    else {ctx.strokeStyle='#684e38';ctx.lineWidth=5;ctx.beginPath();ctx.arc(x,y-10,17,Math.PI,Math.PI*2);ctx.stroke();}
  }
  function room(ctx,s,now){
    box(ctx,0,0,1440,1040,'#eadbc0',0);
    for(let i=0;i<24;i++){box(ctx,28+i*58,122,56,28,i%2?'#fff0d7':'#cd7156',0);}
    box(ctx,22,156,1080,840,'#547a65',13);
    for(let x=0;x<13;x++)for(let y=0;y<10;y++){
      ctx.fillStyle=(x+y)%2?'#c8d9be':'#e8edda';ctx.fillRect(42+x*80,176+y*80,79,79);
    }
    box(ctx,30,163,1064,17,'#bc8b5c',3);box(ctx,30,968,1064,20,'#a6754c',3);
    box(ctx,28,175,22,800,'#bd9062',3);box(ctx,1072,175,22,800,'#bd9062',3);
    for(let y=190;y<960;y+=80){box(ctx,30,y,18,57,'#d9b583',2);box(ctx,1074,y,18,57,'#d9b583',2);}
    box(ctx,1070,452,28,90,'#244b3d',4);box(ctx,1090,480,67,52,'#d19b64',4);
    box(ctx,1118,164,296,832,'#dcc4a0',12);
    for(let y=180;y<980;y+=35){ctx.strokeStyle='#c2a27b';ctx.beginPath();ctx.moveTo(1120,y);ctx.lineTo(1410,y);ctx.stroke();}
    text(ctx,'THE DINING ROOM',1266,207,18,'#6b5038');
    KitchenDining.draw(ctx,s,now,{person,text,colors});
    for(const [x,y] of [[1200,290],[1328,410]]){
      for(const d of [-45,45]){box(ctx,x+d-14,y-14,28,30,'#537c69',9);}
      circle(ctx,x+2,y+5,43,'#a87b53');circle(ctx,x,y,41,'#f7e9cd');circle(ctx,x-12,y,12,'#fffdf0');circle(ctx,x+17,y-4,7,'#bd7656');
      text(ctx,'☕',x+12,y+6,22);
    }
    KitchenDining.meals(ctx,s,{text});
    plant(ctx,1152,244);plant(ctx,1380,268);plant(ctx,1380,448);
    box(ctx,1138,496,250,43,'#385d4a',7);text(ctx,'ORDER PICKUP',1263,524,17,'#fff1d2');
    for(let i=0;i<s.orders.length;i++){
      const o=s.orders[i],x=1172+(i%3)*98,y=630+Math.floor(i/3)*120;
      person(ctx,x,y+Math.sin(now*2+i)*2,colors[(i+2)%8]);
      box(ctx,x-43,y-74,86,31,'#fff8e9',9);
      text(ctx,KitchenDining.icons[o.recipe],x-8,y-51,21);
      if(o.guest)text(ctx,o.guest==='Critic'?'🧐':'👑',x+30,y-51,11);
      box(ctx,x-35,y+43,70,5,'#bca483',2);box(ctx,x-35,y+43,70*Math.max(0,(o.expires-now)/o.patience),5,o.expires-now<15?'#c5654d':'#5e946b',2);
    }
    box(ctx,1133,929,266,62,'#315744',9);text(ctx,'DISH RETURN',1266,943,10,'#d6deba');
    box(ctx,1140,950,122,33,'#eff0cf',6);box(ctx,1270,950,122,33,'#e9c3a3',6);
    text(ctx,s.plates,1162,975,23,'#315744');text(ctx,'CLEAN',1216,972,12,'#315744');
    text(ctx,s.dirty,1292,975,23,'#824d37');text(ctx,'DIRTY',1346,972,12,'#824d37');
    text(ctx,'BON APPÉTIT · EVERY TICKET COUNTS',720,1023,15,'#5f6551');
  }
  function station(ctx,s,x,y,near,now){
    if(s.kind==='serve'){
      box(ctx,x-22,y-36,70,71,'#8c6745',6);box(ctx,x-12,y-26,53,38,'#254c3e',3);
      text(ctx,'🛎️',x+14,y+2,27);text(ctx,'Serve',x+14,y+25,13,'#fff1cf');
      if(near){ctx.strokeStyle='#eb9d40';ctx.lineWidth=4;ctx.strokeRect(x-25,y-39,76,77);}
      return;
    }
    box(ctx,x-37,y-27,74,69,'#8e7051',8);
    box(ctx,x-37,y-36,74,60,s.kind==='counter'?'#d7b286':s.kind==='serve'?'#dd986c':'#f2ead5',8);
    box(ctx,x-31,y+27,62,9,'#a58860',3);
    if(near){ctx.strokeStyle='#eb9d40';ctx.lineWidth=4;ctx.strokeRect(x-39,y-38,78,64);}
    if(s.kind==='stove'){
      box(ctx,x-28,y-28,56,40,'#43524a',5);
      for(const d of [-13,13]){circle(ctx,x+d,y-8,9,s.ready&&s.item!=='fire'?'#d88748':'#9da79b');circle(ctx,x+d,y-8,5,'#3a4741');}
      if(s.item){text(ctx,s.item==='fire'?'🔥':icons[s.item.replace('cooked ','').replace('chopped ','')],x,y+3,30);
        if(s.item.startsWith('cooked'))for(let i=0;i<3;i++)text(ctx,'∿',x-16+i*16,y-38-Math.sin(now*3+i)*5,18,'#fbfff6');}
    }else if(s.kind==='sink'){
      box(ctx,x-26,y-27,52,40,'#91b9b4',8);box(ctx,x-19,y-21,38,26,'#c9e4dc',8);text(ctx,'🚰',x,y-2,29);
    }else if(s.kind==='chop'){
      box(ctx,x-26,y-26,52,37,'#c9925c',5);text(ctx,'🔪',x,y+1,29);
    }else if(s.kind==='counter'){
      for(let i=0;i<3;i++){ctx.strokeStyle='#bd935f';ctx.beginPath();ctx.moveTo(x-26,y-23+i*13);ctx.lineTo(x+26,y-23+i*13);ctx.stroke();}
    }else text(ctx,icons[s.kind],x,y+1,31);
    text(ctx,s.name,x,y+23,13);
    if(s.ready&&s.item!=='fire'){box(ctx,x-28,y+40,56,5,'#9d9f7e',2);box(ctx,x-28,y+40,56*Math.min(1,Math.max(0,1-(s.ready-now)/7)),5,'#568851',2);}
  }
  return {colors,icons,box,text,circle,plant,person,room,station};
})();
