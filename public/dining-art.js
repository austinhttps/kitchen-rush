/* Served customers occupy the server's four shared table seats. */
window.KitchenDining={
  icons:{Salad:'🥗',Burger:'🍔','Fish & rice':'🍱',Lemonade:'🥤'},
  draw(ctx,state,now,art){
    const seats=[[1155,290],[1245,290],[1283,410],[1373,410]];
    for(const diner of state.diners){
      const [x,y]=seats[diner.seat];
      art.person(ctx,x,y,art.colors[diner.seat+2]);
      if(diner.guest)art.text(ctx,diner.guest==='Critic'?'🧐':'👑',x,y-30,19);
      art.text(ctx,'♥',x,y-45,14,'#bd684b');
    }
  },
  meals(ctx,state,art){
    const tables=[[1200,290],[1328,410]];
    for(const diner of state.diners){
      const [x,y]=tables[Math.floor(diner.seat/2)];
      art.text(ctx,this.icons[diner.recipe],x+(diner.seat%2?16:-16),y+8,20);
    }
  }
};
